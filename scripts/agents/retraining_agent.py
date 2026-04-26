#!/usr/bin/env python3
"""Retraining Agent: XGBoost with time-series CV"""

from datetime import datetime
from pathlib import Path

import joblib
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit

from utils.model_registry import ModelRegistry
from pipelines.training_pipeline import TrainingPipeline

ROOT = Path(__file__).resolve().parents[2]


class RetrainingAgent:
    def __init__(self):
        self.registry = ModelRegistry()
        self.pipeline = TrainingPipeline()

    def trigger_retrain(self, data_volume: int, f1_drop: float) -> str:
        """Check triggers and execute retrain"""

        if data_volume < 10000 or f1_drop < 0.02:
            return "no_trigger"

        print("Triggered retraining...")
        new_model_path = self._train_challenger()

        if self.registry.evaluate_promotion(new_model_path):
            self.registry.promote_challenger(new_model_path)
            return "promoted"
        else:
            self.registry.archive_challenger(new_model_path)
            return "rejected"

    def _train_challenger(self):
        """Train XGBoost challenger"""
        X, y = self.pipeline.get_training_data()

        tscv = TimeSeriesSplit(n_splits=5)
        best_score = 0
        best_model = None

        for train_idx, val_idx in tscv.split(X):
            model = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.05,
                random_state=42
            )
            model.fit(X.iloc[train_idx], y.iloc[train_idx])
            score = model.score(X.iloc[val_idx], y.iloc[val_idx])

            if score > best_score:
                best_score = score
                best_model = model

        saved_dir = ROOT / "models" / "saved"
        saved_dir.mkdir(parents=True, exist_ok=True)
        model_path = str(saved_dir / f"challenger_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
        joblib.dump(best_model, model_path)

        print(f"Challenger F1: {best_score:.4f}")
        return model_path
