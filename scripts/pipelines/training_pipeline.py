#!/usr/bin/env python3
"""Retraining + paper trade + promotion pipeline"""

import numpy as np

from utils.feature_store import FeatureStore
from utils.model_registry import ModelRegistry


class TrainingPipeline:
    def __init__(self):
        # NOTE: RetrainingAgent imports TrainingPipeline; avoid circular import by
        # constructing the agent lazily inside execute_full_retrain.
        self.registry = ModelRegistry()
        self.feature_store = FeatureStore()

    def execute_full_retrain(self):
        """Complete retraining workflow"""
        from agents.retraining_agent import RetrainingAgent
        retrain_agent = RetrainingAgent()

        print("Full retraining pipeline...")

        # 1. Load training data
        X, y = self.get_training_data()

        # 2. Train challenger
        result = retrain_agent.trigger_retrain(len(X), f1_drop=0.03)

        # 3. Paper trade test (mock)
        paper_results = self._paper_trade_test()

        # 4. Promotion decision
        if result == 'promoted' and paper_results['winrate'] > 0.55:
            print("New champion promoted!")
        else:
            print("Challenger needs more validation")

    def get_training_data(self):
        """Load features + targets"""
        # Feature store + historical labels
        features = self.feature_store.load_features(days_back=30)
        # Mock targets for now
        y = np.random.choice([0, 1], size=len(features), p=[0.48, 0.52])
        return features, y

    def _paper_trade_test(self) -> dict:
        """1-week paper trade simulation"""
        return {'winrate': 0.57, 'sharpe': 1.2}
