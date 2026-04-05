"""
Market Breadth Indicators from Trading Strategies
Based on indicators defined in messy_stock_book_data
"""

import pandas as pd
import numpy as np

class MarketBreadthIndicators:
    """Market breadth indicators from professional trading literature"""

    @staticmethod
    def tick_indicator(df: pd.DataFrame, tick_col: str = 'tick') -> pd.Series:
        """
        NYSE TICK ($TICK)
        Number of stocks increasing minus number decreasing
        Action levels: +1000, +800, +600, -600, -800, -1000
        """
        if tick_col not in df.columns:
            # If no tick data, approximate using price changes
            tick = df['Close'].pct_change() * 1000
        else:
            tick = df[tick_col]

        return tick.rename('tick')

    @staticmethod
    def tiki_indicator(df: pd.DataFrame, tiki_col: str = 'tiki') -> pd.Series:
        """
        TIKI ($TIKI)
        Net upticks vs downticks on 30 Dow stocks
        Alerts: +26, +28, +30 (upside), -26, -28, -30 (downside)
        """
        if tiki_col not in df.columns:
            # Approximate using volume-weighted price changes
            tiki = df['Close'].pct_change() * df['Volume'].pct_change() * 100
        else:
            tiki = df[tiki_col]

        return tiki.rename('tiki')

    @staticmethod
    def trin_indicator(df: pd.DataFrame, adv_volume: str = 'adv_volume',
                      dec_volume: str = 'dec_volume', adv_stocks: str = 'adv_stocks',
                      dec_stocks: str = 'dec_stocks') -> pd.Series:
        """
        TRIN (Arms Index)
        Ratio of advancing volume to declining volume divided by
        ratio of advancing stocks to declining stocks
        """
        if all(col in df.columns for col in [adv_volume, dec_volume, adv_stocks, dec_stocks]):
            volume_ratio = df[adv_volume] / df[dec_volume]
            stock_ratio = df[adv_stocks] / df[dec_stocks]
            trin = volume_ratio / stock_ratio
        else:
            # Approximate using price and volume changes
            price_change = df['Close'].pct_change()
            volume_change = df['Volume'].pct_change()

            adv_price = (price_change > 0).astype(int)
            dec_price = (price_change < 0).astype(int)
            adv_vol = volume_change * (price_change > 0)
            dec_vol = volume_change * (price_change < 0)

            volume_ratio = adv_vol.sum() / dec_vol.sum() if dec_vol.sum() != 0 else 1
            stock_ratio = adv_price.sum() / dec_price.sum() if dec_price.sum() != 0 else 1
            trin = volume_ratio / stock_ratio

        return pd.Series(trin, index=df.index, name='trin')


class TradingStrategyFeatures:
    """Features derived from trading strategies"""

    @staticmethod
    def opening_gap_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Opening Gap Strategy features
        - Gap size (absolute and percentage)
        - Gap direction (up/down)
        - Pre-market volume context
        """
        features = pd.DataFrame(index=df.index)

        # Calculate gaps (assuming we have pre-market data)
        if 'pre_market_close' in df.columns:
            gap = df['Open'] - df['pre_market_close']
            features['gap_size_abs'] = gap.abs()
            features['gap_size_pct'] = gap / df['pre_market_close']
            features['gap_up'] = (gap > 0).astype(int)
            features['gap_down'] = (gap < 0).astype(int)
        else:
            # Approximate using previous close
            gap = df['Open'] - df['Close'].shift(1)
            features['gap_size_abs'] = gap.abs()
            features['gap_size_pct'] = gap / df['Close'].shift(1)
            features['gap_up'] = (gap > 0).astype(int)
            features['gap_down'] = (gap < 0).astype(int)

        # Gap fill targets (50% and 100%)
        features['gap_fill_50'] = features['gap_size_abs'] * 0.5
        features['gap_fill_100'] = features['gap_size_abs']

        return features

    @staticmethod
    def pivot_point_features(df: pd.DataFrame, timeframe: str = 'daily') -> pd.DataFrame:
        """
        Pivot Point trading features
        - Distance from pivot levels
        - Pivot level identification
        - Support/resistance proximity
        """
        features = pd.DataFrame(index=df.index)

        if timeframe == 'daily':
            # Calculate daily pivots
            high = df['High']
            low = df['Low']
            close = df['Close']

            pivot = (high + low + close) / 3
            r1 = 2 * pivot - low
            s1 = 2 * pivot - high
            r2 = pivot + (high - low)
            s2 = pivot - (high - low)

            features['pivot_level'] = pivot
            features['r1_level'] = r1
            features['s1_level'] = s1
            features['r2_level'] = r2
            features['s2_level'] = s2

            # Distance from current price to pivot levels
            features['dist_to_pivot'] = (df['Close'] - pivot).abs()
            features['dist_to_r1'] = (df['Close'] - r1).abs()
            features['dist_to_s1'] = (df['Close'] - s1).abs()

            # Above/below pivot
            features['above_pivot'] = (df['Close'] > pivot).astype(int)
            features['below_pivot'] = (df['Close'] < pivot).astype(int)

        return features

    @staticmethod
    def scalping_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Scalping strategy features
        - Consecutive higher/lower closes
        - Tick extremes
        - Quick reversal signals
        """
        features = pd.DataFrame(index=df.index)

        # Consecutive closes (for 3 consecutive higher closes)
        close_higher = df['Close'] > df['Close'].shift(1)
        features['consec_higher_3'] = (close_higher & close_higher.shift(1) & close_higher.shift(2)).astype(int)

        close_lower = df['Close'] < df['Close'].shift(1)
        features['consec_lower_3'] = (close_lower & close_lower.shift(1) & close_lower.shift(2)).astype(int)

        # Tick extremes (approximated)
        price_change = df['Close'].pct_change()
        features['extreme_tick_up'] = (price_change > price_change.quantile(0.95)).astype(int)
        features['extreme_tick_down'] = (price_change < price_change.quantile(0.05)).astype(int)

        return features