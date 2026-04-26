"""
RiskManager: trade-level risk controls used by both the backtester and the
production engine, so backtest behaviour matches live behaviour.

Responsibilities (per Plan B Phase 5):
  * Volatility-targeted position sizing (risk a fixed % of equity per trade,
    capped by max gross exposure and a per-trade rupee cap).
  * ATR-based stop and target prices.
  * Daily trade-count cap and IST 15:20 force-exit ("square-off").
  * Time-stop after `max_horizon_bars` bars in the position.

The portfolio-level circuit breakers (drawdown halts, VIX gates) live in the
existing `RiskGuardAgent` -- this class is intentionally narrow.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Literal, Optional
from zoneinfo import ZoneInfo

Side = Literal["BUY", "SELL"]
IST = ZoneInfo("Asia/Kolkata")


@dataclass
class Position:
    symbol: str
    side: Side
    qty: int
    entry_price: float
    entry_time: datetime
    stop_price: float
    target_price: float
    max_horizon_bars: int = 5


@dataclass
class RiskParams:
    account_equity: float
    risk_per_trade: float = 0.01        # fraction of equity at risk per trade
    atr_stop_mult: float = 1.5
    atr_target_mult: float = 2.5
    max_trades_per_day: int = 5
    max_gross_exposure: float = 1.0     # fraction of equity invested
    per_trade_cap: float = 0.10         # any single trade <= 10% of equity
    square_off_ist: time = field(default_factory=lambda: time(15, 20))
    market_open_ist: time = field(default_factory=lambda: time(9, 15))
    max_horizon_bars: int = 5
    bar_minutes: int = 10


class RiskManager:
    """Trade-level risk policy. All times are timezone-aware; we coerce to IST."""

    def __init__(self, params: RiskParams):
        if params.account_equity <= 0:
            raise ValueError("account_equity must be > 0")
        if not 0 < params.risk_per_trade < 1:
            raise ValueError("risk_per_trade must be in (0, 1)")
        self.p = params

    # ---- sizing ----------------------------------------------------------

    def size(self, price: float, atr: float, side: Side) -> int:
        """
        Vol-targeted size: qty * (atr_stop_mult * atr) = risk_per_trade * equity.
        Capped by per_trade_cap and max_gross_exposure.
        """
        if price <= 0 or atr <= 0:
            return 0
        risk_inr = self.p.account_equity * self.p.risk_per_trade
        risk_per_share = self.p.atr_stop_mult * atr
        if risk_per_share <= 0:
            return 0

        qty = int(risk_inr // risk_per_share)
        if qty <= 0:
            return 0

        cap_value = min(
            self.p.account_equity * self.p.per_trade_cap,
            self.p.account_equity * self.p.max_gross_exposure,
        )
        cap_qty = int(cap_value // price)
        return max(0, min(qty, cap_qty))

    # ---- price levels ----------------------------------------------------

    def stop_price(self, entry: float, atr: float, side: Side) -> float:
        delta = self.p.atr_stop_mult * atr
        return round(entry - delta, 2) if side == "BUY" else round(entry + delta, 2)

    def target_price(self, entry: float, atr: float, side: Side) -> float:
        delta = self.p.atr_target_mult * atr
        return round(entry + delta, 2) if side == "BUY" else round(entry - delta, 2)

    # ---- gating ----------------------------------------------------------

    def _to_ist(self, dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=IST)
        return dt.astimezone(IST)

    def can_trade_now(self, now: datetime, today_trade_count: int) -> bool:
        ist = self._to_ist(now).time()
        if ist < self.p.market_open_ist:
            return False
        # Stop opening NEW trades 30 minutes before square-off.
        cutoff = (
            datetime.combine(datetime.today(), self.p.square_off_ist)
            - timedelta(minutes=30)
        ).time()
        if ist >= cutoff:
            return False
        if today_trade_count >= self.p.max_trades_per_day:
            return False
        return True

    def should_force_exit(
        self,
        now: datetime,
        position: Position,
        last_price: Optional[float] = None,
    ) -> tuple[bool, str]:
        """
        Returns (should_exit, reason). Reasons are stable strings used in logs
        and tests: 'square_off', 'time_stop', 'stop_loss', 'take_profit'.
        """
        ist_now = self._to_ist(now)
        if ist_now.time() >= self.p.square_off_ist:
            return True, "square_off"

        bars_held = max(
            0,
            int(
                (ist_now - self._to_ist(position.entry_time)).total_seconds()
                // (60 * self.p.bar_minutes)
            ),
        )
        if bars_held >= position.max_horizon_bars:
            return True, "time_stop"

        if last_price is not None:
            if position.side == "BUY":
                if last_price <= position.stop_price:
                    return True, "stop_loss"
                if last_price >= position.target_price:
                    return True, "take_profit"
            else:
                if last_price >= position.stop_price:
                    return True, "stop_loss"
                if last_price <= position.target_price:
                    return True, "take_profit"

        return False, ""
