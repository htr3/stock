#!/usr/bin/env python3
"""Timestamped feature store with decay"""

from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


class FeatureStore:
    def __init__(self):
        self.store_path = ROOT / "data" / "features.parquet"
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

    def store_features(self, features: dict, symbols: list):
        """Store with timestamp + decay weight"""
        df = pd.DataFrame([features])
        df['timestamp'] = datetime.now()
        df['symbols'] = ','.join(symbols)
        df['decay_weight'] = np.exp(-0.1 * 0)  # Fresh = 1.0

        if self.store_path.exists():
            existing = pd.read_parquet(self.store_path)
            df = pd.concat([existing, df])
        df.to_parquet(self.store_path)

    def load_features(self, days_back: int = 7) -> pd.DataFrame:
        """Load recent features with decay"""
        cutoff = datetime.now() - timedelta(days=days_back)

        if not self.store_path.exists():
            return pd.DataFrame()

        df = pd.read_parquet(self.store_path)
        df['age_days'] = (datetime.now() - df['timestamp']).dt.total_seconds() / 86400
        df['decay'] = np.exp(-0.1 * df['age_days'])

        recent = df[df['timestamp'] > cutoff]
        return recent.drop(['timestamp', 'age_days'], axis=1).fillna(0)
