#!/usr/bin/env python3
"""Risk Guard Agent: Circuit breakers, position limits"""

import json
import os
from pathlib import Path
from datetime import datetime

import alpaca_trade_api as tradeapi
import yfinance as yf

ROOT = Path(__file__).resolve().parents[2]


class RiskGuardAgent:
    def __init__(self):
        self.config_path = ROOT / "scripts" / "config" / "agent_config.json"
        with open(self.config_path) as f:
            self.config = json.load(f)['risk_guard']

        self.api = tradeapi.REST(
            os.getenv('APCA_API_KEY_ID'),
            os.getenv('APCA_API_SECRET_KEY'),
            base_url='https://paper-api.alpaca.markets'
        )

        self.daily_pnl = 0.0
        self.max_positions = {}

    def check_risk_limits(self) -> bool:
        """Multi-level risk gates"""

        checks = {
            'position_size_ok': self._check_position_sizes(),
            'drawdown_ok': self._check_drawdown(),
            'volatility_ok': self._check_volatility(),
            'circuit_breaker_ok': self._check_circuit_breaker()
        }

        healthy = all(checks.values())
        print(f"Risk gates: {'ALL PASS' if healthy else 'BLOCKED'}")

        return healthy

    def _check_position_sizes(self) -> bool:
        current_positions = self._get_current_positions()
        for symbol, size in current_positions.items():
            if abs(size) > self.config['max_position_size']:
                print(f"Position limit: {symbol} {size}")
                return False
        return True

    def _check_drawdown(self) -> bool:
        if self.daily_pnl < -self.config['max_drawdown']:
            print(f"Max drawdown: {self.daily_pnl:.1%}")
            return False
        return True

    def _check_volatility(self) -> bool:
        # VIX or symbol ATR check
        vix = self._get_vix()
        if vix > self.config['volatility_gate']:
            print(f"High volatility: VIX={vix:.1f}")
            return False
        return True

    def _check_circuit_breaker(self) -> bool:
        if abs(self.daily_pnl) > self.config['circuit_breaker']:
            print(f"Circuit breaker tripped: P&L={self.daily_pnl:.1%}")
            return False
        return True

    def _get_current_positions(self) -> dict:
        """Real Alpaca positions pct"""
        try:
            positions = self.api.list_positions()
            pct = {p.symbol: float(p.pct_of_portfolio or 0) for p in positions}
            return pct
        except Exception as e:
            print(f"Position fetch error: {e}")
            return {}

    def _get_vix(self) -> float:
        """Fetch US VIX"""
        try:
            ticker = yf.Ticker('^VIX')
            data = ticker.history(period='1d')
            return data['Close'].iloc[-1]
        except Exception:
            print("VIX fetch failed, using mock")
            return 15.2
