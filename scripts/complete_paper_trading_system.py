#!/usr/bin/env python3
"""
🚀 COMPLETE ML PAPER TRADING SYSTEM v2.0 - Production Engine Integration
Integrates validated ML model with live Alpaca via ProductionTradingEngine
"""

import sys
import os
import argparse
import json
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Local imports
sys.path.insert(0, str(Path(__file__).parent))
from production_trading_engine import ProductionTradingEngine

class CompletePaperTradingSystem:
    "Complete paper trading using production ML engine"
    
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        print("\n🤖 COMPLETE ML PAPER TRADING SYSTEM v2.0")
        print(f"🔄 Dry run: {self.dry_run}")
        print("📡 Powered by ProductionTradingEngine (Live Data + XGBoost + Gates)\n")
        
        # Initialize production engine (handles all ML/live/gates/trades)
        self.engine = ProductionTradingEngine(dry_run=self.dry_run)
        
        if self.engine.model is None:
            print("⚠️ No trained model - run model_training.py first")
    
    def load_symbols(self, symbols_arg=None):
        "Load trading symbols from CLI or config"
        symbols = ["AAPL"]
        
        if symbols_arg:
            symbols = [s.strip().upper() for s in symbols_arg.split(",") if s.strip()]
            print(f"[SYMBOLS] CLI: {', '.join(symbols)}")
            return symbols
        
        # Try config
        config_path = Path(__file__).parent.parent / "config" / "trading_symbols.json"
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                all_symbols = []
                for section in ["stocks", "etfs", "options", "crypto"]:
                    if config.get(section, {}).get("enabled"):
                        all_symbols.extend(config[section]["symbols"])
                if all_symbols:
                    symbols = all_symbols[:5]  # Top 5
                    print(f"[SYMBOLS] Config: {', '.join(symbols)}")
                    return symbols
            except Exception as e:
                print(f"[WARN] Config load error: {e}")
        
        print(f"[SYMBOLS] Default: AAPL")
        return symbols
    
    def run_trading_cycle(self, symbols):
        "Single trading cycle - full engine delegation"
        print(f"\n🔄 TRADING CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        print(f"📈 Symbols: {', '.join(symbols)}")
        
        # Delegate complete cycle to engine
        self.engine.run_production_cycle(symbols)
        
        print(f"\n✅ CYCLE COMPLETE | Engine cycles: {self.engine.cycles}")
    
    def run_continuous(self, symbols, duration_hours=None):
        "Continuous mode"
        print(f"🔄 Continuous mode: {len(symbols)} symbols")
        if duration_hours:
            print(f"⏱️ Duration: {duration_hours}h")
        
        self.engine.run_continuous(symbols, interval_sec=600, duration_hours=duration_hours)

def main():
    parser = argparse.ArgumentParser(description="Complete ML Paper Trading System")
    parser.add_argument("--symbols", type=str, default=None,
                        help="Comma-separated symbols (e.g. AAPL,MSFT)")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Dry run (default)")
    parser.add_argument("--live", action="store_true",
                        help="Live trading (dangerous!)")
    parser.add_argument("--duration", type=float,
                        help="Continuous duration in hours")
    parser.add_argument("--single-cycle", action="store_true", default=False,
                        help="Run one cycle only")
    
    args = parser.parse_args()
    
    # Setup
    dry_run = not args.live
    system = CompletePaperTradingSystem(dry_run=dry_run)
    symbols = system.load_symbols(args.symbols)
    
    if args.single_cycle or args.duration is None:
        system.run_trading_cycle(symbols)
    else:
        system.run_continuous(symbols, args.duration)

if __name__ == "__main__":
    main()
