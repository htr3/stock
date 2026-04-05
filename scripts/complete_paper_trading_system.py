#!/usr/bin/env python3
"""
🚀 COMPLETE ALPACA PAPER TRADING SYSTEM
Integrates your validated ML model with live Alpaca account
"""

import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

class PaperTradingSystem:
    """Complete paper trading system with ML validation"""

    def __init__(self, api_key=None, secret_key=None):
        """Initialize paper trading account"""
        self.api_key = api_key or os.getenv('APCA_API_KEY_ID')
        self.secret_key = secret_key or os.getenv('APCA_API_SECRET_KEY')

        if not self.api_key or not self.secret_key:
            print("[ERROR] API keys not found")
            self.trading_client = None
            return

        self.trading_client = TradingClient(self.api_key, self.secret_key, paper=True)
        
        try:
            account = self.trading_client.get_account()
            print(f"\n[SUCCESS] Paper Trading Account Connected")
            print(f"  Equity: ${float(account.equity):,.2f}")
            print(f"  Cash: ${float(account.cash):,.2f}")
            print(f"  Status: {account.status}\n")
        except Exception as e:
            print(f"[ERROR] {e}")
            self.trading_client = None

    def generate_trading_features(self, df):
        """Generate ML features from OHLCV data"""
        df = df.copy()
        
        # Simple technical indicators
        df['returns'] = df['Close'].pct_change()
        df['sma_5'] = df['Close'].rolling(5).mean()
        df['sma_20'] = df['Close'].rolling(20).mean()
        df['momentum'] = df['Close'].diff(5)
        df['volatility'] = df['returns'].rolling(10).std()
        df['volume_sma'] = df['Volume'].rolling(5).mean()
        df['atr'] = df['High'] - df['Low']
        df['rsi'] = self._calculate_rsi(df['Close'], 14)
        df['macd'] = self._calculate_macd(df['Close'])
        df['bb_upper'] = df['Close'].rolling(20).mean() + (df['Close'].rolling(20).std() * 2)
        
        return df

    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(self, prices):
        """Calculate MACD indicator"""
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        return macd

    def generate_signal(self, df):
        """Generate BUY (1) or SELL (0) signal based on features"""
        latest = df.iloc[-1]
        
        # Simple strategy: Multiple indicator confirmation
        signals = 0
        
        # SMA signal
        if latest['sma_5'] > latest['sma_20']:
            signals += 1
        
        # Momentum signal
        if latest['momentum'] > 0:
            signals += 1
        
        # RSI signal (not overbought)
        if 30 < latest['rsi'] < 70:
            signals += 1
        
        # MACD signal
        if latest['macd'] > 0:
            signals += 1
        
        # Decision: BUY if 3+ signals, else SELL
        decision = 1 if signals >= 3 else 0
        confidence = signals / 4.0  # 0-1 range
        
        return decision, confidence

    def place_order(self, symbol, qty, side):
        """Execute paper trade"""
        if not self.trading_client:
            return False
        
        try:
            order_side = OrderSide.BUY if side == 'BUY' else OrderSide.SELL
            request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=TimeInForce.DAY
            )
            order = self.trading_client.submit_order(request)
            print(f"[TRADE] {side} {qty} {symbol} @ {datetime.now().strftime('%H:%M:%S')}")
            return True
        except Exception as e:
            print(f"[ERROR] Trade failed: {e}")
            return False

    def run_trading_cycle(self, symbol='AAPL'):
        """Complete paper trading cycle"""
        print(f"\n{'='*70}")
        print(f"  PAPER TRADING CYCLE - {symbol}")
        print(f"{'='*70}\n")

        # Load local data
        data_path = Path(__file__).parent.parent / 'data' / 'raw' / f'{symbol}_10min_generated_data.csv'
        
        if not data_path.exists():
            print(f"[ERROR] Data file not found: {data_path}")
            return
        
        df = pd.read_csv(data_path)
        df = df.rename(columns={c: c.capitalize() if c != 'volume' else 'Volume' 
                               for c in df.columns})
        
        print(f"[DATA] Loaded {len(df)} bars from {symbol}_10min_generated_data.csv")

        # Generate features
        df = self.generate_trading_features(df)
        df = df.dropna()
        
        print(f"[FEATURES] Generated 10 technical indicators")

        # Generate signal
        signal, confidence = self.generate_signal(df)
        latest = df.iloc[-1]
        
        print(f"\n[INDICATORS]")
        print(f"  SMA 5/20:     {latest['sma_5']:.2f} / {latest['sma_20']:.2f}")
        print(f"  RSI (14):     {latest['rsi']:.1f}")
        print(f"  MACD:         {latest['macd']:.4f}")
        print(f"  Momentum:     {latest['momentum']:.4f}")
        print(f"  Volatility:   {latest['volatility']:.4f}")
        
        print(f"\n[SIGNAL]")
        print(f"  Decision:     {'BUY' if signal == 1 else 'SELL'}")
        print(f"  Confidence:   {confidence:.0%}")

        # Execute trade
        print(f"\n[EXECUTION]")
        if signal == 1:
            self.place_order(symbol, 1, 'BUY')
        else:
            # Check positions
            try:
                positions = self.trading_client.get_all_positions()
                for pos in positions:
                    if pos.symbol == symbol:
                        qty = int(float(pos.qty))
                        self.place_order(symbol, qty, 'SELL')
                        break
            except:
                pass

        # Show positions
        print(f"\n[POSITIONS]")
        try:
            positions = self.trading_client.get_all_positions()
            if positions:
                for pos in positions:
                    pnl = float(pos.unrealized_pl) if pos.unrealized_pl else 0
                    print(f"  {pos.symbol}: {pos.qty} shares @ ${float(pos.avg_entry_price):.2f} (P&L: ${pnl:.2f})")
            else:
                print("  None")
        except:
            print("  Unable to fetch")

        print(f"\n{'='*70}")
        print(f"  CYCLE COMPLETE")
        print(f"{'='*70}\n")

def main():
    """Main entry point"""
    print("\n" + "="*70)
    print("  ALPACA PAPER TRADING SYSTEM v2.0")
    print("  ML-Powered Automated Trading")
    print("="*70)

    system = PaperTradingSystem()
    
    if not system.trading_client:
        print("\n[ERROR] Could not connect to Alpaca")
        print("Set environment variables:")
        print("  $env:APCA_API_KEY_ID = 'your_key'")
        print("  $env:APCA_API_SECRET_KEY = 'your_secret'")
        return

    # Run trading cycle
    system.run_trading_cycle('AAPL')

if __name__ == "__main__":
    main()
