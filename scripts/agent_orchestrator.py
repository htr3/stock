#!/usr/bin/env python3
import json
import sys
import time
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent))

import alpaca_trade_api as tradeapi
import os
import numpy as np

from agents.news_intelligence_agent import NewsIntelligenceAgent
from agents.feature_analysis_agent import FeatureAnalysisAgent
from agents.risk_guard_agent import RiskGuardAgent
from agents.retraining_agent import RetrainingAgent
from utils.feature_store import FeatureStore
from utils.model_registry import ModelRegistry


class AgentOrchestrator:
    def __init__(self, live: bool = False):
        self.live = live
        self.feature_store = FeatureStore()
        self.model_registry = ModelRegistry()

        self.api = tradeapi.REST(
            os.getenv('APCA_API_KEY_ID'),
            os.getenv('APCA_API_SECRET_KEY'),
            base_url='https://paper-api.alpaca.markets' if not self.live else 'https://api.alpaca.markets'
        )

        # Initialize agents
        self.news_agent = NewsIntelligenceAgent()
        self.feature_agent = FeatureAnalysisAgent()
        self.risk_agent = RiskGuardAgent()
        self.retrain_agent = RetrainingAgent()

        print(f"Orchestrator initialized (live={live})")

    def run_trading_loop(self, symbols: List[str]):
        """Main decision loop"""
        while True:
            # 1. News intelligence
            news_features = self.news_agent.analyze_news(symbols)

            # 2. Feature analysis + drift detection
            feature_health = self.feature_agent.check_features(news_features)

            if feature_health['healthy']:
                # 3. Risk gates
                risk_ok = self.risk_agent.check_risk_limits()

                if risk_ok:
                    # 4. Model prediction (champion model)
                    model = self.model_registry.champion()
                    if model:
                        X = np.array([list(news_features.values())])
                        pred = model.predict(X)[0]
                        prob = model.predict_proba(X)[0]
                        action = 'buy' if prob[1] > 0.6 else 'sell' if prob[0] > 0.6 else 'hold'
                        price = 150.0  # Mock from live data fetcher
                        decision = {'action': action, 'confidence': max(prob), 'symbol': symbols[0], 'price': price}
                    else:
                        decision = {'action': 'hold', 'confidence': 0.0, 'symbol': symbols[0], 'price': 0}

                    # 5. Execute (Alpaca integration)
                    self._execute_trade(decision)

            time.sleep(600)  # 10min cycle

    def run_paper_trading(self, symbols: List[str], duration_hours: float):
        """Paper trading simulation"""
        print(f"Paper trading for {duration_hours}h with {symbols}")
        end_time = time.time() + duration_hours * 3600
        while time.time() < end_time:
            news_features = self.news_agent.analyze_news(symbols)

            feature_health = self.feature_agent.check_features(news_features)

            if feature_health['healthy']:
                risk_ok = self.risk_agent.check_risk_limits()

                if risk_ok:
                    model = self.model_registry.champion()
                    if model:
                        X = np.array([list(news_features.values())])
                        pred = model.predict(X)[0]
                        prob = model.predict_proba(X)[0]
                        action = 'buy' if prob[1] > 0.6 else 'sell' if prob[0] > 0.6 else 'hold'
                        price = 150.0  # Mock
                        decision = {'action': action, 'confidence': max(prob), 'symbol': symbols[0], 'price': price}
                    else:
                        decision = {'action': 'hold'}

                    self._execute_trade(decision)

            time.sleep(60)  # 1min for test

    def _execute_trade(self, decision):
        """Alpaca trade execution"""
        if 'action' not in decision or decision['action'] == 'hold':
            print(f"HOLD {decision.get('symbol', 'N/A')}")
            return

        try:
            symbol = decision['symbol']
            qty = 1  # Fixed qty for test
            side = 'buy' if decision['action'] == 'buy' else 'sell'

            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='gtc'
            )
            print(f"{side.upper()} {qty} {symbol} @ market - Order ID: {order.id}")
        except Exception as e:
            print(f"Trade error: {e}")
