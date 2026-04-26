#!/usr/bin/env python3
"""
Dhan data fetcher: India NSE/BSE replacement for the Alpaca-based fetcher.

Surface area is intentionally identical to ``LiveDataFetcher`` so the
production engine can swap brokers without touching downstream code:

  fetch_live_bars(symbols, bars_back, timeframe="10min") -> Dict[str, DataFrame]
  account_status() -> Dict
  place_cover_order(symbol, qty, side, stop_price, target_price=None) -> Dict
  get_symbols(config_path) -> List[Dict]   # tickers + Dhan security_ids

The ``dhanhq`` SDK is imported lazily so the module is still importable in
environments where the dependency is not installed (CI, smoke tests).
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parent

# Dhan exchange codes
EXCHANGE_NSE_EQ = "NSE_EQ"
EXCHANGE_BSE_EQ = "BSE_EQ"


@dataclass
class DhanSymbol:
    ticker: str
    security_id: str
    exchange: str = EXCHANGE_NSE_EQ


class DhanLiveDataFetcher:
    def __init__(
        self,
        client_id: Optional[str] = None,
        access_token: Optional[str] = None,
        paper: bool = True,
    ):
        self.client_id = client_id or os.getenv("DHAN_CLIENT_ID")
        self.access_token = access_token or os.getenv("DHAN_ACCESS_TOKEN")
        self.paper = paper
        self._client = None  # lazy

        if not paper and (not self.client_id or not self.access_token):
            raise ValueError(
                "Dhan credentials missing. Set DHAN_CLIENT_ID and "
                "DHAN_ACCESS_TOKEN env vars, or pass paper=True."
            )

    # ------------------------------------------------------------------
    # SDK access (lazy)
    # ------------------------------------------------------------------

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from dhanhq import dhanhq  # type: ignore
        except ImportError as exc:  # pragma: no cover - exercised only without sdk
            raise ImportError(
                "dhanhq is not installed. `pip install dhanhq` to use the live "
                "Dhan data fetcher, or run with paper=True for the simulator."
            ) from exc

        if not self.client_id or not self.access_token:
            raise RuntimeError("Dhan credentials are required for live mode.")

        self._client = dhanhq(self.client_id, self.access_token)
        return self._client

    # ------------------------------------------------------------------
    # Symbol config
    # ------------------------------------------------------------------

    def get_symbols(self, config_path: Optional[Path] = None) -> List[DhanSymbol]:
        if config_path is None:
            # Prefer scripts/config/ (the canonical location); fall back to
            # repo-root/config/ for back-compat with older deploys.
            candidates = [
                SCRIPTS_DIR / "config" / "trading_symbols.json",
                ROOT / "config" / "trading_symbols.json",
            ]
            config_path = next((c for c in candidates if c.exists()), candidates[0])
        config_path = Path(config_path)
        if not config_path.exists():
            logger.warning("Trading symbols config missing at %s", config_path)
            return []

        with open(config_path) as f:
            cfg = json.load(f)

        out: List[DhanSymbol] = []
        for category, block in cfg.items():
            if category.startswith("_"):
                continue
            if not isinstance(block, dict) or not block.get("enabled"):
                continue
            for entry in block.get("symbols", []):
                if isinstance(entry, dict):
                    out.append(
                        DhanSymbol(
                            ticker=entry["ticker"],
                            security_id=str(entry["security_id"]),
                            exchange=entry.get("exchange", EXCHANGE_NSE_EQ),
                        )
                    )
                elif isinstance(entry, str):
                    # Plain ticker (legacy) -- skip; we cannot place orders without security_id
                    logger.warning("Skipping symbol %s with no security_id", entry)
        return out

    # ------------------------------------------------------------------
    # Market data
    # ------------------------------------------------------------------

    def fetch_live_bars(
        self,
        symbols: Optional[List[DhanSymbol]] = None,
        bars_back: int = 200,
        timeframe: str = "10min",
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch the most recent ``bars_back`` candles for each symbol.

        Returns a dict keyed by ticker. Each DataFrame uses lowercase OHLCV
        column names and a tz-aware DatetimeIndex named 'timestamp', matching
        the schema produced by ``LiveDataFetcher``.
        """
        if symbols is None:
            symbols = self.get_symbols()
        if not symbols:
            return {}

        if self.paper:
            return self._paper_bars(symbols, bars_back)

        return self._live_bars(symbols, bars_back, timeframe)

    def _live_bars(
        self,
        symbols: List[DhanSymbol],
        bars_back: int,
        timeframe: str,
    ) -> Dict[str, pd.DataFrame]:
        client = self._get_client()
        interval = _parse_interval_minutes(timeframe)
        end = datetime.now()
        start = end - timedelta(minutes=interval * bars_back * 2)  # buffer for non-trading bars

        out: Dict[str, pd.DataFrame] = {}
        for sym in symbols:
            try:
                resp = client.intraday_minute_data(
                    security_id=sym.security_id,
                    exchange_segment=sym.exchange,
                    instrument_type="EQUITY",
                    from_date=start.strftime("%Y-%m-%d"),
                    to_date=end.strftime("%Y-%m-%d"),
                )
                df = _dhan_response_to_df(resp, interval)
                if df is None or df.empty:
                    out[sym.ticker] = pd.DataFrame()
                    continue
                out[sym.ticker] = df.tail(bars_back)
            except Exception as exc:  # pragma: no cover - depends on live API
                logger.error("Dhan fetch failed for %s: %s", sym.ticker, exc)
                out[sym.ticker] = pd.DataFrame()
        return out

    def _paper_bars(
        self,
        symbols: List[DhanSymbol],
        bars_back: int,
    ) -> Dict[str, pd.DataFrame]:
        """
        Paper-mode replays the most recent ``bars_back`` rows from a bundled
        CSV under ``data/raw/`` so the engine can be exercised without market
        data. The CSV chosen for each ticker is the first one matching the
        ticker name; if none matches, the first CSV is used as a stand-in.
        """
        raw = ROOT / "data" / "raw"
        csvs = sorted(raw.glob("*.csv")) if raw.exists() else []
        out: Dict[str, pd.DataFrame] = {}
        for sym in symbols:
            csv = next((c for c in csvs if sym.ticker.upper() in c.stem.upper()), None)
            if csv is None and csvs:
                csv = csvs[0]
            if csv is None:
                out[sym.ticker] = pd.DataFrame()
                continue
            df = pd.read_csv(csv)
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.set_index("timestamp")
            df.columns = [c.lower() for c in df.columns]
            out[sym.ticker] = df.tail(bars_back).copy()
        return out

    # ------------------------------------------------------------------
    # Account + orders
    # ------------------------------------------------------------------

    def account_status(self) -> Dict[str, Any]:
        if self.paper:
            return {"equity": 100_000.0, "cash": 100_000.0, "status": "paper"}
        try:
            client = self._get_client()
            funds = client.get_fund_limits()
            data = funds.get("data", {}) if isinstance(funds, dict) else {}
            return {
                "equity": float(data.get("availabelBalance", 0.0)),
                "cash": float(data.get("availabelBalance", 0.0)),
                "status": "live",
                "raw": data,
            }
        except Exception as exc:  # pragma: no cover
            logger.warning("Dhan account_status failed: %s", exc)
            return {"error": str(exc)}

    def place_cover_order(
        self,
        symbol: DhanSymbol,
        qty: int,
        side: str,
        stop_price: float,
        target_price: Optional[float] = None,
        price: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Place a Dhan cover order (CO) -- one entry leg + an attached SL leg.
        In paper mode we simulate a successful fill at the requested price.
        """
        if qty <= 0:
            raise ValueError("qty must be > 0")
        if side not in ("BUY", "SELL"):
            raise ValueError("side must be 'BUY' or 'SELL'")

        if self.paper:
            return {
                "status": "paper_filled",
                "order_id": f"PAPER-{datetime.utcnow().timestamp():.0f}",
                "symbol": symbol.ticker,
                "qty": qty,
                "side": side,
                "fill_price": price,
                "stop_price": stop_price,
                "target_price": target_price,
            }

        client = self._get_client()
        try:
            resp = client.place_order(
                security_id=symbol.security_id,
                exchange_segment=symbol.exchange,
                transaction_type=side,
                quantity=qty,
                order_type="MARKET",
                product_type="CO",
                price=0,
                trigger_price=stop_price,
                validity="DAY",
            )
            return {"status": "submitted", "raw": resp}
        except Exception as exc:  # pragma: no cover
            return {"status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_interval_minutes(tf: str) -> int:
    """'10min' -> 10, '1min' -> 1."""
    tf = tf.strip().lower()
    if tf.endswith("min"):
        return int(tf[:-3])
    if tf.endswith("m"):
        return int(tf[:-1])
    raise ValueError(f"Unsupported timeframe: {tf}")


def _dhan_response_to_df(resp: Any, interval: int) -> Optional[pd.DataFrame]:
    """Convert the Dhan ``intraday_minute_data`` response into our schema."""
    if not isinstance(resp, dict):
        return None
    data = resp.get("data") or {}
    keys = ("open", "high", "low", "close", "volume", "timestamp")
    if not all(k in data for k in keys):
        return None
    df = pd.DataFrame({k: data[k] for k in keys})
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df = df.set_index("timestamp")
    if interval > 1:
        df = (
            df.resample(f"{interval}min")
            .agg(
                {
                    "open": "first",
                    "high": "max",
                    "low": "min",
                    "close": "last",
                    "volume": "sum",
                }
            )
            .dropna()
        )
    return df
