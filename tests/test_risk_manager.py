"""
RiskManager unit tests: sizing math, stop/target signs, daily limit and the
15:20 IST square-off behaviour.
"""
from __future__ import annotations

import sys
from datetime import datetime, time
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from risk_manager import IST, Position, RiskManager, RiskParams  # noqa: E402


def _rm(**overrides) -> RiskManager:
    params = dict(account_equity=100_000.0, risk_per_trade=0.01)
    params.update(overrides)
    return RiskManager(RiskParams(**params))


def test_size_uses_risk_per_trade_and_atr_stop():
    # equity 100k, risk 1% = 1000. ATR=1, stop_mult=2 -> risk per share = 2.
    # qty = 1000 / 2 = 500.
    rm = _rm(atr_stop_mult=2.0, atr_target_mult=4.0, per_trade_cap=1.0)
    qty = rm.size(price=200.0, atr=1.0, side="BUY")
    assert qty == 500


def test_size_capped_by_per_trade_cap():
    # per_trade_cap 0.10 of 100k = 10k -> at price 200 cap = 50 shares.
    rm = _rm(atr_stop_mult=0.01, per_trade_cap=0.10)  # tiny atr-based risk -> cap dominates
    qty = rm.size(price=200.0, atr=0.5, side="BUY")
    assert qty == 50


def test_stop_and_target_signs_respect_side():
    rm = _rm(atr_stop_mult=1.0, atr_target_mult=2.0)
    long_stop = rm.stop_price(100.0, atr=2.0, side="BUY")
    long_target = rm.target_price(100.0, atr=2.0, side="BUY")
    assert long_stop < 100 < long_target

    short_stop = rm.stop_price(100.0, atr=2.0, side="SELL")
    short_target = rm.target_price(100.0, atr=2.0, side="SELL")
    assert short_target < 100 < short_stop


def test_can_trade_now_blocks_after_cutoff():
    rm = _rm(square_off_ist=time(15, 20))
    market_open = datetime(2026, 1, 5, 10, 0, tzinfo=IST)
    after_cutoff = datetime(2026, 1, 5, 15, 0, tzinfo=IST)  # cutoff = 14:50

    assert rm.can_trade_now(market_open, today_trade_count=0)
    assert not rm.can_trade_now(after_cutoff, today_trade_count=0)


def test_can_trade_now_respects_daily_limit():
    rm = _rm(max_trades_per_day=2)
    t = datetime(2026, 1, 5, 10, 0, tzinfo=IST)
    assert rm.can_trade_now(t, today_trade_count=1)
    assert not rm.can_trade_now(t, today_trade_count=2)


def test_should_force_exit_square_off():
    rm = _rm()
    pos = Position(
        symbol="X",
        side="BUY",
        qty=10,
        entry_price=100.0,
        entry_time=datetime(2026, 1, 5, 10, 0, tzinfo=IST),
        stop_price=98.0,
        target_price=104.0,
    )
    at_square_off = datetime(2026, 1, 5, 15, 21, tzinfo=IST)
    should, reason = rm.should_force_exit(at_square_off, pos)
    assert should and reason == "square_off"


def test_should_force_exit_stop_loss_then_target():
    rm = _rm()
    pos = Position(
        symbol="X",
        side="BUY",
        qty=10,
        entry_price=100.0,
        entry_time=datetime(2026, 1, 5, 10, 0, tzinfo=IST),
        stop_price=98.0,
        target_price=104.0,
    )
    t = datetime(2026, 1, 5, 10, 5, tzinfo=IST)
    assert rm.should_force_exit(t, pos, last_price=97.5) == (True, "stop_loss")
    assert rm.should_force_exit(t, pos, last_price=105.0) == (True, "take_profit")
    assert rm.should_force_exit(t, pos, last_price=101.0) == (False, "")


def test_invalid_params_rejected():
    with pytest.raises(ValueError):
        RiskManager(RiskParams(account_equity=0.0))
    with pytest.raises(ValueError):
        RiskManager(RiskParams(account_equity=1.0, risk_per_trade=1.5))
