#!/usr/bin/env python3
"""
🚀 ALPACA PAPER TRADING - Enhanced with Historical Data

Works with free Alpaca plan (limited real-time data)
Uses daily data + historical backtest data
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Import your validator and model
import sys
sys.path.insert(0, os.path.dirname(__file__))
from production_validator import ProductionValidator

class AlpacaPaperTrader:
    """Paper trading with Alpaca - enhanced version"""

    def __init__(self, api_key=None, secret_key=None, paper=True):
        """Initialize Alpaca connection"""
        self.api_key = api_key or os.getenv('APCA_API_KEY_ID')
        self.secret_key = secret_key or os.getenv('APCA_API_SECRET_KEY')

        if not self.api_key or not self.secret_key:
            print("ERROR: Alpaca API keys not found!")
            return

        self.trading_client = TradingClient(self.api_key, self.secret_key, paper=paper)
        print("[OK] Alpaca paper trading connected")

        # Get account info
        try:
            account = self.trading_client.get_account()
            print(f"Account: ${float(account.cash):,.2f} cash")
            print(f"Portfolio: ${float(account.portfolio_value):,.2f}")
        except Exception as e:
            print(f"[WARN] Could not get account info: {e}")

    def load_historical_data(self, symbol='AAPL', days=100):
        """Load historical data from CSV if available"""
        try:
            # Try to load from your data directory
            data_path = Path(__file__).parent.parent / 'data' / 'raw' / f'{symbol}_10min_generated_data.csv'
            
            if data_path.exists():
                df = pd.read_csv(data_path)
                print(f"[OK] Loaded {len(df)} rows from {data_path.name}")
                
                # Rename columns
                if 'open' in df.columns:
                    df = df.rename(columns={
                        'open': 'Open', 'high': 'High', 'low': 'Low',
                        'close': 'Close', 'volume': 'Volume'
                    })
                
                df['returns'] = df['Close'].pct_change()
                return df.tail(200)  # Last 200 bars
            
        except Exception as e:
            print(f"[WARN] Could not load historical data: {e}")
        
        # Fallback: generate synthetic data
        print("[WARN] Generating synthetic OHLCV data (no live subscription)")
        np.random.seed(42)
        dates = pd.date_range(datetime.now() - timedelta(days=days), 
                             datetime.now(), freq='1D')
        
        prices = 150 + np.cumsum(np.random.randn(len(dates)) * 2)
        df = pd.DataFrame({
            'Open': prices + np.random.randn(len(dates)),
            'High': prices + abs(np.random.randn(len(dates)) * 2),
            'Low': prices - abs(np.random.randn(len(dates)) * 2),
            'Close': prices,
            'Volume': np.random.randint(1000000, 5000000, len(dates)),
        }, index=dates)
        
        df['returns'] = df['Close'].pct_change()
        df['symbol'] = symbol
        return df

    def place_order(self, symbol, qty, side):
        """Place a trade order"""
        try:
            order_side = OrderSide.BUY if side.upper() == 'BUY' else OrderSide.SELL
            
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=TimeInForce.DAY
            )
            
            order = self.trading_client.submit_order(order_request)
            print(f"[OK] Order: {side} {qty} {symbol} (ID: {order.id})")
            return order
            
        except Exception as e:
            print(f"[ERROR] Order failed: {e}")
            return None

    def check_positions(self):
        """Check current positions"""
        try:
            positions = self.trading_client.get_all_positions()
            if positions:
                print("\n[POSITIONS]")
                for pos in positions:
                    pnl = float(pos.unrealized_pl) if pos.unrealized_pl else 0
                    print(f"  {pos.symbol}: {pos.qty} @ ${float(pos.avg_entry_price):.2f} (P&L: ${pnl:.2f})")
            else:
                print("[POSITIONS] None")
        except Exception as e:
            print(f"[WARN] Could not check positions: {e}")

    def run_paper_trading(self, symbol='AAPL'):
        """Complete paper trading cycle"""
        print(f"\n{'='*60}")
        print(f"PAPER TRADING CYCLE - {symbol}")
        print(f"{'='*60}\n")

        # Step 1: Load data
        print("[STEP 1] Loading market data")
        df = self.load_historical_data(symbol)
        
        if df is None or df.empty:
            print("[ERROR] No data available")
            return
        
        print(f"[OK] Got {len(df)} bars of data\n")

        # Step 2: Run validation
        print("[STEP 2] Running production validation")
        validator = ProductionValidator(df)
        results = validator.run_all_gates()
        
        decision = results['decision']
        confidence = results['confidence']
        print(f"[DECISION] {decision}")
        print(f"[CONFIDENCE] {confidence:.0%}\n")

        # Step 3: Generate signals
        print("[STEP 3] Generating trading signals")
        
        if 'SAFE' in decision or 'READY' in decision:
            # Simple momentum signal
            latest_return = df['returns'].iloc[-1] if not df['returns'].isna().all() else 0
            signal = 1 if latest_return > 0 else 0
            
            print(f"Latest return: {latest_return:.4f}")
            print(f"Signal: {'BUY' if signal == 1 else 'SELL'}\n")

            # Step 4: Execute trade
            print("[STEP 4] Executing paper trade")
            if signal == 1:
                self.place_order(symbol, 1, 'BUY')
            else:
                try:
                    positions = self.trading_client.get_all_positions()
                    for pos in positions:
                        if pos.symbol == symbol:
                            self.place_order(symbol, int(float(pos.qty)), 'SELL')
                except:
                    pass
        else:
            print("[OK] Validation failed - no trades executed\n")

        # Step 5: Check positions
        print("[STEP 5] Checking positions")
        self.check_positions()

        print(f"\n{'='*60}")
        print("PAPER TRADING CYCLE COMPLETE")
        print(f"{'='*60}\n")

def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("ALPACA PAPER TRADING INTEGRATION")
    print("="*60 + "\n")

    trader = AlpacaPaperTrader(paper=True)

    if not trader.api_key:
        print("ERROR: Set Alpaca API keys")
        print("$env:APCA_API_KEY_ID = 'your_key'")
        print("$env:APCA_API_SECRET_KEY = 'your_secret'")
        return

    # Run paper trading
    trader.run_paper_trading(symbol='AAPL')

if __name__ == "__main__":
    main()
