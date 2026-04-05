#!/usr/bin/env python3
"""
🚀 WEB DASHBOARD SERVER
Real-time trading dashboard with REST API
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from flask import Flask, render_template, jsonify
from flask_cors import CORS

from alpaca.trading.client import TradingClient

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

# Global state
class TradingState:
    def __init__(self):
        self.api_key = os.getenv('APCA_API_KEY_ID')
        self.secret_key = os.getenv('APCA_API_SECRET_KEY')
        self.trading_client = None
        
        if self.api_key and self.secret_key:
            try:
                self.trading_client = TradingClient(self.api_key, self.secret_key, paper=True)
                print("[OK] Alpaca connected")
            except Exception as e:
                print(f"[ERROR] {e}")

state = TradingState()

@app.route('/')
def dashboard():
    """Serve dashboard"""
    return render_template('dashboard.html')

@app.route('/api/account')
def get_account():
    """Get account info"""
    try:
        if not state.trading_client:
            return jsonify({'error': 'Not connected'}), 500
        
        account = state.trading_client.get_account()
        
        equity = float(account.equity)
        pnl = equity - 100000
        
        return jsonify({
            'equity': equity,
            'cash': float(account.cash),
            'buying_power': float(account.buying_power),
            'pnl': pnl,
            'pnl_pct': (pnl / 100000 * 100),
            'status': 'ACTIVE'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions')
def get_positions():
    """Get open positions"""
    try:
        if not state.trading_client:
            return jsonify({'positions': []})
        
        positions = state.trading_client.get_all_positions()
        
        pos_list = []
        for pos in positions:
            pos_list.append({
                'symbol': pos.symbol,
                'qty': int(float(pos.qty)),
                'avg_entry_price': float(pos.avg_entry_price),
                'current_price': float(pos.current_price),
                'unrealized_pl': float(pos.unrealized_pl) if pos.unrealized_pl else 0,
                'unrealized_plpc': float(pos.unrealized_plpc) if pos.unrealized_plpc else 0
            })
        
        return jsonify({'positions': pos_list})
    except Exception as e:
        return jsonify({'error': str(e), 'positions': []}), 200

@app.route('/api/trades')
def get_trades():
    """Get recent trades"""
    try:
        log_dir = Path(__file__).parent.parent / 'logs'
        log_file = log_dir / f'trading_log_{datetime.now().strftime("%Y%m%d")}.json'
        
        if log_file.exists():
            with open(log_file, 'r') as f:
                trades = json.load(f)
            return jsonify({'trades': list(reversed(trades[-30:]))})
        else:
            return jsonify({'trades': []})
    except Exception as e:
        return jsonify({'error': str(e), 'trades': []}), 200

@app.route('/api/stats')
def get_stats():
    """Get trading statistics"""
    try:
        log_dir = Path(__file__).parent.parent / 'logs'
        log_file = log_dir / f'trading_log_{datetime.now().strftime("%Y%m%d")}.json'
        
        stats = {
            'total_trades': 0,
            'buys': 0,
            'sells': 0,
            'symbols': []
        }
        
        if log_file.exists():
            with open(log_file, 'r') as f:
                trades = json.load(f)
            
            stats['total_trades'] = len(trades)
            stats['buys'] = len([t for t in trades if t['side'] == 'BUY'])
            stats['sells'] = len([t for t in trades if t['side'] == 'SELL'])
            stats['symbols'] = sorted(list(set([t['symbol'] for t in trades])))
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print("  TRADING DASHBOARD SERVER")
    print("="*70)
    print("\n[INFO] Server starting...")
    print("  URL: http://localhost:5000")
    print("  Dashboard: http://localhost:5000/")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
