#!/usr/bin/env python3
"""
🚀 CONTINUOUS PAPER TRADING SYSTEM
Runs 24/7 trading cycles with logging and P&L tracking
"""

import sys
import os
import time
import json
import argparse
import joblib
from datetime import datetime
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# ML Integration
sys.path.insert(0, str(Path(__file__).parent))
from live_data_fetcher import LiveDataFetcher
from production_trading_engine import ProductionTradingEngine

class ContinuousTradingSystem:
    """Continuous paper trading with logging"""

    def __init__(self, dry_run=True, api_key=None, secret_key=None, run_interval=300):
        """
        Initialize system
        run_interval: seconds between trading cycles (default 5 min)
        """
        self.api_key = api_key or os.getenv('APCA_API_KEY_ID')
        self.secret_key = secret_key or os.getenv('APCA_API_SECRET_KEY')
        self.run_interval = run_interval
        self.trade_log = []
        self.cycle_count = 0
        
        # Create logs directory
        self.log_dir = Path(__file__).parent.parent / 'logs'
        self.log_dir.mkdir(exist_ok=True)
        
        # Log files
        self.log_file = self.log_dir / f'trading_log_{datetime.now().strftime("%Y%m%d")}.json'
        self.prediction_file = self.log_dir / 'latest_prediction.json'

        # Production Trading Engine (replaces static logic)
        print("[🤖] Initializing ProductionTradingEngine...")
        self.dry_run = dry_run
        self.engine = ProductionTradingEngine(dry_run=self.dry_run)
        
        if self.engine.model is None:
            print("⚠️  No trained model found - skipping ML predictions")
        
        if not self.api_key or not self.secret_key:
            print("[ERROR] API keys not found")
            self.trading_client = None
        else:
            self.trading_client = TradingClient(self.api_key, self.secret_key, paper=True)
        
        try:
            account = self.trading_client.get_account()
            print(f"\n[SUCCESS] Connected to Alpaca Paper Trading")
            print(f"  Equity: ${float(account.equity):,.2f}")
            print(f"  Cash: ${float(account.cash):,.2f}")
            print(f"  Run Interval: {run_interval}s ({run_interval/60:.1f} min)")
            print(f"  Log File: {self.log_file}\n")
        except Exception as e:
            print(f"[ERROR] {e}")
            self.trading_client = None





    def run_trading_cycle(self, symbol='AAPL'):
        """Execute one trading cycle - DYNAMIC ML PIPELINE"""
        self.cycle_count += 1
        
        print(f"[{self.cycle_count:04d}] {datetime.now().strftime('%H:%M:%S')} | Running ML cycle for {symbol}...")
        
        if self.engine.model is None:
            print(f"  ⚠️  No ML model - skipping {symbol}")
            return
        
        try:
            # Run full production cycle for this symbol
            self.engine.run_production_cycle([symbol])
            
            # Enhanced logging from engine
            print(f"  📊 Engine cycles: {self.engine.cycles}, Model: {self.engine.model is not None}")
                
        except Exception as e:
            print(f"  ❌ Error in {symbol}: {e}")

    def save_log(self):
        """Save trading log"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.trade_log, f, indent=2)
        except:
            pass

    def save_prediction(self, prediction):
        """Save latest prediction to disk"""
        try:
            with open(self.prediction_file, 'w') as f:
                json.dump(prediction, f, indent=2)
        except:
            pass

    def run_continuous(self, symbols=['AAPL'], duration=None):
        """
        Run trading cycles continuously
        symbols: list of stocks to trade
        duration: run for N hours (None = infinite)
        """
        start_time = datetime.now()
        
        print("\n" + "="*80)
        print("  CONTINUOUS PAPER TRADING SYSTEM - STARTED")
        print("="*80)
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Interval: {self.run_interval}s ({self.run_interval/60:.1f} min)")
        if duration:
            print(f"Duration: {duration} hours")
        print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        print("\nPress Ctrl+C to stop\n")

        try:
            while True:
                # Check duration
                if duration:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > duration * 3600:
                        print(f"\n[INFO] Duration limit reached ({duration}h)")
                        break
                
                # Run trading cycle for each symbol
                for symbol in symbols:
                    try:
                        self.run_trading_cycle(symbol)
                    except Exception as e:
                        print(f"[ERROR] {symbol}: {e}")
                
                # Wait for next cycle
                print(f"\n[NEXT] Waiting {self.run_interval}s until next cycle...\n")
                time.sleep(self.run_interval)

        except KeyboardInterrupt:
            print("\n\n[STOPPED] User terminated")
            
        finally:
            # Save log and show summary
            self.save_log()
            self.show_summary()

    def show_summary(self):
        """Show trading summary"""
        print("\n" + "="*80)
        print("  TRADING SUMMARY")
        print("="*80)
        print(f"Total Cycles: {self.cycle_count}")
        print(f"Total Trades: {len(self.trade_log)}")
        print(f"Trades Placed: {len([t for t in self.trade_log if t['status'] == 'PLACED'])}")
        
        try:
            account = self.trading_client.get_account()
            equity = float(account.equity)
            pnl = equity - 100000
            print(f"Final Equity: ${equity:,.2f}")
            print(f"P&L: ${pnl:+,.2f}")
        except:
            pass
        
        print(f"Log File: {self.log_file}")
        print("="*80 + "\n")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Continuous paper trading runner')
    parser.add_argument('--symbols', type=str, default=None,
                        help='Comma-separated symbols to trade, e.g. AAPL,MSFT,GOOGL')
    parser.add_argument('--interval', type=int, default=int(os.getenv('TRADING_INTERVAL', '10')),
                        help='Seconds between trading cycles')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Dry run mode')
    parser.add_argument('--duration', type=float, default=None,
                        help='Duration in hours to run (default infinite)')
    parser.add_argument('--config', action='store_true',
                        help='Load symbols from config/trading_symbols.json')

    args = parser.parse_args()
    
    # Determine symbols to trade
    symbols = ['AAPL']
    config_path = Path(__file__).parent.parent / 'config' / 'trading_symbols.json'
    if args.symbols:
        symbols = [sym.strip().upper() for sym in args.symbols.split(',') if sym.strip()]
        print(f"[OK] Trading symbols from CLI: {', '.join(symbols)}")
    elif args.config and config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

            enabled_symbols = []
            if config.get('stocks', {}).get('enabled'):
                enabled_symbols.extend(config['stocks']['symbols'])
            if config.get('etfs', {}).get('enabled'):
                enabled_symbols.extend(config['etfs']['symbols'])
            if config.get('options', {}).get('enabled'):
                enabled_symbols.extend(config['options']['symbols'])
            if config.get('crypto', {}).get('enabled'):
                enabled_symbols.extend(config['crypto']['symbols'])

            if enabled_symbols:
                symbols = enabled_symbols
                print(f"[OK] Loaded {len(symbols)} symbols from config")
                print(f"     Trading: {', '.join(symbols)}\n")
        except Exception as e:
            print(f"[WARN] Could not load config: {e}")

    print("\n" + "="*80)
    print("  CONTINUOUS PAPER TRADING SYSTEM")
    print("="*80 + "\n")

    system = ContinuousTradingSystem(
        dry_run=args.dry_run,
        run_interval=args.interval
    )
    
    if not system.trading_client:
        print("[ERROR] Could not connect to Alpaca")
        return

    # Run continuous trading
    system.run_continuous(
        symbols=symbols,
        duration=args.duration
    )

if __name__ == "__main__":
    main()
