"""
NSE Intraday cost model.

All charges follow the published 2024 schedule for retail intraday equity on
NSE through a discount broker (Dhan / Zerodha). Numbers are kept as named
constants so they are easy to audit and update.

The model is used in two places that MUST agree:
  1. Triple-barrier labeling (the no-trade zone uses round-trip cost in bps).
  2. Walk-forward backtest (subtracts net cost from each trade P&L).

Pure functions, no I/O, no globals other than rate constants.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


# ---------------------------------------------------------------------------
# Rate constants (decimals, NOT percent). Update these in one place.
# ---------------------------------------------------------------------------

# Brokerage: flat Rs 20 per executed order OR 0.03% of turnover, whichever lower
BROKERAGE_FLAT_INR = 20.0
BROKERAGE_PCT = 0.0003  # 0.03%

# Securities Transaction Tax: 0.025% on SELL side only (intraday equity)
STT_SELL_PCT = 0.00025

# Exchange transaction charges on turnover (differ by exchange).
#   NSE equity: 0.00297%   BSE equity: 0.00375%
EXCHANGE_TXN_PCT_NSE = 0.0000297
EXCHANGE_TXN_PCT_BSE = 0.0000375
EXCHANGE_TXN_PCT = EXCHANGE_TXN_PCT_NSE  # legacy alias; do not use in new code

# SEBI turnover fees: Rs 10 per crore = 0.0001%
SEBI_PCT = 0.000001

# Stamp duty on BUY side only: 0.003%
STAMP_BUY_PCT = 0.00003

# GST applied to (brokerage + exchange + SEBI)
GST_PCT = 0.18


Side = Literal["BUY", "SELL"]
Exchange = Literal["NSE", "BSE"]


def _exchange_pct(exchange: Exchange) -> float:
    if exchange == "NSE":
        return EXCHANGE_TXN_PCT_NSE
    if exchange == "BSE":
        return EXCHANGE_TXN_PCT_BSE
    raise ValueError(f"Unsupported exchange: {exchange}")


@dataclass(frozen=True)
class TradeCharges:
    """Itemized charges for a single fill leg in INR."""
    brokerage: float
    stt: float
    exchange: float
    sebi: float
    stamp: float
    gst: float

    @property
    def total(self) -> float:
        return (
            self.brokerage + self.stt + self.exchange + self.sebi + self.stamp + self.gst
        )


class IndianIntradayCostModel:
    """
    Cost model for retail intraday equity on Indian exchanges (NSE / BSE)
    through a Dhan-style discount broker. Every method takes an explicit
    ``exchange`` so the same instance can price trades on either venue.

    Parameters
    ----------
    slippage_bps:
        Half-spread + market-impact estimate applied to every fill in basis
        points. Default 3 bps reflects liquid large-caps; raise to 5-10 bps
        for less liquid names.
    default_exchange:
        Used when the caller does not pass ``exchange`` to a method. Defaults
        to ``"NSE"``.
    """

    def __init__(self, slippage_bps: float = 3.0, default_exchange: Exchange = "NSE"):
        if slippage_bps < 0:
            raise ValueError("slippage_bps must be >= 0")
        _exchange_pct(default_exchange)  # validate
        self.slippage_bps = slippage_bps
        self.default_exchange: Exchange = default_exchange

    # ---- per-leg charges -------------------------------------------------

    def leg_charges(
        self,
        price: float,
        qty: int,
        side: Side,
        exchange: Optional[Exchange] = None,
    ) -> TradeCharges:
        """Charges in INR for a single fill leg."""
        if price <= 0 or qty <= 0:
            raise ValueError("price and qty must be > 0")

        ex = exchange or self.default_exchange
        exchange_pct = _exchange_pct(ex)
        turnover = price * qty

        brokerage = min(BROKERAGE_FLAT_INR, BROKERAGE_PCT * turnover)
        stt = STT_SELL_PCT * turnover if side == "SELL" else 0.0
        exchange_charge = exchange_pct * turnover
        sebi = SEBI_PCT * turnover
        stamp = STAMP_BUY_PCT * turnover if side == "BUY" else 0.0
        gst = GST_PCT * (brokerage + exchange_charge + sebi)

        return TradeCharges(brokerage, stt, exchange_charge, sebi, stamp, gst)

    # ---- effective fill prices ------------------------------------------

    def fill_price(self, mid_price: float, side: Side) -> float:
        """Return the effective fill price after slippage."""
        slip = mid_price * self.slippage_bps / 1e4
        return mid_price + slip if side == "BUY" else mid_price - slip

    # ---- round-trip helpers ---------------------------------------------

    def round_trip_inr(
        self,
        entry: float,
        exit_: float,
        qty: int,
        long_side: bool,
        exchange: Optional[Exchange] = None,
    ) -> float:
        """Total INR charges for one open + one close leg (slippage NOT included)."""
        buy_leg = self.leg_charges(entry if long_side else exit_, qty, "BUY", exchange)
        sell_leg = self.leg_charges(exit_ if long_side else entry, qty, "SELL", exchange)
        return buy_leg.total + sell_leg.total

    def round_trip_bps(
        self,
        price: float,
        qty: int = 1,
        exchange: Optional[Exchange] = None,
    ) -> float:
        """
        Approximate round-trip cost in basis points of turnover, including
        slippage on both legs. Used by the labeler to set the no-trade zone.
        """
        if price <= 0:
            raise ValueError("price must be > 0")
        # Use price for both legs (zero PnL trade) so we measure pure friction.
        charges = self.round_trip_inr(price, price, qty, long_side=True, exchange=exchange)
        turnover = price * qty
        charge_bps = charges / turnover * 1e4
        slip_bps = 2.0 * self.slippage_bps  # both legs
        return charge_bps + slip_bps

    # ---- net PnL on a closed trade --------------------------------------

    def net_pnl_inr(
        self,
        entry: float,
        exit_: float,
        qty: int,
        long_side: bool,
        exchange: Optional[Exchange] = None,
    ) -> float:
        """
        Net INR P&L on a closed round-trip trade, AFTER slippage and charges.
        `entry` and `exit_` are mid prices; slippage is applied here so the
        caller passes raw prices.
        """
        buy_mid, sell_mid = (entry, exit_) if long_side else (exit_, entry)
        buy_fill = self.fill_price(buy_mid, "BUY")
        sell_fill = self.fill_price(sell_mid, "SELL")

        gross = (sell_fill - buy_fill) * qty
        charges = self.round_trip_inr(buy_fill, sell_fill, qty, long_side=True, exchange=exchange)
        return gross - charges

    def net_pnl_bps(
        self,
        entry: float,
        exit_: float,
        long_side: bool,
        qty: int = 1,
        exchange: Optional[Exchange] = None,
    ) -> float:
        """Net P&L in bps of entry turnover (sign matches trade direction)."""
        if entry <= 0:
            raise ValueError("entry must be > 0")
        net = self.net_pnl_inr(entry, exit_, qty, long_side, exchange=exchange)
        return net / (entry * qty) * 1e4


# Back-compat alias so existing imports keep working unchanged.
NSEIntradayCostModel = IndianIntradayCostModel
