"""
TripleBarrier label tests using synthetic OHLCV where each barrier outcome
is forced. We pre-bake an ATR series so the test is deterministic and does
not depend on the warm-up window of the EWMA-based ATR.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from target_variable import TripleBarrier  # noqa: E402


def _make_df(rows):
    df = pd.DataFrame(rows, columns=["Open", "High", "Low", "Close"])
    df["Volume"] = 1_000
    return df


def test_upper_barrier_hit_first():
    # Bar 0: signal. Entry = bar 1 open = 100. ATR=1. Up=101, Dn=99.
    # Bar 1: high 101.5 -> upper hit immediately.
    df = _make_df(
        [
            (100, 100, 100, 100),  # signal bar
            (100, 101.5, 99.5, 101.0),  # entry bar; up barrier touched
            (101, 102, 101, 101),
            (101, 102, 101, 101),
            (101, 102, 101, 101),
            (101, 102, 101, 101),
        ]
    )
    atr = pd.Series([1.0] * len(df))
    out = TripleBarrier.label(df, up_mult=1.0, dn_mult=1.0, max_horizon=3, atr=atr)
    assert out.iloc[0]["label"] == 1
    assert out.iloc[0]["barrier"] == "up"
    assert out.iloc[0]["tradable"]


def test_lower_barrier_hit_first():
    df = _make_df(
        [
            (100, 100, 100, 100),
            (100, 100.5, 98.5, 99.0),  # low 98.5 < dn=99 -> lower hit
            (99, 100, 98, 99),
            (99, 100, 98, 99),
        ]
    )
    atr = pd.Series([1.0] * len(df))
    out = TripleBarrier.label(df, up_mult=1.0, dn_mult=1.0, max_horizon=3, atr=atr)
    assert out.iloc[0]["label"] == -1
    assert out.iloc[0]["barrier"] == "dn"


def test_timeout_drops_sample():
    # Neither barrier is hit within horizon -> label 0, tradable False.
    df = _make_df(
        [
            (100, 100, 100, 100),
            (100, 100.4, 99.7, 100.1),
            (100, 100.4, 99.7, 100.1),
            (100, 100.4, 99.7, 100.1),
        ]
    )
    atr = pd.Series([1.0] * len(df))
    out = TripleBarrier.label(df, up_mult=1.0, dn_mult=1.0, max_horizon=3, atr=atr)
    assert out.iloc[0]["label"] == 0
    assert out.iloc[0]["barrier"] == "time"
    assert not out.iloc[0]["tradable"]


def test_no_trade_zone_drops_narrow_barriers():
    # ATR very small -> barrier width tiny in bps. Cost zone of 100 bps drops it.
    df = _make_df([(100, 100, 100, 100), (100, 100.01, 99.99, 100.0)] * 5)
    atr = pd.Series([0.001] * len(df))  # 1 bps barrier width
    out = TripleBarrier.label(
        df, up_mult=1.0, dn_mult=1.0, max_horizon=3, atr=atr, min_move_bps=100.0
    )
    # All entries hit the no-trade zone -> label 0, NOT tradable.
    assert (out["label"] == 0).all()
    assert (~out["tradable"]).all()
