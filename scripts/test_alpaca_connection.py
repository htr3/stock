#!/usr/bin/env python3
"""Test Alpaca connection"""
import sys
import os

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from alpaca.trading.client import TradingClient

print("Testing Alpaca connection...")

try:
    client = TradingClient(
        api_key=os.getenv('APCA_API_KEY_ID'),
        secret_key=os.getenv('APCA_API_SECRET_KEY'),
        paper=True
    )
    
    account = client.get_account()
    
    print("\n✅ CONNECTED TO ALPACA!\n")
    print(f"Account Equity:    ${float(account.equity):,.2f}")
    print(f"Cash Available:    ${float(account.cash):,.2f}")
    print(f"Buying Power:      ${float(account.buying_power):,.2f}")
    print(f"Account Status:    {account.status}")
    print(f"\n✅ Ready for paper trading!\n")
    
except Exception as e:
    print(f"\nERROR during connection: {e}\n")
    import traceback
    traceback.print_exc()
