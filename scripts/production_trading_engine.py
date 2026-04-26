#!/usr/bin/env python3
"""
Production Trading Engine -- India / Dhan / NSE.

Pipeline per cycle:
  1. Force-exit any open positions whose stop / target / time-stop / 15:20
     square-off triggered.
  2. Fetch the latest 10-min bars from Dhan.
  3. Engineer features.
  4. Predict via the loaded champion model.
  5. Run validator gates.
  6. If signal + gates + RiskManager.can_trade_now: size with RiskManager and
     submit a Dhan cover order with attached stop-loss.

This file deliberately drops the Alpaca import; the legacy fetcher is left in
the repo for back-compat with US notebooks but is no longer in the production
import graph.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import joblib
import pandas as pd

if sys.platform == "win32":  # pragma: no cover
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).parent))

from dhan_data_fetcher import DhanLiveDataFetcher, DhanSymbol  # noqa: E402
from feature_engineering import FeatureEngineer  # noqa: E402
from production_validator import ProductionValidator  # noqa: E402
from risk_manager import IST, Position, RiskManager, RiskParams  # noqa: E402

ROOT = Path(__file__).parent.parent


class ProductionTradingEngine:
    def __init__(
        self,
        dry_run: bool = True,
        paper: bool = True,
        equity_override: Optional[float] = None,
    ):
        self.dry_run = dry_run
        self.paper = paper
        self.cycles = 0
        self.log_dir = ROOT / "logs" / "production"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.trades_log = self.log_dir / f"trades_{datetime.now().strftime('%Y%m%d')}.jsonl"

        self.fetcher = DhanLiveDataFetcher(paper=paper)
        self.symbols: List[DhanSymbol] = self.fetcher.get_symbols()

        self.bundle = self._load_champion()
        self.model = self.bundle.get("model") if self.bundle else None
        self.selector = self.bundle.get("selector") if self.bundle else None
        self.feature_columns = self.bundle.get("feature_columns") if self.bundle else None

        equity = equity_override or float(self.fetcher.account_status().get("equity", 100_000.0))
        self.risk = RiskManager(
            RiskParams(
                account_equity=equity,
                risk_per_trade=0.01,
                atr_stop_mult=1.5,
                atr_target_mult=2.5,
                max_trades_per_day=5,
                max_horizon_bars=5,
                bar_minutes=10,
            )
        )

        self.open_positions: Dict[str, Position] = {}
        self.today_trade_count = 0
        self.today_date: Optional[str] = None

        print("=" * 80)
        print("Production Trading Engine v2.0  --  Dhan / NSE")
        print(f"  dry_run={self.dry_run}  paper={self.paper}  equity={equity:,.0f}")
        print(f"  symbols ({len(self.symbols)}): {', '.join(s.ticker for s in self.symbols)}")
        print(f"  model loaded: {self.model is not None}")
        print("=" * 80)

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_champion(self) -> Optional[dict]:
        # Prefer ModelRegistry champion path so we always run what was promoted.
        try:
            from utils.model_registry import ModelRegistry
            reg = ModelRegistry()
            path = reg.registry.get("champion")
            if path and Path(path).exists():
                bundle = joblib.load(path)
                print(f"Loaded champion: {path}")
                return bundle if isinstance(bundle, dict) else {"model": bundle}
        except Exception as exc:
            print(f"Registry load failed: {exc}")

        # Fallback: latest XGBoost in models/saved
        model_dir = ROOT / "models" / "saved"
        if model_dir.exists():
            candidates = sorted(model_dir.glob("xgb_walkforward_*.joblib"))
            if candidates:
                path = candidates[-1]
                print(f"Loaded fallback model: {path}")
                bundle = joblib.load(path)
                return bundle if isinstance(bundle, dict) else {"model": bundle}

        print("No champion model available -- engine will run in observe-only mode.")
        return None

    # ------------------------------------------------------------------
    # Day boundary book-keeping
    # ------------------------------------------------------------------

    def _roll_day(self, now: datetime) -> None:
        today = now.astimezone(IST).strftime("%Y-%m-%d")
        if today != self.today_date:
            self.today_date = today
            self.today_trade_count = 0

    # ------------------------------------------------------------------
    # Feature + signal
    # ------------------------------------------------------------------

    def _features(self, df_live: pd.DataFrame) -> pd.DataFrame:
        if df_live.empty:
            return pd.DataFrame()
        df_norm = df_live.copy()
        df_norm.columns = [c.capitalize() if c.lower() in ("open", "high", "low", "close", "volume") else c for c in df_norm.columns]
        feats = FeatureEngineer(df_norm).generate_all_features()
        feats = feats.dropna()
        return feats

    def _signal(self, features: pd.DataFrame) -> Dict:
        if self.model is None or features.empty:
            return {"signal": 0, "confidence": 0.0, "error": "no model/features"}

        X = features.tail(1).fillna(0.0)
        if self.selector is not None:
            try:
                X = self.selector.transform(X)
            except Exception as exc:
                return {"signal": 0, "confidence": 0.0, "error": f"selector: {exc}"}
        elif self.feature_columns is not None:
            X = X[[c for c in self.feature_columns if c in X.columns]]

        try:
            proba = float(self.model.predict_proba(X)[:, 1][0])
        except Exception as exc:
            return {"signal": 0, "confidence": 0.0, "error": f"predict: {exc}"}

        signal = 1 if proba >= 0.55 else 0
        return {"signal": signal, "confidence": proba, "prob": proba}

    # ------------------------------------------------------------------
    # Cycle
    # ------------------------------------------------------------------

    def run_production_cycle(self) -> None:
        self.cycles += 1
        now = datetime.now(IST)
        self._roll_day(now)

        cycle_log = {
            "cycle": self.cycles,
            "timestamp": now.isoformat(),
            "symbols": {},
            "exits": [],
        }

        # --- Step 1: force-exit pass ---
        live_data = self.fetcher.fetch_live_bars(symbols=self.symbols, bars_back=200)

        for ticker, position in list(self.open_positions.items()):
            df = live_data.get(ticker, pd.DataFrame())
            last_price = float(df["close"].iloc[-1]) if not df.empty and "close" in df else None
            should_exit, reason = self.risk.should_force_exit(now, position, last_price)
            if should_exit:
                self._close_position(ticker, position, last_price, reason, cycle_log)

        # --- Step 2-6: signal pass ---
        for sym in self.symbols:
            ticker = sym.ticker
            df_live = live_data.get(ticker, pd.DataFrame())
            if df_live.empty:
                cycle_log["symbols"][ticker] = {"status": "no_data"}
                continue
            if ticker in self.open_positions:
                cycle_log["symbols"][ticker] = {"status": "in_position"}
                continue

            feats = self._features(df_live)
            if feats.empty:
                cycle_log["symbols"][ticker] = {"status": "no_features"}
                continue

            ml = self._signal(feats)

            df_norm = df_live.copy()
            df_norm.columns = [c.capitalize() if c.lower() in ("open", "high", "low", "close", "volume") else c for c in df_norm.columns]
            df_norm["signal"] = ml.get("signal", 0)
            df_norm["confidence"] = ml.get("confidence", 0.0)
            df_norm["prediction"] = ml.get("signal", 0)
            try:
                gates = ProductionValidator(df_norm, model=self.model).run_all_gates()
                gate_pass = any(k in gates.get("decision", "") for k in ("SAFE", "READY", "MARGINAL"))
            except Exception as exc:
                gates = {"decision": f"validator_error: {exc}", "passed": 0}
                gate_pass = False

            entry_log = {
                "signal": ml.get("signal", 0),
                "confidence": ml.get("confidence", 0.0),
                "gates": gates.get("decision"),
                "passed": gates.get("passed", 0),
            }

            if not gate_pass or ml.get("signal", 0) != 1:
                entry_log["status"] = "no_trade"
                cycle_log["symbols"][ticker] = entry_log
                continue

            if not self.risk.can_trade_now(now, self.today_trade_count):
                entry_log["status"] = "risk_blocked"
                cycle_log["symbols"][ticker] = entry_log
                continue

            atr_value = float(feats.tail(1).get("atr", pd.Series([0.0])).iloc[0])
            price = float(df_norm["Close"].iloc[-1])
            qty = self.risk.size(price, atr_value, "BUY")
            if qty <= 0:
                entry_log["status"] = "size_zero"
                entry_log["atr"] = atr_value
                cycle_log["symbols"][ticker] = entry_log
                continue

            stop = self.risk.stop_price(price, atr_value, "BUY")
            target = self.risk.target_price(price, atr_value, "BUY")

            entry_log.update(
                {"status": "trade", "qty": qty, "price": price, "stop": stop, "target": target, "atr": atr_value}
            )

            if not self.dry_run:
                resp = self.fetcher.place_cover_order(
                    sym, qty=qty, side="BUY", stop_price=stop, target_price=target, price=price
                )
                entry_log["broker_response"] = resp

            self.open_positions[ticker] = Position(
                symbol=ticker,
                side="BUY",
                qty=qty,
                entry_price=price,
                entry_time=now,
                stop_price=stop,
                target_price=target,
                max_horizon_bars=self.risk.p.max_horizon_bars,
            )
            self.today_trade_count += 1
            cycle_log["symbols"][ticker] = entry_log
            self._append_trade_log({"event": "open", "ticker": ticker, "time": now.isoformat(), **entry_log})

        self._append_trade_log({"event": "cycle", **cycle_log})
        print(
            f"Cycle {self.cycles} @ {now.strftime('%H:%M:%S IST')} | "
            f"open={len(self.open_positions)} trades_today={self.today_trade_count}"
        )

    def _close_position(
        self,
        ticker: str,
        position: Position,
        last_price: Optional[float],
        reason: str,
        cycle_log: dict,
    ) -> None:
        exit_log = {
            "ticker": ticker,
            "qty": position.qty,
            "entry_price": position.entry_price,
            "exit_price": last_price,
            "reason": reason,
            "time": datetime.now(IST).isoformat(),
        }
        if not self.dry_run and last_price is not None:
            sym = next((s for s in self.symbols if s.ticker == ticker), None)
            if sym is not None:
                # Close the cover order by submitting an opposite leg.
                resp = self.fetcher.place_cover_order(
                    sym,
                    qty=position.qty,
                    side="SELL" if position.side == "BUY" else "BUY",
                    stop_price=last_price,  # stop unused on exit
                    price=last_price,
                )
                exit_log["broker_response"] = resp

        cycle_log["exits"].append(exit_log)
        self._append_trade_log({"event": "close", **exit_log})
        self.open_positions.pop(ticker, None)

    def _append_trade_log(self, payload: dict) -> None:
        try:
            with open(self.trades_log, "a") as f:
                f.write(json.dumps(payload, default=str) + "\n")
        except Exception as exc:
            print(f"trade-log write failed: {exc}")

    def run_continuous(self, interval_sec: int = 600, duration_hours: Optional[float] = None) -> None:
        start = datetime.now()
        try:
            while True:
                if duration_hours is not None:
                    elapsed = (datetime.now() - start).total_seconds() / 3600
                    if elapsed > duration_hours:
                        return
                self.run_production_cycle()
                time.sleep(interval_sec)
        except KeyboardInterrupt:
            print("Stopped by user.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="No live orders; log decisions only")
    parser.add_argument("--paper", action="store_true", help="Use Dhan paper-mode simulator")
    parser.add_argument("--equity", type=float, default=None, help="Override account equity (INR)")
    parser.add_argument("--interval", type=int, default=600)
    parser.add_argument("--duration", type=float, default=None)
    parser.add_argument("--single-cycle", action="store_true")
    args = parser.parse_args()

    paper = args.paper or args.dry_run or not (
        os.getenv("DHAN_CLIENT_ID") and os.getenv("DHAN_ACCESS_TOKEN")
    )
    engine = ProductionTradingEngine(dry_run=args.dry_run, paper=paper, equity_override=args.equity)

    if args.single_cycle:
        engine.run_production_cycle()
    else:
        engine.run_continuous(interval_sec=args.interval, duration_hours=args.duration)
    return 0


if __name__ == "__main__":
    sys.exit(main())
