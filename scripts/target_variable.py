"""
PHASE 4: Define Target Variable
Create target for 10-minute stock price prediction
"""

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
