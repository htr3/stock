"""
Feature Selection & Analysis
Reduce 150+ features to the 20-30 that actually matter
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')


class FeatureSelector:
    """Feature selection and importance analysis"""
    
    def __init__(self, X_train, X_test, y_train, y_test):
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.feature_importance = None
        self.selected_features = None
    
    def get_xgboost_importance(self, top_n=30):
        """Get feature importance from XGBoost"""
        print("\n" + "="*70)
        print("XGBoost Feature Importance Analysis")
        print("="*70)
        
        model = xgb.XGBClassifier(n_estimators=100, max_depth=5, random_state=42)
        model.fit(self.X_train, self.y_train)
        
        importance = pd.DataFrame({
            "feature": self.X_train.columns,
            "importance": model.feature_importances_
        }).sort_values(by="importance", ascending=False)
        
        print(f"\n✅ Top {top_n} Most Important Features:\n")
        print(importance.head(top_n).to_string(index=False))
        
        self.feature_importance = importance
        return importance
    
    def get_random_forest_importance(self, top_n=30):
        """Get feature importance from Random Forest"""
        print("\n" + "="*70)
        print("Random Forest Feature Importance Analysis")
        print("="*70)
        
        model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        model.fit(self.X_train, self.y_train)
        
        importance = pd.DataFrame({
            "feature": self.X_train.columns,
            "importance": model.feature_importances_
        }).sort_values(by="importance", ascending=False)
        
        print(f"\n✅ Top {top_n} Most Important Features:\n")
        print(importance.head(top_n).to_string(index=False))
        
        self.feature_importance = importance
        return importance
    
    def remove_correlated_features(self, correlation_threshold=0.9):
        """Remove highly correlated features"""
        print("\n" + "="*70)
        print("Removing Correlated Features")
        print("="*70)
        
        # Calculate correlation matrix
        corr_matrix = self.X_train.corr().abs()
        
        # Select upper triangle of correlation matrix
        upper = corr_matrix.where(
            ~np.tril(np.ones(corr_matrix.shape)).astype(bool)
        )
        
        # Find features with correlation > threshold
        to_drop = set()
        for column in upper.columns:
            drop_cols = [idx for idx, val in upper[column].items() if val > correlation_threshold]
            to_drop.update(drop_cols)
        
        print(f"\n⚠️  Found {len(to_drop)} highly correlated features to remove:")
        if to_drop:
            print(f"   {', '.join(list(to_drop)[:10])}...")
        
        return list(to_drop)
    
    def select_top_features(self, n_features=20):
        """Select top N features"""
        if self.feature_importance is None:
            self.get_xgboost_importance()
        
        top_features = self.feature_importance.head(n_features)['feature'].tolist()
        self.selected_features = top_features
        
        print(f"\n✅ Selected top {n_features} features")
        print(f"   Total features: {len(top_features)}")
        
        return top_features
    
    def analyze_feature_distribution(self, top_n=10):
        """Visualize feature importance"""
        if self.feature_importance is None:
            self.get_xgboost_importance()
        
        top_features = self.feature_importance.head(top_n)
        
        plt.figure(figsize=(12, 6))
        plt.barh(range(len(top_features)), top_features['importance'].values)
        plt.yticks(range(len(top_features)), top_features['feature'].values)
        plt.xlabel('Importance Score')
        plt.title(f'Top {top_n} Feature Importance')
        plt.tight_layout()
        plt.savefig('../outputs/plots/feature_importance_analysis.png', dpi=150)
        plt.close()
        
        print("✅ Feature importance plot saved!")
    
    def get_signature_features(self):
        """Get the core features that define your model"""
        print("\n" + "="*70)
        print("Signature Features (Core Model Drivers)")
        print("="*70)
        
        if self.feature_importance is None:
            self.get_xgboost_importance()
        
        # Features that explain 80% of importance
        cumsum = self.feature_importance['importance'].cumsum()
        cumsum_pct = cumsum / cumsum.iloc[-1]
        core_features = cumsum_pct[cumsum_pct <= 0.8]
        
        signature = self.feature_importance.iloc[:len(core_features)]
        
        print(f"\n🎯 Core Features (80% of importance):\n")
        print(signature.to_string(index=False))
        print(f"\n✅ Total core features: {len(signature)}")
        
        return signature['feature'].tolist()


class ICFeatureSelector:
    """
    Information-Coefficient based feature selector.

    For each feature it computes the Spearman rank correlation between the
    feature value at time t and the (signed) forward return at t+horizon.
    Features are then ranked by absolute IC and the top-K are kept.

    This is the selection scheme implied by Plan B Phase 3 -- it does NOT
    fit a model, so it cannot leak future information through tree splits.
    """

    def __init__(self, top_k: int = 60, method: str = "spearman"):
        if top_k <= 0:
            raise ValueError("top_k must be > 0")
        if method not in {"spearman", "pearson"}:
            raise ValueError("method must be 'spearman' or 'pearson'")
        self.top_k = top_k
        self.method = method
        self.ic_: pd.Series | None = None
        self.selected_: list[str] | None = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "ICFeatureSelector":
        if len(X) != len(y):
            raise ValueError("X and y must have the same length")

        ics = {}
        y_aligned = y.reindex(X.index) if isinstance(y, pd.Series) else pd.Series(y, index=X.index)
        for col in X.columns:
            s = X[col]
            mask = s.notna() & y_aligned.notna()
            if mask.sum() < 30:
                ics[col] = 0.0
                continue
            try:
                if self.method == "spearman":
                    ic = s[mask].rank().corr(y_aligned[mask].rank())
                else:
                    ic = s[mask].corr(y_aligned[mask])
            except Exception:
                ic = 0.0
            ics[col] = 0.0 if pd.isna(ic) else float(ic)

        self.ic_ = pd.Series(ics).sort_values(key=lambda s: s.abs(), ascending=False)
        self.selected_ = self.ic_.head(self.top_k).index.tolist()
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if self.selected_ is None:
            raise RuntimeError("ICFeatureSelector not fitted yet")
        return X[[c for c in self.selected_ if c in X.columns]]

    def fit_transform(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        return self.fit(X, y).transform(X)


def main():
    """Run feature selection analysis"""
    
    # Load your trained model data
    from data_preparation import DataPipeline
    from feature_engineering import FeatureEngineer
    from target_variable import TargetVariable
    import sys
    
    # Load data
    print("Loading data...")
    df = pd.read_csv('../data/raw/AAPL_10min_generated_data.csv')
    
    # Generate features
    print("Generating features...")
    engineer = FeatureEngineer(df)
    features = engineer.generate_all_features()
    
    # Generate targets
    targets = TargetVariable.create_all_targets(df)
    
    # Prepare data
    print("Preparing data...")
    pipeline = DataPipeline(features, targets)
    X_train, X_test, y_train, y_test = pipeline.prepare(
        target_col='target_direction'
    )
    
    # Feature selection
    selector = FeatureSelector(X_train, X_test, y_train, y_test)
    
    # Get importance
    print("\n" + "="*70)
    print("FEATURE IMPORTANCE ANALYSIS")
    print("="*70)
    
    selector.get_xgboost_importance(top_n=30)
    selector.analyze_feature_distribution(top_n=20)
    
    # Remove correlated features
    print("\n" + "="*70)
    print("CORRELATION ANALYSIS")
    print("="*70)
    
    correlated = selector.remove_correlated_features(correlation_threshold=0.9)
    
    # Get core features
    core_features = selector.get_signature_features()
    
    # Final recommendation - multiple options
    print("\n" + "="*70)
    print("FEATURE SETS")
    print("="*70)
    
    # Option 1: Core 28 features (80% importance)
    feature_sets = {
        'core_28_features.csv': core_features,
        'top_20_features.csv': selector.select_top_features(n_features=20),
        'top_15_independent.csv': [f for f in selector.select_top_features(n_features=15) if f not in correlated],
        'top_20_independent.csv': [f for f in selector.select_top_features(n_features=20) if f not in correlated],
        'top_30_independent.csv': [f for f in selector.select_top_features(n_features=30) if f not in correlated],
    }
    
    print(f"\n📊 Feature Set Options:")
    print(f"   1. Core Features (80% importance):     {len(core_features)} features")
    print(f"   2. Top 20 Features (with correlation): {len(feature_sets['top_20_features.csv'])} features")
    print(f"   3. Top 15 Independent Features:        {len(feature_sets['top_15_independent.csv'])} features")
    print(f"   4. Top 20 Independent Features:        {len(feature_sets['top_20_independent.csv'])} features")
    print(f"   5. Top 30 Independent Features:        {len(feature_sets['top_30_independent.csv'])} features")
    
    # Save all options
    for filename, features_list in feature_sets.items():
        feature_df = pd.DataFrame({
            'feature': features_list,
            'rank': range(1, len(features_list) + 1)
        })
        feature_df.to_csv(f'../outputs/{filename}', index=False)
        print(f"\n✅ Saved: {filename}")
    
    # Default recommendation: Top 20 independent (good balance)
    recommended = feature_sets['top_20_independent.csv']
    print(f"\n{'='*70}")
    print("📌 RECOMMENDED: Top 20 Independent Features")
    print(f"{'='*70}")
    print(f"\nUse for production trading:")
    print(recommended)
    
    return selector, recommended


if __name__ == "__main__":
    selector, selected_features = main()
