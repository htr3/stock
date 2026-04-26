#!/usr/bin/env python3
"""
Walk-Forward Training Pipeline (Plan B Phase 3).

This is the *only* sanctioned production training entrypoint. It:

  1. Loads OHLCV from one or more CSVs (or a Dhan history dump).
  2. Generates features via the existing FeatureEngineer.
  3. Generates triple-barrier labels (cost-aware).
  4. Splits into walk-forward folds with purge + embargo.
  5. Per fold: IC-based feature selection -> XGBoost fit -> backtest with the
     NSE cost model and RiskManager.
  6. Aggregates metrics across folds.
  7. Calls ModelRegistry.evaluate_promotion -- on success, refits on the full
     window, saves the artefact, and writes a sibling model_card.json.

Usage:
    python scripts/train_walk_forward.py \
        --csv data/raw/AAPL_10min_generated_data.csv --smoke

CLI is deliberately small; parameters that affect comparability across runs
(barrier mults, cost bps, risk per trade) are surfaced as flags so they end
up in the model card.
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from cost_model import NSEIntradayCostModel  # noqa: E402
from feature_engineering import FeatureEngineer  # noqa: E402
from feature_selection import ICFeatureSelector  # noqa: E402
from risk_manager import RiskManager, RiskParams  # noqa: E402
from target_variable import TripleBarrier  # noqa: E402
from utils.model_registry import ModelRegistry  # noqa: E402

warnings.filterwarnings("ignore")


# ---------------------------------------------------------------------------
# Walk-forward fold generator
# ---------------------------------------------------------------------------


@dataclass
class FoldSpec:
    train_start: int
    train_end: int
    test_start: int
    test_end: int


def make_folds(
    n: int,
    n_splits: int = 5,
    train_frac: float = 0.6,
    test_frac: float = 0.1,
    embargo: int = 5,
) -> List[FoldSpec]:
    """
    Walk-forward folds with embargo. Train and test windows slide forward;
    ``embargo`` bars are discarded between train and test to break leakage
    through overlapping label horizons.
    """
    train_size = int(n * train_frac)
    test_size = int(n * test_frac)
    if train_size <= 0 or test_size <= 0:
        raise ValueError("Insufficient rows for walk-forward training")

    step = max(1, (n - train_size - test_size - embargo) // max(1, n_splits - 1))
    folds: List[FoldSpec] = []
    for k in range(n_splits):
        train_start = k * step
        train_end = train_start + train_size
        test_start = train_end + embargo
        test_end = test_start + test_size
        if test_end > n:
            break
        folds.append(FoldSpec(train_start, train_end, test_start, test_end))
    return folds


# ---------------------------------------------------------------------------
# Per-fold backtest
# ---------------------------------------------------------------------------


def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["High"], df["Low"], df["Close"]
    prev = close.shift(1)
    tr = pd.concat(
        [(high - low).abs(), (high - prev).abs(), (low - prev).abs()], axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def fold_backtest(
    df_test: pd.DataFrame,
    proba: np.ndarray,
    cost: NSEIntradayCostModel,
    risk: RiskManager,
    threshold: float = 0.55,
    max_horizon: int = 5,
    starting_equity: float = 100_000.0,
    exchange: str = "NSE",
) -> dict:
    """
    Walk every test bar; if proba[i] > threshold open a long, simulate
    stop/target/time-stop within the next ``max_horizon`` bars, and record
    net P&L (after slippage and charges).
    """
    if len(df_test) != len(proba):
        raise ValueError("predictions length must match df_test length")

    atr = _atr(df_test).to_numpy()
    opens = df_test["Open"].to_numpy()
    highs = df_test["High"].to_numpy()
    lows = df_test["Low"].to_numpy()
    closes = df_test["Close"].to_numpy()
    n = len(df_test)

    trades: list[dict] = []
    last_exit_idx = -1

    for i in range(n - 1):
        if proba[i] < threshold:
            continue
        if i <= last_exit_idx:
            continue  # don't pyramid -- one position at a time

        atr_i = atr[i]
        if not np.isfinite(atr_i) or atr_i <= 0:
            continue

        entry = opens[i + 1]
        if not np.isfinite(entry) or entry <= 0:
            continue

        qty = risk.size(entry, atr_i, "BUY")
        if qty <= 0:
            continue

        stop = risk.stop_price(entry, atr_i, "BUY")
        target = risk.target_price(entry, atr_i, "BUY")

        horizon_end = min(i + 1 + max_horizon, n)
        exit_price = closes[horizon_end - 1]
        exit_idx = horizon_end - 1
        exit_reason = "time_stop"

        for j in range(i + 1, horizon_end):
            hi, lo = highs[j], lows[j]
            if lo <= stop:
                exit_price, exit_idx, exit_reason = stop, j, "stop_loss"
                break
            if hi >= target:
                exit_price, exit_idx, exit_reason = target, j, "take_profit"
                break

        net_inr = cost.net_pnl_inr(entry, exit_price, qty, long_side=True, exchange=exchange)
        net_bps = cost.net_pnl_bps(entry, exit_price, long_side=True, exchange=exchange)

        trades.append(
            {
                "entry_idx": i + 1,
                "exit_idx": exit_idx,
                "entry_time": df_test.index[i + 1] if isinstance(df_test.index, pd.DatetimeIndex) else None,
                "exit_time": df_test.index[exit_idx] if isinstance(df_test.index, pd.DatetimeIndex) else None,
                "entry": float(entry),
                "exit": float(exit_price),
                "qty": int(qty),
                "net_inr": float(net_inr),
                "net_bps": float(net_bps),
                "exit_reason": exit_reason,
            }
        )
        last_exit_idx = exit_idx

    return _summarise_trades(trades, starting_equity=starting_equity)


def _summarise_trades(trades: list[dict], starting_equity: float = 100_000.0) -> dict:
    if not trades:
        return {
            "trades": 0,
            "win_rate": 0.0,
            "net_pnl_inr": 0.0,
            "net_pnl_bps": 0.0,
            "sharpe": 0.0,
            "max_drawdown": 0.0,
            "avg_bps": 0.0,
            "trades_detail": [],
        }

    df = pd.DataFrame(trades)
    n = len(df)
    win_rate = float((df["net_inr"] > 0).mean())
    total_inr = float(df["net_inr"].sum())
    avg_bps = float(df["net_bps"].mean())

    # Daily Sharpe -- aggregate per-trade pnl by exit day if we have timestamps,
    # otherwise fall back to per-trade Sharpe.
    if "exit_time" in df and df["exit_time"].notna().all():
        by_day = df.set_index("exit_time")["net_inr"].resample("1D").sum().dropna()
        if len(by_day) > 1 and by_day.std() > 0:
            sharpe = float(by_day.mean() / by_day.std() * np.sqrt(252))
        else:
            sharpe = 0.0
    else:
        if df["net_inr"].std() > 0:
            sharpe = float(df["net_inr"].mean() / df["net_inr"].std() * np.sqrt(n))
        else:
            sharpe = 0.0

    equity_curve = starting_equity + df["net_inr"].cumsum()
    peak = equity_curve.cummax()
    dd = ((peak - equity_curve) / peak.clip(lower=1e-9)).clip(lower=0.0)
    max_dd = float(dd.max()) if len(dd) else 0.0

    return {
        "trades": int(n),
        "win_rate": win_rate,
        "net_pnl_inr": total_inr,
        "net_pnl_bps": avg_bps,  # avg bps per trade (used as net edge)
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "avg_bps": avg_bps,
        "trades_detail": trades,
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def load_ohlcv(csv_paths: Iterable[Path]) -> pd.DataFrame:
    frames = []
    for p in csv_paths:
        df = pd.read_csv(p)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp")
        df.columns = [c.capitalize() if c.lower() in ("open", "high", "low", "close", "volume") else c for c in df.columns]
        frames.append(df)
    out = pd.concat(frames).sort_index()
    out = out[~out.index.duplicated(keep="first")]
    return out


def aggregate(metrics: List[dict]) -> dict:
    """Trade-weighted aggregation across folds."""
    total_trades = sum(m["trades"] for m in metrics)
    if total_trades == 0:
        return {
            "trades": 0,
            "win_rate": 0.0,
            "net_pnl_inr": 0.0,
            "net_pnl_bps": 0.0,
            "sharpe": 0.0,
            "max_drawdown": 0.0,
            "folds": metrics,
        }

    weighted_winrate = sum(m["win_rate"] * m["trades"] for m in metrics) / total_trades
    weighted_bps = sum(m["net_pnl_bps"] * m["trades"] for m in metrics) / total_trades
    total_inr = sum(m["net_pnl_inr"] for m in metrics)
    sharpe = float(np.mean([m["sharpe"] for m in metrics]))
    max_dd = float(max(m["max_drawdown"] for m in metrics))

    return {
        "trades": total_trades,
        "win_rate": weighted_winrate,
        "net_pnl_inr": total_inr,
        "net_pnl_bps": weighted_bps,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "folds": [{k: v for k, v in m.items() if k != "trades_detail"} for m in metrics],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", nargs="+", default=[str(ROOT / "data" / "raw" / "AAPL_10min_generated_data.csv")])
    parser.add_argument("--smoke", action="store_true", help="Run a fast smoke configuration")
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--top-k", type=int, default=60)
    parser.add_argument("--up-mult", type=float, default=1.0)
    parser.add_argument("--dn-mult", type=float, default=1.0)
    parser.add_argument("--max-horizon", type=int, default=5)
    parser.add_argument("--threshold", type=float, default=0.55)
    parser.add_argument("--equity", type=float, default=100_000.0)
    parser.add_argument("--slippage-bps", type=float, default=3.0)
    parser.add_argument("--exchange", choices=["NSE", "BSE"], default="NSE",
                        help="Exchange used for cost-model charges in backtest.")
    parser.add_argument("--out", type=str, default=str(ROOT / "models" / "saved"))
    args = parser.parse_args()

    if args.smoke:
        args.n_splits = 3
        args.top_k = 30

    try:
        from xgboost import XGBClassifier
    except ImportError:
        print("xgboost is required (pip install xgboost)")
        return 2

    csv_paths = [Path(p) for p in args.csv]
    print(f"Loading {len(csv_paths)} csv(s)...")
    df = load_ohlcv(csv_paths)
    print(f"  {len(df):,} rows, {df.index.min()} -> {df.index.max()}")

    # Bundled synthetic CSVs may contain negative prices; positive prices
    # are required for the cost model and triple-barrier logic.
    pos_mask = (df[["Open", "High", "Low", "Close"]] > 0).all(axis=1)
    dropped = (~pos_mask).sum()
    if dropped:
        print(f"  Dropping {dropped} rows with non-positive OHLC")
        df = df.loc[pos_mask]

    print("Generating features...")
    feats = FeatureEngineer(df).generate_all_features()
    feats = feats.replace([np.inf, -np.inf], np.nan)

    cost = NSEIntradayCostModel(
        slippage_bps=args.slippage_bps, default_exchange=args.exchange
    )
    sample_price = float(df["Close"].dropna().median())
    if sample_price <= 0:
        sample_price = 100.0
    cost_bps = cost.round_trip_bps(sample_price, exchange=args.exchange)
    print(f"Round-trip cost @ ~price={sample_price:.2f} on {args.exchange}: {cost_bps:.2f} bps")

    print("Generating triple-barrier labels...")
    labels = TripleBarrier.label(
        df,
        up_mult=args.up_mult,
        dn_mult=args.dn_mult,
        max_horizon=args.max_horizon,
        min_move_bps=cost_bps,
    )

    # Keep tradable rows only and align features.
    tradable = labels["tradable"]
    common_idx = feats.dropna(thresh=int(0.5 * feats.shape[1])).index
    common_idx = common_idx.intersection(labels.index[tradable])
    X_full = feats.loc[common_idx].fillna(0.0)
    y_full = (labels.loc[common_idx, "label"] > 0).astype(int)
    df_full = df.loc[common_idx]

    print(f"Tradable samples: {len(common_idx):,} ({len(common_idx) / len(df):.1%})")
    if len(common_idx) < 200:
        print("  Not enough tradable samples after filtering; aborting.")
        return 3

    risk = RiskManager(
        RiskParams(
            account_equity=args.equity,
            risk_per_trade=0.01,
            atr_stop_mult=1.5,
            atr_target_mult=2.5,
            max_trades_per_day=5,
            max_horizon_bars=args.max_horizon,
            bar_minutes=10,
        )
    )

    folds = make_folds(len(X_full), n_splits=args.n_splits)
    print(f"Walk-forward folds: {len(folds)}")
    fold_metrics = []
    for k, fs in enumerate(folds, 1):
        X_tr, X_te = X_full.iloc[fs.train_start:fs.train_end], X_full.iloc[fs.test_start:fs.test_end]
        y_tr, y_te = y_full.iloc[fs.train_start:fs.train_end], y_full.iloc[fs.test_start:fs.test_end]
        df_te = df_full.iloc[fs.test_start:fs.test_end]

        if y_tr.nunique() < 2 or y_te.empty:
            print(f"  Fold {k}: skipped (degenerate)")
            continue

        sel = ICFeatureSelector(top_k=args.top_k).fit(X_tr, y_tr)
        X_tr_s, X_te_s = sel.transform(X_tr), sel.transform(X_te)

        model = XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            verbosity=0,
            n_jobs=1,
        )
        model.fit(X_tr_s, y_tr)
        proba = model.predict_proba(X_te_s)[:, 1]

        m = fold_backtest(
            df_te.assign(),
            proba,
            cost=cost,
            risk=risk,
            threshold=args.threshold,
            max_horizon=args.max_horizon,
            starting_equity=args.equity,
            exchange=args.exchange,
        )
        print(
            f"  Fold {k}: trades={m['trades']:3d}  win={m['win_rate']*100:5.1f}%  "
            f"avg_bps={m['avg_bps']:+6.1f}  sharpe={m['sharpe']:+5.2f}  maxDD={m['max_drawdown']*100:5.2f}%"
        )
        fold_metrics.append(m)

    if not fold_metrics:
        print("No usable folds. Aborting.")
        return 4

    agg = aggregate(fold_metrics)
    print("\nAggregated walk-forward metrics:")
    for k in ("trades", "win_rate", "net_pnl_bps", "sharpe", "max_drawdown"):
        print(f"  {k:14s}: {agg[k]}")

    # Promotion gate
    registry = ModelRegistry()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    challenger_path = out_dir / f"xgb_walkforward_{stamp}.joblib"

    # Refit on full data for the saved artefact (typical practice once gate passes).
    sel_full = ICFeatureSelector(top_k=args.top_k).fit(X_full, y_full)
    final = XGBClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42, verbosity=0, n_jobs=1
    )
    final.fit(sel_full.transform(X_full), y_full)

    import joblib
    joblib.dump(
        {"model": final, "selector": sel_full, "feature_columns": sel_full.selected_},
        challenger_path,
    )

    passed, gate_details = registry.evaluate_promotion(str(challenger_path), agg)
    extra = {
        "args": vars(args),
        "cost_round_trip_bps": cost_bps,
        "n_features_selected": len(sel_full.selected_ or []),
        "rows_used": int(len(common_idx)),
    }

    if passed:
        card = registry.promote_challenger(str(challenger_path), agg, extra=extra)
        print(f"\nPROMOTED. model_card.json -> {card}")
    else:
        registry.archive_challenger(str(challenger_path), agg, reason="gate_failed")
        print("\nGATE FAILED. Challenger archived. Failures:")
        print(json.dumps(gate_details["failed"], indent=2))

    print(f"Artefact: {challenger_path}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
