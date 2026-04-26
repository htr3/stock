#!/usr/bin/env python3
"""Feature Analysis Agent: PSI drift, null rates, outliers"""

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from utils.feature_store import FeatureStore


class FeatureAnalysisAgent:
    def __init__(self):
        self.feature_store = FeatureStore()
        ref_df = self.feature_store.load_features(days_back=7)
        self.reference_stats = ref_df.mean(numeric_only=True).to_dict() if not ref_df.empty else {}
        print(f"Reference stats loaded: {len(self.reference_stats)} features")

    def check_features(self, features: dict) -> dict:
        """PSI drift detection + quality gates"""
        df = pd.DataFrame([features])

        health = {
            'healthy': True,
            'issues': [],
            'psi_scores': {}
        }

        for col in df.columns:
            if col in self.reference_stats:
                psi = self._calculate_psi(df[col], self.reference_stats[col])
                health['psi_scores'][col] = psi

                if psi > 0.1:
                    health['healthy'] = False
                    health['issues'].append(f"High PSI drift: {col}={psi:.3f}")

        null_rate = df.isnull().mean().max()
        if null_rate > 0.05:
            health['healthy'] = False
            health['issues'].append(f"High null rate: {null_rate:.1%}")

        print(f"Feature health: {'OK' if health['healthy'] else 'ALERT'}")
        return health

    def _calculate_psi(self, current: pd.Series, reference: pd.Series, buckets=10) -> float:
        """Population Stability Index"""
        def scale_range(input_series, min_val, max_val):
            return (input_series - min_val) / (max_val - min_val)

        min_val = min(reference.min(), current.min())
        max_val = max(reference.max(), current.max())

        scaled_ref = scale_range(reference, min_val, max_val)
        scaled_cur = scale_range(current, min_val, max_val)

        breaks = np.arange(0, 1.01, 1.0 / buckets)
        breaks = np.unique(breaks)

        def get_bucket(data, breaks):
            return pd.cut(data, breaks, include_lowest=True)

        ref_bucket = get_bucket(scaled_ref, breaks)
        cur_bucket = get_bucket(scaled_cur, breaks)

        ref_pct = ref_bucket.value_counts() / len(ref_bucket)
        cur_pct = cur_bucket.value_counts() / len(cur_bucket)

        common = ref_pct.index.intersection(cur_pct.index)

        psi = np.sum((ref_pct[common] - cur_pct[common]) * np.log(ref_pct[common] / cur_pct[common]))
        return psi
