"""
Regime Detector

Identifies market regime: TRENDING vs SIDEWAYS
Uses: ADX, Volatility, Volume

Only trade when market is trending:
- High ADX (strong trend)
- Rising volatility
- High volume
Otherwise: SKIP TRADES (wait for better conditions)
"""

import pandas as pd
import numpy as np


class RegimeDetector:
    """Detect market regime: TRENDING or SIDEWAYS"""
    
    def __init__(self, df, adx_threshold=25, volatility_period=14):
        """
        Args:
            df: OHLCV dataframe
            adx_threshold: ADX > threshold = TRENDING
            volatility_period: Period for volatility calculation
        """
        self.df = df.copy()
        self.adx_threshold = adx_threshold
        self.volatility_period = volatility_period
        self.regimes = None
    
    def calculate_adx(self, period=14):
        """Calculate ADX (Average Directional Index)"""
        df = self.df.copy()
        
        # True Range
        df['hl'] = df['High'] - df['Low']
        df['hc'] = abs(df['High'] - df['Close'].shift(1))
        df['lc'] = abs(df['Low'] - df['Close'].shift(1))
        df['tr'] = df[['hl', 'hc', 'lc']].max(axis=1)
        
        # Directional Movements
        df['pos_dm'] = 0.0
        df['neg_dm'] = 0.0
        
        for i in range(1, len(df)):
            up = df['High'].iloc[i] - df['High'].iloc[i-1]
            down = df['Low'].iloc[i-1] - df['Low'].iloc[i]
            
            if up > 0 and up > down:
                df['pos_dm'].iloc[i] = up
            if down > 0 and down > up:
                df['neg_dm'].iloc[i] = down
        
        # Smoothed TR and DM
        atr = df['tr'].rolling(period).mean()
        pos_di = 100 * (df['pos_dm'].rolling(period).mean() / atr)
        neg_di = 100 * (df['neg_dm'].rolling(period).mean() / atr)
        
        # DX and ADX
        dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di)
        adx = dx.rolling(period).mean()
        
        return adx, pos_di, neg_di
    
    def calculate_volatility(self):
        """Calculate rolling volatility (ATR based)"""
        df = self.df.copy()
        
        # True Range
        df['hl'] = df['High'] - df['Low']
        df['hc'] = abs(df['High'] - df['Close'].shift(1))
        df['lc'] = abs(df['Low'] - df['Close'].shift(1))
        df['tr'] = df[['hl', 'hc', 'lc']].max(axis=1)
        
        # ATR (Average True Range)
        atr = df['tr'].rolling(self.volatility_period).mean()
        
        return atr
    
    def calculate_volume_trend(self, period=14):
        """Calculate volume strength"""
        df = self.df.copy()
        
        # Volume moving average
        vol_ma = df['Volume'].rolling(period).mean()
        
        # Current volume vs MA
        vol_ratio = df['Volume'] / vol_ma
        
        return vol_ratio
    
    def detect_regime(self):
        """Detect TRENDING vs SIDEWAYS regime"""
        df = self.df.copy()
        
        # Calculate indicators
        adx, +di, -di = self.calculate_adx()
        volatility = self.calculate_volatility()
        vol_ratio = self.calculate_volume_trend()
        
        # Regime logic
        regime = []
        
        for i in range(len(df)):
            adx_val = adx.iloc[i] if i < len(adx) else np.nan
            vol_val = volatility.iloc[i] if i < len(volatility) else np.nan
            vol_r = vol_ratio.iloc[i] if i < len(vol_ratio) else np.nan
            
            if pd.isna(adx_val):
                regime.append('UNKNOWN')
            elif adx_val > self.adx_threshold and vol_r > 0.8:
                regime.append('TRENDING')
            else:
                regime.append('SIDEWAYS')
        
        df['regime'] = regime
        df['adx'] = adx
        df['atr'] = volatility
        df['vol_ratio'] = vol_ratio
        
        self.regimes = df
        
        return df
    
    def get_regime_stats(self):
        """Summary of regime distribution"""
        if self.regimes is None:
            self.detect_regime()
        
        print("\n" + "="*70)
        print("REGIME ANALYSIS")
        print("="*70 + "\n")
        
        regime_counts = self.regimes['regime'].value_counts()
        total = len(self.regimes)
        
        for regime, count in regime_counts.items():
            pct = count / total * 100
            print(f"{regime:15s}: {count:5d} candles ({pct:5.1f}%)")
        
        print("\n" + "="*70)
        print("TRADING IMPLICATION")
        print("="*70 + "\n")
        
        trending_pct = regime_counts.get('TRENDING', 0) / total * 100
        
        if trending_pct > 60:
            print(f"✅ Market is mostly TRENDING ({trending_pct:.1f}%)")
            print("   Good conditions for trend-following model")
        elif trending_pct > 40:
            print(f"⚠️  Mixed conditions ({trending_pct:.1f}% trending)")
            print("   Model should use regime filter")
        else:
            print(f"❌ Market is mostly SIDEWAYS ({trending_pct:.1f}% trending)")
            print("   Trend-following model will struggle")
        
        print("="*70 + "\n")
        
        return regime_counts
    
    def apply_regime_filter(self, predictions, probabilities):
        """
        Apply regime filter to predictions
        
        Only take trades when TRENDING
        Skip trades when SIDEWAYS
        """
        if self.regimes is None:
            self.detect_regime()
        
        filtered_predictions = predictions.copy()
        filtered_probabilities = probabilities.copy()
        
        for i in range(len(self.regimes)):
            if i >= len(filtered_predictions):
                break
            
            if self.regimes['regime'].iloc[i] == 'SIDEWAYS':
                # Mark as "no trade" by setting confidence to 0.5
                filtered_probabilities[i] = 0.5
        
        return filtered_predictions, filtered_probabilities
    
    def backtest_with_regime_filter(self, predictions, probabilities, returns, 
                                   position_size=0.02, threshold=0.65):
        """Backtest with regime filter applied"""
        filtered_preds, filtered_probs = self.apply_regime_filter(
            predictions, probabilities
        )
        
        equity = 10000
        winning_trades = 0
        total_trades = 0
        skipped_trades = 0
        
        for i in range(len(predictions)):
            confidence = filtered_probs[i]
            
            if confidence <= threshold:
                skipped_trades += 1
                continue
            
            if filtered_preds[i] == 1:
                trade_return = returns.iloc[i]
            else:
                trade_return = -returns.iloc[i]
            
            equity *= (1 + trade_return * position_size)
            total_trades += 1
            
            if trade_return > 0:
                winning_trades += 1
        
        total_return = (equity - 10000) / 10000
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        print("\n" + "="*70)
        print("BACKTEST WITH REGIME FILTER")
        print("="*70 + "\n")
        
        print(f"Candlestick counts:")
        print(f"  Total:           {len(predictions)}")
        print(f"  Skipped (Sideways): {skipped_trades}")
        print(f"  Traded (Trending):  {total_trades}\n")
        
        print(f"Performance:")
        print(f"  Final Balance:   ${equity:,.2f}")
        print(f"  Return:          {total_return*100:.2f}%")
        print(f"  Win Rate:        {win_rate*100:.2f}%")
        
        print("="*70 + "\n")
        
        return {
            'final_balance': equity,
            'total_return': total_return,
            'total_trades': total_trades,
            'skipped_trades': skipped_trades,
            'win_rate': win_rate
        }
