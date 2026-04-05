#!/usr/bin/env python3
"""
🚀 ALPACA PAPER TRADING INTEGRATION

Connect your validated ML trading system to Alpaca paper trading.

Requirements:
- Alpaca account (free)
- API keys from Alpaca dashboard
- Your trained model and features

Usage:
1. Get API keys from https://alpaca.markets/
2. Set environment variables or edit this file
3. Run: python alpaca_paper_trading.py
"""

import os
import sys
import argparse
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

# Alpaca imports
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# Import your validator and model
from production_validator import ProductionValidator

class AlpacaPaperTrader:
    """Paper trading integration with Alpaca"""

    def __init__(self, api_key=None, secret_key=None, paper=True):
        """Initialize Alpaca connection"""
        self.api_key = api_key or os.getenv('APCA_API_KEY_ID')
        self.secret_key = secret_key or os.getenv('APCA_API_SECRET_KEY')

        if not self.api_key or not self.secret_key:
            print("❌ ERROR: Alpaca API keys not found!")
            print("Get keys from: https://alpaca.markets/")
            print("Set environment variables:")
            print("  APCA_API_KEY_ID=PKT7E4MZS3DZPMJTOOJCS5HBQB")
            print("  APCA_API_SECRET_KEY=591RCNtqAuoQ3XqVZnqGbpifCDTpBy1u4K14M8i1jwUr")
            return

        # Initialize clients
        self.trading_client = TradingClient(self.api_key, self.secret_key, paper=paper)
        self.data_client = StockHistoricalDataClient(self.api_key, self.secret_key)

        print("✅ Alpaca paper trading connected")

        # Get account info
        try:
            account = self.trading_client.get_account()
            print(f"Account: ${float(account.cash):.2f} cash available")
            print(f"Portfolio Value: ${float(account.portfolio_value):.2f}")
        except Exception as e:
            print(f"⚠️  Could not get account info: {e}")

    def get_live_data(self, symbol, minutes=100):
        """Get recent market data"""
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Minute,
                start=datetime.now() - timedelta(minutes=minutes),
                end=datetime.now()
            )

            bars = self.data_client.get_stock_bars(request)
            df = bars.df

            if df.empty:
                print(f"⚠️  No data received for {symbol}")
                return None

            # Rename columns to match your system
            df = df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })

            df['returns'] = df['Close'].pct_change()
            df['symbol'] = symbol

            print(f"📊 Got {len(df)} minutes of {symbol} data")
            return df

        except Exception as e:
            print(f"❌ Error getting data: {e}")
            return None

    def check_positions(self):
        """Check current positions"""
        try:
            positions = self.trading_client.get_all_positions()
            if positions:
                print("\n📊 Current Positions:")
                for pos in positions:
                    print(f"  {pos.symbol}: {pos.qty} shares @ ${float(pos.avg_entry_price):.2f}")
            else:
                print("📊 No open positions")
        except Exception as e:
            print(f"⚠️  Could not check positions: {e}")

    def place_order(self, symbol, qty, side, order_type='market'):
        """Place a trade order"""
        try:
            if side.upper() == 'BUY':
                order_side = OrderSide.BUY
            elif side.upper() == 'SELL':
                order_side = OrderSide.SELL
            else:
                print(f"❌ Invalid side: {side}")
                return None

            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=TimeInForce.DAY
            )

            order = self.trading_client.submit_order(order_request)
            print(f"✅ Order placed: {side} {qty} {symbol} (ID: {order.id})")
            return order

        except Exception as e:
            print(f"❌ Order failed: {e}")
            return None

    def run_paper_trading_cycle(self, symbol='AAPL', model_path=None):
        """Complete paper trading cycle"""
        print(f"\n🚀 PAPER TRADING CYCLE - {symbol}")
        print("="*50)

        # Step 1: Get live data
        print("\n📥 Step 1: Getting live market data")
        live_df = self.get_live_data(symbol)

        if live_df is None or live_df.empty:
            print("❌ No live data - skipping cycle")
            return

        # Step 2: Load your model and validator
        print("\n🤖 Step 2: Loading validated model")
        try:
            import joblib
            model = joblib.load(model_path) if model_path else None
            if model:
                print("✅ Model loaded")
            else:
                print("⚠️  No model - using dummy signals")
                model = None
        except:
            print("⚠️  Model load failed - using dummy signals")
            model = None

        # Step 3: Run validation
        print("\n🔍 Step 3: Running production validation")
        validator = ProductionValidator(live_df, model=model)
        validation_results = validator.run_all_gates()

        print(f"Decision: {validation_results['decision']}")
        print(f"Confidence: {validation_results['confidence']:.1%}")

        # Step 4: Generate signals
        print("\n📈 Step 4: Generating trading signals")

        if validation_results['decision'] in ['SAFE FOR PAPER TRADING', 'READY FOR LIVE TRADING']:
            # Generate signal (simplified - you'd use your full feature pipeline)
            latest_return = live_df['returns'].iloc[-1]
            signal = 1 if latest_return > 0 else 0  # Simple momentum signal

            print(f"Latest return: {latest_return:.4f}")
            print(f"Signal: {'BUY' if signal == 1 else 'SELL'}")

            # Step 5: Execute trade (paper money)
            if signal == 1:
                print("\n💰 Step 5: Executing BUY order")
                self.place_order(symbol, 10, 'BUY')  # Buy 10 shares
            else:
                # Check if we have position to sell
                try:
                    positions = self.trading_client.get_all_positions()
                    symbol_positions = [p for p in positions if p.symbol == symbol]
                    if symbol_positions:
                        qty = int(float(symbol_positions[0].qty))
                        if qty > 0:
                            print("\n💰 Step 5: Executing SELL order")
                            self.place_order(symbol, qty, 'SELL')
                        else:
                            print("📊 No position to sell")
                    else:
                        print("📊 No position to sell")
                except:
                    print("📊 Could not check positions")

        else:
            print("⏸️  Validation failed - no trades executed")

        # Step 6: Check final positions
        print("\n📊 Step 6: Final positions")
        self.check_positions()

        print("\n✅ Paper trading cycle complete")

def main():
    """Main paper trading demo"""
    parser = argparse.ArgumentParser(description='Alpaca paper trading runner')
    parser.add_argument('--symbol', type=str, default=os.getenv('TRADING_SYMBOL', 'AAPL'),
                        help='Symbol to trade, e.g. AAPL or BTCUSD')
    parser.add_argument('--model_path', type=str, default='models/trained_model.pkl',
                        help='Path to trained model file')
    args = parser.parse_args()

    print("🚀 ALPACA PAPER TRADING INTEGRATION")
    print("="*50)
    print(f"Symbol: {args.symbol}")
    print(f"Model: {args.model_path}")

    # Initialize trader (uses environment variables)
    trader = AlpacaPaperTrader(paper=True)

    if not trader.api_key:
        print("\n⚠️  SETUP REQUIRED:")
        print("1. Go to https://alpaca.markets/")
        print("2. Create free account")
        print("3. Get API keys from dashboard")
        print("4. Set environment variables or edit this file")
        print("5. Run again")
        return

    # Run a paper trading cycle
    trader.run_paper_trading_cycle(
        symbol=args.symbol,
        model_path=args.model_path
    )

    print("\n" + "="*50)
    print("🎯 PAPER TRADING SETUP COMPLETE")
    print("="*50)

if __name__ == "__main__":
    main()