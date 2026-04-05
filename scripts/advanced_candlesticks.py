"""
Enhanced Candlestick Patterns from Trading Strategies
Based on patterns defined in messy_stock_book_data
"""

import pandas as pd
import numpy as np

class AdvancedCandlestickFeatures:
    """Advanced candlestick patterns from professional trading literature"""

    @staticmethod
    def evening_star(df: pd.DataFrame) -> pd.Series:
        """
        Bearish reversal pattern (3-day)
        1st day: Long white candle
        2nd day: Small body (star) that gaps above 1st day's body
        3rd day: Black candle that gaps below star and closes below midpoint of 1st day's body
        """
        # Day 1: Long white candle
        day1_white = (df['Close'].shift(2) > df['Open'].shift(2)) & \
                    ((df['Close'].shift(2) - df['Open'].shift(2)) > (df['High'].shift(2) - df['Low'].shift(2)) * 0.6)

        # Day 2: Star (small body) that gaps above day 1
        day2_body = abs(df['Close'].shift(1) - df['Open'].shift(1))
        day2_range = df['High'].shift(1) - df['Low'].shift(1)
        day2_star = (day2_body < day2_range * 0.3) & \
                   (df['Low'].shift(1) > df['Close'].shift(2))

        # Day 3: Black candle that gaps below star and closes below midpoint of day 1
        day1_midpoint = (df['Open'].shift(2) + df['Close'].shift(2)) / 2
        day3_black = (df['Close'] < df['Open']) & \
                    (df['High'] < df['Low'].shift(1)) & \
                    (df['Close'] < day1_midpoint)

        evening_star = day1_white & day2_star & day3_black
        return evening_star.astype(int).rename('evening_star')

    @staticmethod
    def morning_star(df: pd.DataFrame) -> pd.Series:
        """
        Bullish reversal pattern (3-day)
        1st day: Long black candle
        2nd day: Small body (star) that gaps below 1st day's body
        3rd day: White candle that closes more than halfway up the 1st day's body
        """
        # Day 1: Long black candle
        day1_black = (df['Close'].shift(2) < df['Open'].shift(2)) & \
                    ((df['Open'].shift(2) - df['Close'].shift(2)) > (df['High'].shift(2) - df['Low'].shift(2)) * 0.6)

        # Day 2: Star (small body) that gaps below day 1
        day2_body = abs(df['Close'].shift(1) - df['Open'].shift(1))
        day2_range = df['High'].shift(1) - df['Low'].shift(1)
        day2_star = (day2_body < day2_range * 0.3) & \
                   (df['High'].shift(1) < df['Open'].shift(2))

        # Day 3: White candle that closes more than halfway up day 1's body
        day1_body = df['Open'].shift(2) - df['Close'].shift(2)
        day3_target = df['Close'].shift(2) + (day1_body * 0.5)
        day3_white = (df['Close'] > df['Open']) & (df['Close'] > day3_target)

        morning_star = day1_black & day2_star & day3_white
        return morning_star.astype(int).rename('morning_star')

    @staticmethod
    def dark_cloud_cover(df: pd.DataFrame) -> pd.Series:
        """
        Bearish reversal pattern (2-day)
        1st day: Strong white candlestick
        2nd day: Black candlestick that opens above upper wick of white and closes below midpoint
        """
        # Day 1: Strong white candle
        day1_white = (df['Close'].shift(1) > df['Open'].shift(1)) & \
                    ((df['Close'].shift(1) - df['Open'].shift(1)) > (df['High'].shift(1) - df['Low'].shift(1)) * 0.6)

        # Day 2: Black candle that opens above day 1's high and closes below day 1's midpoint
        day1_midpoint = (df['Open'].shift(1) + df['Close'].shift(1)) / 2
        day2_black = (df['Close'] < df['Open']) & \
                    (df['Open'] > df['High'].shift(1)) & \
                    (df['Close'] < day1_midpoint)

        dark_cloud = day1_white & day2_black
        return dark_cloud.astype(int).rename('dark_cloud_cover')

    @staticmethod
    def piercing_line(df: pd.DataFrame) -> pd.Series:
        """
        Bullish reversal pattern (2-day)
        1st day: Long black candlestick
        2nd day: White candlestick that opens below lower wick and closes more than halfway above black body
        """
        # Day 1: Long black candle
        day1_black = (df['Close'].shift(1) < df['Open'].shift(1)) & \
                    ((df['Open'].shift(1) - df['Close'].shift(1)) > (df['High'].shift(1) - df['Low'].shift(1)) * 0.6)

        # Day 2: White candle that opens below day 1's low and closes more than halfway up day 1's body
        day1_body = df['Open'].shift(1) - df['Close'].shift(1)
        day2_target = df['Close'].shift(1) + (day1_body * 0.5)
        day2_white = (df['Close'] > df['Open']) & \
                    (df['Open'] < df['Low'].shift(1)) & \
                    (df['Close'] > day2_target)

        piercing = day1_black & day2_white
        return piercing.astype(int).rename('piercing_line')

    @staticmethod
    def three_black_crows(df: pd.DataFrame) -> pd.Series:
        """
        Bearish reversal pattern (3-day)
        Three declining black candlesticks, each opening within previous range and closing near low
        """
        # Three consecutive black candles
        black1 = df['Close'].shift(2) < df['Open'].shift(2)
        black2 = df['Close'].shift(1) < df['Open'].shift(1)
        black3 = df['Close'] < df['Open']

        # Each opens within/near previous real body
        open2_in_range = (df['Open'].shift(1) <= df['High'].shift(2)) & (df['Open'].shift(1) >= df['Low'].shift(2))
        open3_in_range = (df['Open'] <= df['High'].shift(1)) & (df['Open'] >= df['Low'].shift(1))

        # Each closes near its low (no lower wick)
        close_near_low1 = (df['Close'].shift(2) - df['Low'].shift(2)) < (df['High'].shift(2) - df['Low'].shift(2)) * 0.1
        close_near_low2 = (df['Close'].shift(1) - df['Low'].shift(1)) < (df['High'].shift(1) - df['Low'].shift(1)) * 0.1
        close_near_low3 = (df['Close'] - df['Low']) < (df['High'] - df['Low']) * 0.1

        # Declining closes
        declining = (df['Close'].shift(2) > df['Close'].shift(1)) & (df['Close'].shift(1) > df['Close'])

        crows = black1 & black2 & black3 & open2_in_range & open3_in_range & \
                close_near_low1 & close_near_low2 & close_near_low3 & declining

        return crows.astype(int).rename('three_black_crows')