"""
PHASE 2 & 3: Feature Engineering
Convert candlestick patterns, trading setups, and indicators into ML features
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class CandlestickPatternFeatures:
    """Convert candlestick patterns to binary features"""
    
    @staticmethod
    def hollow_white_candle(df: pd.DataFrame) -> pd.Series:
        """Bullish: Close > Open"""
        return ((df['Close'] > df['Open']).astype(int)).rename('hollow_white_candle')
    
    @staticmethod
    def filled_black_candle(df: pd.DataFrame) -> pd.Series:
        """Bearish: Close < Open"""
        return ((df['Close'] < df['Open']).astype(int)).rename('filled_black_candle')
    
    @staticmethod
    def spinning_top(df: pd.DataFrame, threshold=0.1) -> pd.Series:
        """Neutral: Small body with large wicks"""
        body = (df['Close'] - df['Open']).abs()
        total_range = df['High'] - df['Low']
        upper_wick = df['High'] - df[['Open', 'Close']].max(axis=1)
        lower_wick = df[['Open', 'Close']].min(axis=1) - df['Low']
        
        is_spinning = (body < total_range * threshold) & \
                      (upper_wick > body * 2) & \
                      (lower_wick > body * 2)
        return is_spinning.astype(int).rename('spinning_top')
    
    @staticmethod
    def doji(df: pd.DataFrame, threshold=0.01) -> pd.Series:
        """Neutral: Open ≈ Close"""
        body = (df['Close'] - df['Open']).abs()
        avg_price = (df['High'] + df['Low']) / 2 * threshold
        is_doji = body <= avg_price
        return is_doji.astype(int).rename('doji')
    
    @staticmethod
    def hammer(df: pd.DataFrame, window=1) -> pd.Series:
        """Bullish reversal: Small body at top, long lower wick"""
        body = (df['Close'] - df['Open']).abs()
        upper_wick = df['High'] - df[['Open', 'Close']].max(axis=1)
        lower_wick = df[['Open', 'Close']].min(axis=1) - df['Low']
        
        is_hammer = (lower_wick > body * 2) & (upper_wick < body) & (df['Close'] > df['Open'])
        return is_hammer.astype(int).rename('hammer')
    
    @staticmethod
    def shooting_star(df: pd.DataFrame) -> pd.Series:
        """Bearish reversal: Small body at bottom, long upper wick"""
        body = (df['Close'] - df['Open']).abs()
        upper_wick = df['High'] - df[['Open', 'Close']].max(axis=1)
        lower_wick = df[['Open', 'Close']].min(axis=1) - df['Low']
        
        is_star = (upper_wick > body * 2) & (lower_wick < body) & (df['Close'] < df['Open'])
        return is_star.astype(int).rename('shooting_star')
    
    @staticmethod
    def engulfing_pattern(df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Bullish/Bearish: Current candle engulfs previous"""
        bullish_engulfing = (
            (df['Close'].shift(1) < df['Open'].shift(1)) &  # Prev is black
            (df['Close'] > df['Open']) &  # Current is white
            (df['Open'] < df['Close'].shift(1)) &  # Current opens below prev close
            (df['Close'] > df['Open'].shift(1))  # Current closes above prev open
        ).astype(int).rename('bullish_engulfing')
        
        bearish_engulfing = (
            (df['Close'].shift(1) > df['Open'].shift(1)) &  # Prev is white
            (df['Close'] < df['Open']) &  # Current is black
            (df['Open'] > df['Close'].shift(1)) &  # Current opens above prev close
            (df['Close'] < df['Open'].shift(1))  # Current closes below prev open
        ).astype(int).rename('bearish_engulfing')
        
        return {'bullish_engulfing': bullish_engulfing, 'bearish_engulfing': bearish_engulfing}


class IndicatorFeatures:
    """Convert technical indicators to ML features"""
    
    @staticmethod
    def rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.rename('rsi')
    
    @staticmethod
    def macd(df: pd.DataFrame, fast=12, slow=26, signal=9) -> Dict[str, pd.Series]:
        """Moving Average Convergence Divergence"""
        ema_fast = df['Close'].ewm(span=fast).mean()
        ema_slow = df['Close'].ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line.rename('macd'),
            'macd_signal': signal_line.rename('macd_signal'),
            'macd_histogram': histogram.rename('macd_histogram')
        }
    
    @staticmethod
    def bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """Bollinger Bands"""
        sma = df['Close'].rolling(window=period).mean()
        std = df['Close'].rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return {
            'bb_upper': upper.rename('bb_upper'),
            'bb_middle': sma.rename('bb_middle'),
            'bb_lower': lower.rename('bb_lower')
        }
    
    @staticmethod
    def stochastic(df: pd.DataFrame, period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> Dict[str, pd.Series]:
        """Stochastic Oscillator"""
        low_min = df['Low'].rolling(window=period).min()
        high_max = df['High'].rolling(window=period).max()
        
        k = 100 * ((df['Close'] - low_min) / (high_max - low_min))
        k_smooth = k.rolling(window=smooth_k).mean()
        d_smooth = k_smooth.rolling(window=smooth_d).mean()
        
        return {
            'stoch_k': k_smooth.rename('stoch_k'),
            'stoch_d': d_smooth.rename('stoch_d')
        }
    
    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range (Volatility)"""
        tr1 = df['High'] - df['Low']
        tr2 = (df['High'] - df['Close'].shift()).abs()
        tr3 = (df['Low'] - df['Close'].shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr.rename('atr')
    
    @staticmethod
    def pivot_points(df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Floor Pivot Points"""
        pivot = (df['High'] + df['Low'] + df['Close']) / 3
        s1 = (2 * pivot) - df['High']
        s2 = pivot - (df['High'] - df['Low'])
        r1 = (2 * pivot) - df['Low']
        r2 = pivot + (df['High'] - df['Low'])
        
        return {
            'pivot': pivot.rename('pivot'),
            's1': s1.rename('s1'),
            's2': s2.rename('s2'),
            'r1': r1.rename('r1'),
            'r2': r2.rename('r2')
        }


class TimeSeriesFeatures:
    """PHASE 3: Add mathematical and statistical time-series features"""
    
    @staticmethod
    def lag_features(df: pd.DataFrame, lags: List[int] = [1, 2, 3]) -> pd.DataFrame:
        """Previous candle features"""
        lag_df = pd.DataFrame()
        for lag in lags:
            lag_df[f'close_lag_{lag}'] = df['Close'].shift(lag)
            lag_df[f'high_lag_{lag}'] = df['High'].shift(lag)
            lag_df[f'low_lag_{lag}'] = df['Low'].shift(lag)
            lag_df[f'volume_lag_{lag}'] = df['Volume'].shift(lag)
        return lag_df
    
    @staticmethod
    def returns_features(df: pd.DataFrame, periods: List[int] = [1, 3, 5]) -> pd.DataFrame:
        """Price returns"""
        returns_df = pd.DataFrame()
        for period in periods:
            returns_df[f'return_{period}'] = df['Close'].pct_change(period)
        return returns_df
    
    @staticmethod
    def rolling_features(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """Rolling statistics"""
        rolling_df = pd.DataFrame()
        rolling_df[f'rolling_mean_{window}'] = df['Close'].rolling(window).mean()
        rolling_df[f'rolling_std_{window}'] = df['Close'].rolling(window).std()
        rolling_df[f'rolling_max_{window}'] = df['Close'].rolling(window).max()
        rolling_df[f'rolling_min_{window}'] = df['Close'].rolling(window).min()
        rolling_df[f'rolling_volume_mean_{window}'] = df['Volume'].rolling(window).mean()
        return rolling_df
    
    @staticmethod
    def momentum_features(df: pd.DataFrame, period: int = 10) -> pd.Series:
        """Momentum indicator"""
        momentum = df['Close'] - df['Close'].shift(period)
        return momentum.rename('momentum')
    
    @staticmethod
    def volatility_features(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Volatility features"""
        vol_df = pd.DataFrame()
        vol_df['volatility'] = df['Close'].pct_change().rolling(period).std()
        vol_df['z_score'] = (df['Close'] - df['Close'].rolling(period).mean()) / df['Close'].rolling(period).std()
        return vol_df


class MarketStructureFeatures:
    """Market structure features - trend and volatility patterns"""
    
    @staticmethod
    def higher_high_lower_low(df: pd.DataFrame) -> pd.DataFrame:
        """Identify higher highs and lower lows for trend structure"""
        structure_df = pd.DataFrame(index=df.index)
        structure_df['higher_high'] = (df['High'] > df['High'].shift(1)).astype(int)
        structure_df['lower_low'] = (df['Low'] < df['Low'].shift(1)).astype(int)
        structure_df['higher_low'] = (df['Low'] > df['Low'].shift(1)).astype(int)
        structure_df['lower_high'] = (df['High'] < df['High'].shift(1)).astype(int)
        return structure_df
    
    @staticmethod
    def breakout_levels(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """Identify breakout levels and support/resistance"""
        breakout_df = pd.DataFrame(index=df.index)
        breakout_df['breakout_up'] = (df['Close'] > df['High'].rolling(period).max().shift(1)).astype(int)
        breakout_df['breakout_down'] = (df['Close'] < df['Low'].rolling(period).min().shift(1)).astype(int)
        breakout_df['resistance'] = df['High'].rolling(period).max()
        breakout_df['support'] = df['Low'].rolling(period).min()
        breakout_df['price_above_resistance'] = (df['Close'] > breakout_df['resistance'].shift(1)).astype(int)
        breakout_df['price_below_support'] = (df['Close'] < breakout_df['support'].shift(1)).astype(int)
        return breakout_df


class PriceActionFeatures:
    """Pure price action patterns - raw market behavior"""
    
    @staticmethod
    def candle_anatomy(df: pd.DataFrame) -> pd.DataFrame:
        """Decompose candles into body, wicks, and ranges"""
        action_df = pd.DataFrame(index=df.index)
        action_df['body'] = df['Close'] - df['Open']
        action_df['body_abs'] = (df['Close'] - df['Open']).abs()
        action_df['range'] = df['High'] - df['Low']
        action_df['upper_wick'] = df['High'] - df[['Close', 'Open']].max(axis=1)
        action_df['lower_wick'] = df[['Close', 'Open']].min(axis=1) - df['Low']
        action_df['body_ratio'] = action_df['body_abs'] / (action_df['range'] + 1e-8)
        action_df['wick_ratio'] = (action_df['upper_wick'] + action_df['lower_wick']) / (action_df['range'] + 1e-8)
        return action_df
    
    @staticmethod
    def price_pressure(df: pd.DataFrame) -> pd.DataFrame:
        """Measure buying vs selling pressure"""
        pressure_df = pd.DataFrame(index=df.index)
        pressure_df['close_position'] = (df['Close'] - df['Low']) / (df['High'] - df['Low'] + 1e-8)
        pressure_df['bullish_pressure'] = ((df['Close'] - df['Open']) > 0).astype(int)
        pressure_df['bearish_pressure'] = ((df['Close'] - df['Open']) < 0).astype(int)
        return pressure_df


class VolumeIntelligenceFeatures:
    """Smart money volume patterns"""
    
    @staticmethod
    def volume_analysis(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """Analyze volume spikes and patterns"""
        vol_df = pd.DataFrame(index=df.index)
        vol_df['volume_ma'] = df['Volume'].rolling(period).mean()
        vol_df['volume_spike'] = df['Volume'] / (df['Volume'].rolling(period).mean() + 1e-8)
        vol_df['abnormal_volume'] = (vol_df['volume_spike'] > 1.5).astype(int)
        vol_df['volume_trend'] = df['Volume'].diff()
        vol_df['increasing_volume'] = (vol_df['volume_trend'] > 0).astype(int)
        return vol_df
    
    @staticmethod
    def volume_price_action(df: pd.DataFrame) -> pd.DataFrame:
        """Combine volume with price action"""
        vpa_df = pd.DataFrame(index=df.index)
        vpa_df['price_up_high_vol'] = ((df['Close'] > df['Open']) & (df['Volume'] > df['Volume'].rolling(20).mean())).astype(int)
        vpa_df['price_down_high_vol'] = ((df['Close'] < df['Open']) & (df['Volume'] > df['Volume'].rolling(20).mean())).astype(int)
        vpa_df['bullish_engulf_vol'] = ((df['Close'] > df['Open']) & (df['Volume'] > df['Volume'].rolling(10).mean())).astype(int)
        return vpa_df


class TimeFeatures:
    """Time-based features for market session analysis"""
    
    @staticmethod
    def time_of_day(df: pd.DataFrame) -> pd.DataFrame:
        """Extract time features from timestamp"""
        time_df = pd.DataFrame(index=df.index)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            time_df['hour'] = df['timestamp'].dt.hour
            time_df['minute'] = df['timestamp'].dt.minute
            time_df['day_of_week'] = df['timestamp'].dt.dayofweek
            time_df['is_opening_hour'] = (df['timestamp'].dt.hour == 9).astype(int)
            time_df['is_close_hour'] = (df['timestamp'].dt.hour == 16).astype(int)
            time_df['is_morning'] = (df['timestamp'].dt.hour < 12).astype(int)
            time_df['is_afternoon'] = (df['timestamp'].dt.hour >= 14).astype(int)
        return time_df


class RegimeDetectionFeatures:
    """Detect market regime and conditions"""
    
    @staticmethod
    def trend_regime(df: pd.DataFrame) -> pd.DataFrame:
        """Detect trending vs sideways market"""
        regime_df = pd.DataFrame(index=df.index)
        regime_df['trend_strength'] = abs(df['Close'].ewm(span=9).mean() - df['Close'].ewm(span=21).mean())
        regime_df['is_trending'] = (regime_df['trend_strength'] > regime_df['trend_strength'].rolling(20).mean()).astype(int)
        regime_df['is_sideways'] = (1 - regime_df['is_trending']).astype(int)
        return regime_df
    
    @staticmethod
    def volatility_regime(df: pd.DataFrame) -> pd.DataFrame:
        """Detect high vs low volatility periods"""
        vol_regime = pd.DataFrame(index=df.index)
        atr_val = (df['High'] - df['Low']).rolling(14).mean()
        volatility_val = df['Close'].pct_change().rolling(14).std()
        vol_regime['regime_atr'] = atr_val
        vol_regime['regime_volatility'] = volatility_val
        vol_regime['regime_high_volatility'] = (volatility_val > volatility_val.rolling(20).mean()).astype(int)
        vol_regime['regime_low_volatility'] = (1 - vol_regime['regime_high_volatility']).astype(int)
        return vol_regime


class FeatureEngineer:
    """Main class to generate all features"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.features = pd.DataFrame(index=df.index)
    
    def generate_all_features(self) -> pd.DataFrame:
        """Generate all categories of features"""
        
        # Candlestick patterns
        print("Generating candlestick pattern features...")
        self.features['hollow_white'] = CandlestickPatternFeatures.hollow_white_candle(self.df)
        self.features['filled_black'] = CandlestickPatternFeatures.filled_black_candle(self.df)
        self.features['spinning_top'] = CandlestickPatternFeatures.spinning_top(self.df)
        self.features['doji'] = CandlestickPatternFeatures.doji(self.df)
        self.features['hammer'] = CandlestickPatternFeatures.hammer(self.df)
        self.features['shooting_star'] = CandlestickPatternFeatures.shooting_star(self.df)

        engulfing = CandlestickPatternFeatures.engulfing_pattern(self.df)
        for name, feature in engulfing.items():
            self.features[name] = feature

        # Advanced candlestick patterns from trading strategies
        print("Generating advanced candlestick patterns...")
        try:
            from advanced_candlesticks import AdvancedCandlestickFeatures
            self.features['evening_star'] = AdvancedCandlestickFeatures.evening_star(self.df)
            self.features['morning_star'] = AdvancedCandlestickFeatures.morning_star(self.df)
            self.features['dark_cloud_cover'] = AdvancedCandlestickFeatures.dark_cloud_cover(self.df)
            self.features['piercing_line'] = AdvancedCandlestickFeatures.piercing_line(self.df)
            self.features['three_black_crows'] = AdvancedCandlestickFeatures.three_black_crows(self.df)
        except ImportError:
            print("Advanced candlestick features not available - install advanced_candlesticks.py")
        
        # Technical Indicators
        print("Generating indicator features...")
        self.features['rsi'] = IndicatorFeatures.rsi(self.df)

        macd_features = IndicatorFeatures.macd(self.df)
        for name, feature in macd_features.items():
            self.features[name] = feature

        bb_features = IndicatorFeatures.bollinger_bands(self.df)
        for name, feature in bb_features.items():
            self.features[name] = feature

        stoch_features = IndicatorFeatures.stochastic(self.df)
        for name, feature in stoch_features.items():
            self.features[name] = feature

        self.features['atr'] = IndicatorFeatures.atr(self.df)

        pivot_features = IndicatorFeatures.pivot_points(self.df)
        for name, feature in pivot_features.items():
            self.features[name] = feature

        # Market breadth indicators from trading strategies
        print("Generating market breadth indicators...")
        try:
            from market_breadth_indicators import MarketBreadthIndicators, TradingStrategyFeatures

            # Market breadth (if available)
            self.features['tick'] = MarketBreadthIndicators.tick_indicator(self.df)
            self.features['tiki'] = MarketBreadthIndicators.tiki_indicator(self.df)
            self.features['trin'] = MarketBreadthIndicators.trin_indicator(self.df)

            # Trading strategy features
            gap_features = TradingStrategyFeatures.opening_gap_features(self.df)
            self.features = self.features.join(gap_features)

            pivot_strategy_features = TradingStrategyFeatures.pivot_point_features(self.df)
            self.features = self.features.join(pivot_strategy_features)

            scalping_features = TradingStrategyFeatures.scalping_features(self.df)
            self.features = self.features.join(scalping_features)

        except ImportError:
            print("Market breadth features not available - install market_breadth_indicators.py")
        
        # Moving averages
        print("Generating moving average features...")
        self.features['ema_9'] = self.df['Close'].ewm(span=9).mean()
        self.features['ema_20'] = self.df['Close'].ewm(span=20).mean()
        self.features['sma_50'] = self.df['Close'].rolling(50).mean()
        
        # Time series features
        print("Generating time series features...")
        lag_df = TimeSeriesFeatures.lag_features(self.df)
        self.features = self.features.join(lag_df)
        
        returns_df = TimeSeriesFeatures.returns_features(self.df)
        self.features = self.features.join(returns_df)
        
        rolling_df = TimeSeriesFeatures.rolling_features(self.df)
        self.features = self.features.join(rolling_df)
        
        self.features['momentum'] = TimeSeriesFeatures.momentum_features(self.df)
        
        vol_df = TimeSeriesFeatures.volatility_features(self.df)
        self.features = self.features.join(vol_df)
        
        # Volume features
        print("Generating volume features...")
        # Note: volume_ma and volume_ratio will be generated in volume intelligence features
        
        # Market structure features (VERY IMPORTANT)
        print("Generating market structure features...")
        structure = MarketStructureFeatures.higher_high_lower_low(self.df)
        self.features = self.features.join(structure)
        
        breakout = MarketStructureFeatures.breakout_levels(self.df)
        self.features = self.features.join(breakout)
        
        # Price action features (RAW BEHAVIOR)
        print("Generating price action features...")
        anatomy = PriceActionFeatures.candle_anatomy(self.df)
        self.features = self.features.join(anatomy)
        
        pressure = PriceActionFeatures.price_pressure(self.df)
        self.features = self.features.join(pressure)
        
        # Volume intelligence features (SMART MONEY)
        print("Generating volume intelligence features...")
        vol_intel = VolumeIntelligenceFeatures.volume_analysis(self.df)
        self.features = self.features.join(vol_intel)
        
        vol_price = VolumeIntelligenceFeatures.volume_price_action(self.df)
        self.features = self.features.join(vol_price)
        
        # Time features (MARKET SESSION PATTERNS)
        print("Generating time features...")
        time_feat = TimeFeatures.time_of_day(self.df)
        if not time_feat.empty:
            self.features = self.features.join(time_feat)
        
        # Regime detection features (PRO LEVEL)
        print("Generating regime detection features...")
        trend_regime = RegimeDetectionFeatures.trend_regime(self.df)
        self.features = self.features.join(trend_regime)
        
        vol_regime = RegimeDetectionFeatures.volatility_regime(self.df)
        self.features = self.features.join(vol_regime)
        
        # Combined signals (important)
        print("Generating combined signals...")
        self._generate_combined_signals()
        
        return self.features
    
    def _generate_combined_signals(self):
        """Create combined trading signals"""
        # Strong buy signal: Multiple bullish indicators align
        rsi_buy = self.features['rsi'] < 30
        macd_buy = self.features['macd'] > self.features['macd_signal']
        bb_buy = self.df['Close'] < self.features['bb_lower']
        stoch_buy = self.features['stoch_k'] < 20
        
        self.features['strong_buy_signal'] = (
            (rsi_buy.astype(int) + macd_buy.astype(int) + 
             bb_buy.astype(int) + stoch_buy.astype(int)) >= 2
        ).astype(int)
        
        # Strong sell signal: Multiple bearish indicators align
        rsi_sell = self.features['rsi'] > 70
        macd_sell = self.features['macd'] < self.features['macd_signal']
        bb_sell = self.df['Close'] > self.features['bb_upper']
        stoch_sell = self.features['stoch_k'] > 80
        
        self.features['strong_sell_signal'] = (
            (rsi_sell.astype(int) + macd_sell.astype(int) + 
             bb_sell.astype(int) + stoch_sell.astype(int)) >= 2
        ).astype(int)
        
        # Trend signals
        self.features['uptrend'] = (self.features['ema_9'] > self.features['ema_20']).astype(int)
        self.features['downtrend'] = (self.features['ema_9'] < self.features['ema_20']).astype(int)
        
        # Volatility signal
        self.features['high_volatility'] = (self.features['atr'] > self.features['atr'].rolling(20).mean()).astype(int)
        
        # CONTEXT FEATURES (THIS IS GOLD) - Combining multiple signals
        print("Generating context features...")
        
        # Professional-grade buy signal: RSI + Trend + Volume alignment
        rsi_oversold = self.features['rsi'] < 30
        trend_up = self.features['uptrend'] == 1
        volume_spike = self.features.get('volume_spike', pd.Series(0, index=self.df.index)) > 1.5
        
        self.features['professional_buy_signal'] = (
            (rsi_oversold.astype(int) & trend_up.astype(int) & volume_spike.astype(int))
        ).astype(int)
        
        # Professional-grade sell signal: RSI + Trend + Volume alignment
        rsi_overbought = self.features['rsi'] > 70
        trend_down = self.features['downtrend'] == 1
        
        self.features['professional_sell_signal'] = (
            (rsi_overbought.astype(int) & trend_down.astype(int) & volume_spike.astype(int))
        ).astype(int)
        
        # Momentum confirmation: Price action + Trend alignment
        bullish_candle = self.features.get('body_abs', pd.Series(0, index=self.df.index)) > 0
        self.features['momentum_buy'] = (
            (bullish_candle.astype(int) & trend_up.astype(int)) >= 1
        ).astype(int)
        
        # Breakout confirmation: Price action + Volume + Trend
        breakout_up = self.features.get('breakout_up', pd.Series(0, index=self.df.index)) == 1
        self.features['confirmed_breakout_up'] = (
            (breakout_up.astype(int) & volume_spike.astype(int) & trend_up.astype(int))
        ).astype(int)
        
        breakout_down = self.features.get('breakout_down', pd.Series(0, index=self.df.index)) == 1
        self.features['confirmed_breakout_down'] = (
            (breakout_down.astype(int) & volume_spike.astype(int) & trend_down.astype(int))
        ).astype(int)
        
        # Support/Resistance interaction
        if 'support' in self.features.columns and 'resistance' in self.features.columns:
            self.features['price_at_support'] = (
                (self.df['Close'] <= self.features['support'] * 1.01) & 
                (self.df['Close'] >= self.features['support'] * 0.99)
            ).astype(int)
            
            self.features['price_at_resistance'] = (
                (self.df['Close'] >= self.features['resistance'] * 0.99) & 
                (self.df['Close'] <= self.features['resistance'] * 1.01)
            ).astype(int)
        
        # Regime-aware signals: Only trade when trending
        self.features['buy_in_uptrend'] = (
            (self.features['strong_buy_signal'] == 1) & (self.features.get('is_trending', pd.Series(0, index=self.df.index)) == 1)
        ).astype(int)
        
        self.features['sell_in_downtrend'] = (
            (self.features['strong_sell_signal'] == 1) & (self.features.get('is_trending', pd.Series(0, index=self.df.index)) == 1)
        ).astype(int)
        
        # Entry opportunity score: Combines all factors (0-5)
        self.features['entry_score'] = 0
        self.features['entry_score'] += (self.features['strong_buy_signal'] if 'strong_buy_signal' in self.features.columns else 0)
        self.features['entry_score'] += (self.features.get('bullish_pressure', pd.Series(0, index=self.df.index)))
        self.features['entry_score'] += (self.features.get('abnormal_volume', pd.Series(0, index=self.df.index)))
        self.features['entry_score'] += (self.features.get('is_trending', pd.Series(0, index=self.df.index)))
        self.features['entry_score'] += (self.features.get('increasing_volume', pd.Series(0, index=self.df.index)))

