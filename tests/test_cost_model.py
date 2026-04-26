"""
Spot-check NSEIntradayCostModel against published Zerodha / Dhan brokerage
calculator examples.

Reference (intraday equity, NSE, 2024 schedule):
    Buy  100 shares of RELIANCE @ 2500   -> turnover 2,50,000
    Sell 100 shares             @ 2510   -> turnover 2,51,000
    Brokerage  : min(20, 0.03% * t)   = 20 + 20             = 40
    STT (sell) : 0.025% * 2,51,000                          = 62.75
    Exchange   : 0.0000297 * (250000 + 251000)              ~= 14.88
    SEBI       : 0.000001 * 501000                          = 0.50
    Stamp(buy) : 0.00003 * 250000                           = 7.50
    GST 18%    : on (brokerage + exch + SEBI)               ~= 9.97
    Total                                                    ~= 135.6

Slippage is excluded from this comparison because the public calculators
don't model it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from cost_model import NSEIntradayCostModel  # noqa: E402


def test_round_trip_charges_close_to_published_calculator():
    cost = NSEIntradayCostModel(slippage_bps=0.0)

    buy = cost.leg_charges(price=2500.0, qty=100, side="BUY")
    sell = cost.leg_charges(price=2510.0, qty=100, side="SELL")

    total = buy.total + sell.total
    # Allow 5% tolerance for tiny rate updates.
    assert 128.0 <= total <= 145.0, f"unexpected charges total {total:.2f}"

    # Stamp duty is BUY-only.
    assert buy.stamp > 0
    assert sell.stamp == 0
    # STT is SELL-only.
    assert buy.stt == 0
    assert sell.stt > 0


def test_round_trip_bps_includes_slippage():
    cheap = NSEIntradayCostModel(slippage_bps=0.0).round_trip_bps(price=1000.0, qty=10)
    expensive = NSEIntradayCostModel(slippage_bps=5.0).round_trip_bps(price=1000.0, qty=10)
    assert expensive > cheap
    # Slippage is on BOTH legs, so 2 * 5 = 10 bps difference, exactly.
    assert abs((expensive - cheap) - 10.0) < 1e-6


def test_net_pnl_bps_handles_break_even():
    cost = NSEIntradayCostModel(slippage_bps=0.0)
    # Same buy and sell price -> net P&L should be NEGATIVE due to charges.
    net = cost.net_pnl_bps(entry=1000.0, exit_=1000.0, long_side=True, qty=10)
    assert net < 0


def test_bse_charges_higher_than_nse_for_same_trade():
    """Exchange transaction charge is higher on BSE (0.00375%) than NSE (0.00297%)."""
    cost = NSEIntradayCostModel(slippage_bps=0.0)
    nse = cost.round_trip_bps(price=1000.0, qty=100, exchange="NSE")
    bse = cost.round_trip_bps(price=1000.0, qty=100, exchange="BSE")
    assert bse > nse
    # The gap should be roughly 2 * (0.00375 - 0.00297)% on each leg, scaled by GST.
    assert 0.10 < (bse - nse) < 0.40


def test_default_exchange_respected():
    cost_nse = NSEIntradayCostModel(slippage_bps=0.0, default_exchange="NSE")
    cost_bse = NSEIntradayCostModel(slippage_bps=0.0, default_exchange="BSE")
    a = cost_nse.round_trip_bps(price=1000.0, qty=100)
    b = cost_bse.round_trip_bps(price=1000.0, qty=100)
    assert b > a


def test_invalid_inputs_rejected():
    cost = NSEIntradayCostModel()
    with pytest.raises(ValueError):
        cost.leg_charges(price=0.0, qty=10, side="BUY")
    with pytest.raises(ValueError):
        cost.leg_charges(price=100.0, qty=0, side="BUY")
    with pytest.raises(ValueError):
        NSEIntradayCostModel(slippage_bps=-1.0)
