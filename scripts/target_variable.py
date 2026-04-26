"""
PHASE 4: Define Target Variable
Create target for 10-minute stock price prediction
"""

from __future__ import annotations

import pandas as pd
import numpy as np


class TargetVariable:
    """Define and create target variables for intraday stock prediction"""
    
    @staticmethod
    def next_candle_direction(df: pd.DataFrame, hours_ahead: int = 0, minutes_ahead: int = 10) -> pd.Series:
        """
        Predict if price will go UP or DOWN in next 10 minutes
        Returns: 1 for UP, 0 for DOWN
        """
        # Calculate future price (next 10 minutes)
        future_close = df['Close'].shift(-1)  # Next candle close
        
        # Determine if price went up (1) or down (0)
        target = (future_close > df['Close']).astype(int)
        
        return target.rename('target_direction')
    
    @staticmethod
    def price_change_percentage(df: pd.DataFrame) -> pd.Series:
        """Percentage change for next candle"""
        future_close = df['Close'].shift(-1)
        pct_change = ((future_close - df['Close']) / df['Close'] * 100)
        return pct_change.rename('price_change_pct')
    
    @staticmethod
    def price_change_points(df: pd.DataFrame) -> pd.Series:
        """Absolute point change"""
        future_close = df['Close'].shift(-1)
        point_change = future_close - df['Close']
        return point_change.rename('price_change_points')
    
    @staticmethod
    def binary_classification_target(df: pd.DataFrame, threshold_pct: float = 0.0) -> pd.Series:
        """
        Binary target with threshold
        1: Price goes up by threshold% or more
        0: Price stays flat or goes down
        """
        future_close = df['Close'].shift(-1)
        pct_change = ((future_close - df['Close']) / df['Close'] * 100)
        target = (pct_change > threshold_pct).astype(int)
        return target.rename('target_binary')
    
    @staticmethod
    def multiclass_target(df: pd.DataFrame, up_threshold: float = 0.5, down_threshold: float = -0.5) -> pd.Series:
        """
        3-class target:
        1: Strong UP (change > up_threshold %)
        0: NEUTRAL (between thresholds)
        -1: Strong DOWN (change < down_threshold %)
        """
        future_close = df['Close'].shift(-1)
        pct_change = ((future_close - df['Close']) / df['Close'] * 100)
        
        target = np.where(pct_change > up_threshold, 1,
                         np.where(pct_change < down_threshold, -1, 0))
        
        return pd.Series(target, index=df.index, name='target_multiclass')
    
    @staticmethod
    def create_all_targets(df: pd.DataFrame) -> pd.DataFrame:
        """Create all target variable types"""
        targets = pd.DataFrame(index=df.index)
        
        targets['target_direction'] = TargetVariable.next_candle_direction(df)
        targets['price_change_pct'] = TargetVariable.price_change_percentage(df)
        targets['price_change_points'] = TargetVariable.price_change_points(df)
        targets['target_binary'] = TargetVariable.binary_classification_target(df, threshold_pct=0.0)
        targets['target_multiclass'] = TargetVariable.multiclass_target(df)
        
        return targets


def _compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """ATR (Wilder) computed strictly from past bars; safe to use as a feature."""
    high, low, close = df['High'], df['Low'], df['Close']
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


class TripleBarrier:
    """
    Triple-barrier labeling (Lopez de Prado).

    For each bar i we open a hypothetical long+short straddle at the next bar's
    open and watch the next ``max_horizon`` bars. The label is:

        +1 if the upper barrier is hit first
        -1 if the lower barrier is hit first
         0 otherwise (timeout) -- such samples are dropped from training

    The barrier widths are k * ATR(period) so they scale with volatility.

    Cost-aware no-trade zone:
        Samples whose barrier width in bps is below ``min_move_bps`` are
        labeled 0 and dropped. This prevents the model from learning to
        trade through the spread.
    """

    @staticmethod
    def label(
        df: pd.DataFrame,
        up_mult: float = 1.0,
        dn_mult: float = 1.0,
        max_horizon: int = 5,
        atr_period: int = 14,
        min_move_bps: float = 0.0,
        atr: pd.Series | None = None,
    ) -> pd.DataFrame:
        """
        Returns a DataFrame indexed like ``df`` with columns:
            label    -- {-1, 0, +1}, dtype int
            entry    -- price assumed for the trade entry (next bar Open)
            barrier  -- 'up', 'dn', or 'time'
            ret_bps  -- realised return at exit, in bps of entry
            atr      -- ATR used for the barrier
            tradable -- bool; False if dropped (timeout, NaN ATR, or below
                        cost zone)
        """
        if atr is None:
            atr = _compute_atr(df, period=atr_period)

        n = len(df)
        labels = np.zeros(n, dtype=np.int8)
        entries = np.full(n, np.nan)
        barriers = np.array(['none'] * n, dtype=object)
        ret_bps = np.full(n, np.nan)
        tradable = np.zeros(n, dtype=bool)

        opens = df['Open'].to_numpy()
        highs = df['High'].to_numpy()
        lows = df['Low'].to_numpy()
        closes = df['Close'].to_numpy()
        atr_arr = atr.to_numpy()

        for i in range(n - 1):
            atr_i = atr_arr[i]
            if not np.isfinite(atr_i) or atr_i <= 0:
                continue

            entry = opens[i + 1]
            if not np.isfinite(entry) or entry <= 0:
                continue

            barrier_width_bps = (up_mult * atr_i / entry) * 1e4
            if barrier_width_bps < min_move_bps:
                # No-trade zone: barriers narrower than friction
                entries[i] = entry
                continue

            up = entry + up_mult * atr_i
            dn = entry - dn_mult * atr_i
            horizon_end = min(i + 1 + max_horizon, n)

            label = 0
            barrier_kind = 'time'
            exit_price = closes[horizon_end - 1] if horizon_end > i + 1 else entry

            for j in range(i + 1, horizon_end):
                hi, lo = highs[j], lows[j]
                hit_up = hi >= up
                hit_dn = lo <= dn
                if hit_up and hit_dn:
                    # Conservative: assume the adverse barrier hit first.
                    label, barrier_kind, exit_price = -1, 'dn', dn
                    break
                if hit_up:
                    label, barrier_kind, exit_price = +1, 'up', up
                    break
                if hit_dn:
                    label, barrier_kind, exit_price = -1, 'dn', dn
                    break

            labels[i] = label
            entries[i] = entry
            barriers[i] = barrier_kind
            ret_bps[i] = (exit_price - entry) / entry * 1e4
            tradable[i] = label != 0

        result = pd.DataFrame(
            {
                'label': labels,
                'entry': entries,
                'barrier': barriers,
                'ret_bps': ret_bps,
                'atr': atr_arr,
                'tradable': tradable,
            },
            index=df.index,
        )
        return result

    @staticmethod
    def to_binary(label_df: pd.DataFrame) -> pd.Series:
        """
        Convert {-1, 0, +1} to {0, 1} for binary classifiers, dropping the 0
        (no-trade) samples via the ``tradable`` mask.
        """
        binary = (label_df['label'] > 0).astype(int)
        binary[~label_df['tradable']] = -1  # sentinel; caller masks with tradable
        return binary.rename('target_triple_barrier')
