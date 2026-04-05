#!/usr/bin/env python3
"""
📋 SYMBOL MANAGEMENT - Configure which stocks/cryptos to trade
"""

import sys
import os
import json
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'trading_symbols.json'

def load_config():
    """Load symbol configuration"""
    if not CONFIG_PATH.exists():
        print("[ERROR] Config file not found")
        return None
    
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def save_config(config):
    """Save symbol configuration"""
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    print("[OK] Config saved")

def show_menu():
    """Display main menu"""
    print("\n" + "="*60)
    print("  SYMBOL MANAGEMENT")
    print("="*60)
    print("\n1. View current symbols")
    print("2. Add stock")
    print("3. Remove stock")
    print("4. Enable/Disable category")
    print("5. View full config")
    print("6. Reset to default")
    print("0. Exit")
    print()

def view_symbols(config):
    """View currently enabled symbols"""
    print("\n[CURRENTLY TRADING]")
    print("-" * 60)
    
    symbols = []
    
    if config['stocks']['enabled']:
        print(f"\nStocks ({len(config['stocks']['symbols'])}): [ENABLED]")
        for sym in config['stocks']['symbols']:
            print(f"  • {sym}")
        symbols.extend(config['stocks']['symbols'])
    else:
        print(f"\nStocks: [DISABLED]")
    
    if config['etfs']['enabled']:
        print(f"\nETFs ({len(config['etfs']['symbols'])}): [ENABLED]")
        for sym in config['etfs']['symbols']:
            print(f"  • {sym}")
        symbols.extend(config['etfs']['symbols'])
    else:
        print(f"\nETFs: [DISABLED]")
    
    if config['options']['enabled']:
        print(f"\nOptions ({len(config['options']['symbols'])}): [ENABLED]")
        for sym in config['options']['symbols']:
            print(f"  • {sym}")
        symbols.extend(config['options']['symbols'])
    else:
        print(f"\nOptions: [DISABLED]")
    
    if config['crypto']['enabled']:
        print(f"\nCrypto ({len(config['crypto']['symbols'])}): [ENABLED]")
        for sym in config['crypto']['symbols']:
            print(f"  • {sym}")
        symbols.extend(config['crypto']['symbols'])
    else:
        print(f"\nCrypto: [DISABLED]")
    
    print(f"\nTotal Symbols: {len(symbols)}")
    print(f"All Symbols: {', '.join(symbols)}")

def add_symbol(config):
    """Add a new symbol"""
    print("\nAdd Symbol")
    category = input("Category (stocks/etfs/options/crypto): ").lower()
    
    if category not in config:
        print("[ERROR] Invalid category")
        return
    
    symbol = input("Symbol (e.g., AAPL, SPY): ").upper()
    
    if symbol in config[category]['symbols']:
        print(f"[WARN] {symbol} already in {category}")
        return
    
    config[category]['symbols'].append(symbol)
    save_config(config)
    print(f"[OK] Added {symbol} to {category}")

def remove_symbol(config):
    """Remove a symbol"""
    print("\nRemove Symbol")
    symbol = input("Symbol to remove (e.g., AAPL): ").upper()
    
    found = False
    for category in ['stocks', 'etfs', 'options', 'crypto']:
        if symbol in config[category]['symbols']:
            config[category]['symbols'].remove(symbol)
            save_config(config)
            print(f"[OK] Removed {symbol} from {category}")
            found = True
            break
    
    if not found:
        print(f"[ERROR] {symbol} not found")

def toggle_category(config):
    """Enable/disable a category"""
    print("\nToggle Category")
    print("1. Stocks")
    print("2. ETFs")
    print("3. Options")
    print("4. Crypto")
    
    choice = input("Choice (1-4): ")
    mapping = {'1': 'stocks', '2': 'etfs', '3': 'options', '4': 'crypto'}
    
    if choice not in mapping:
        print("[ERROR] Invalid choice")
        return
    
    category = mapping[choice]
    current = config[category]['enabled']
    config[category]['enabled'] = not current
    save_config(config)
    
    status = "ENABLED" if config[category]['enabled'] else "DISABLED"
    print(f"[OK] {category.upper()} {status}")

def view_config(config):
    """View full configuration"""
    print("\n" + "="*60)
    print("FULL CONFIGURATION")
    print("="*60)
    print(json.dumps(config, indent=2))

def reset_config():
    """Reset to default configuration"""
    default = {
        "stocks": {
            "enabled": True,
            "symbols": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        },
        "etfs": {
            "enabled": False,
            "symbols": ["SPY", "QQQ", "IWM"]
        },
        "options": {
            "enabled": False,
            "symbols": ["SPY", "QQQ"]
        },
        "crypto": {
            "enabled": False,
            "note": "Requires Alpaca Crypto subscription",
            "symbols": ["BTC/USD", "ETH/USD"]
        },
        "settings": {
            "position_size": 1,
            "max_positions": 5,
            "risk_percent": 2,
            "notes": "Edit symbols list to change what to trade"
        }
    }
    
    confirm = input("Reset to default? (yes/no): ").lower()
    if confirm == 'yes':
        save_config(default)
        print("[OK] Reset to default")

def main():
    """Main loop"""
    print("\n" + "="*60)
    print("  SYMBOL MANAGEMENT TOOL")
    print("="*60)
    
    config = load_config()
    if not config:
        return
    
    while True:
        show_menu()
        choice = input("Choice (0-6): ").strip()
        
        if choice == '1':
            view_symbols(config)
        elif choice == '2':
            add_symbol(config)
            config = load_config()
        elif choice == '3':
            remove_symbol(config)
            config = load_config()
        elif choice == '4':
            toggle_category(config)
            config = load_config()
        elif choice == '5':
            view_config(config)
        elif choice == '6':
            reset_config()
            config = load_config()
        elif choice == '0':
            print("\nGoodbye!")
            break
        else:
            print("[ERROR] Invalid choice")

if __name__ == "__main__":
    main()
