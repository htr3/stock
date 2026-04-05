#!/usr/bin/env python3
"""
📊 TRADING DASHBOARD - View Live Trading Status
Shows P&L, positions, and recent trades without stopping the system
"""

import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from alpaca.trading.client import TradingClient
from datetime import datetime
import json
from pathlib import Path

def show_dashboard():
    """Display trading dashboard"""
    api_key = os.getenv('APCA_API_KEY_ID')
    secret_key = os.getenv('APCA_API_SECRET_KEY')

    if not api_key or not secret_key:
        print("[ERROR] API keys not set")
        return

    try:
        client = TradingClient(api_key, secret_key, paper=True)
        account = client.get_account()

        print("\n" + "="*80)
        print(f"  TRADING DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")

        # Account info
        equity = float(account.equity)
        cash = float(account.cash)
        pnl = equity - 100000

        print("[ACCOUNT STATUS]")
        print(f"  Equity:      ${equity:>12,.2f}")
        print(f"  Cash:        ${cash:>12,.2f}")
        print(f"  P&L:         ${pnl:>12,.2f} ({pnl/100000*100:+.2f}%)")
        print()

        # Positions
        positions = client.get_all_positions()
        
        print("[OPEN POSITIONS]")
        if positions:
            for pos in positions:
                avg_price = float(pos.avg_entry_price)
                current_price = float(pos.current_price)
                qty = int(float(pos.qty))
                unrealized_pl = float(pos.unrealized_pl) if pos.unrealized_pl else 0
                
                print(f"  {pos.symbol}")
                print(f"    Shares:  {qty}")
                print(f"    Avg Entry: ${avg_price:.2f}")
                print(f"    Current:   ${current_price:.2f}")
                print(f"    P&L:       ${unrealized_pl:+.2f}")
                print()
        else:
            print("  None\n")

        # Recent trades from log
        log_file = Path(__file__).parent.parent / 'logs' / f'trading_log_{datetime.now().strftime("%Y%m%d")}.json'
        
        print("[RECENT TRADES]")
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    trades = json.load(f)
                
                if trades:
                    for trade in trades[-5:]:  # Last 5 trades
                        print(f"  {trade['timestamp']}: {trade['side']:4s} {trade['qty']} {trade['symbol']}")
                    
                    if len(trades) > 5:
                        print(f"  ... and {len(trades) - 5} more trades")
                else:
                    print("  None yet\n")
            except:
                print("  (Log file error)\n")
        else:
            print("  (Log file not created yet)\n")

        print("="*80 + "\n")

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    show_dashboard()
