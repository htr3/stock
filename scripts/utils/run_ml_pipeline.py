"""
Reusable ML Pipeline for Stock Price Prediction
Extracted from scripts/main.py for integration with agent system
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Import from scripts (adjust paths as needed)
# Note: These need to be available in sys.path or properly installed
try:
    from feature_engineering import FeatureEngineer
    from target_variable import TargetVariable
    from data_preparation import DataPipeline
    from model_training import ModelTrainer
except ImportError as e:
    print(f"Import error - ensure scripts/ modules are in path: {e}")
    raise

class StockPricePredictionPipeline:
    '''Complete end-to-end ML pipeline for stock price prediction'''
    
    def __init__(self, df=None, csv_file=None):
        self.df = None
        self.features = None
        self.targets = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.trainer = None
        
        if csv_file:
            self.load_data(csv_file)
        elif df is not None:
            self.df = df
        else:
            raise ValueError("Provide csv_file or df")
    
    def load_data(self, csv_file: str):
        print(f"[ML PIPELINE] Loading data from {csv_file}...")
        
        try:
            self.df = pd.read_csv(csv_file)
            
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_cols:
                if col not in self.df.columns:
                    raise ValueError(f"Missing required column: {col}")
            
            print(f"✓ Loaded {len(self.df)} candles")
        except Exception as e:
            print(f"✗ Error loading data: {e}")
            raise
    
    def generate_features(self):
        print(f"[ML PIPELINE] Generating features...")
        engineer = FeatureEngineer(self.df)
        self.features = engineer.generate_all_features()
        print(f"✓ Generated {len(self.features.columns)} features")
    
    def create_targets(self):
        print(f"[ML PIPELINE] Creating targets...")
        self.targets = TargetVariable.create_all_targets(self.df)
        print(f"✓ Created {len(self.targets.columns)} targets")
    
    def prepare_data(self, target_col: str = 'target_direction'):
        pipeline = DataPipeline(self.features, self.targets)
        self.X_train, self.X_test, self.y_train, self.y_test = pipeline.prepare(
            target_col=target_col,
            remove_outliers=True,
            handle_imbalance=True,
            test_size=0.2
        )
    
    def train_models(self):
        print(f"[ML PIPELINE] Training models...")
        self.trainer = ModelTrainer()
        
        self.trainer.train_logistic_regression(self.X_train, self.y_train, self.X_test, self.y_test)
        self.trainer.train_random_forest(self.X_train, self.y_train, self.X_test, self.y_test)
        self.trainer.train_gradient_boosting(self.X_train, self.y_train, self.X_test, self.y_test)
        self.trainer.train_xgboost(self.X_train, self.y_train, self.X_test, self.y_test)
        self.trainer.train_lightgbm(self.X_train, self.y_train, self.X_test, self.y_test)
    
    def evaluate_and_compare(self):
        results_df = self.trainer.compare_models()
        best_model_name, filename = self.trainer.save_best_model()
        print(f"✓ Best model: {best_model_name}")
        return results_df, best_model_name
    
    def run_pipeline(self, target_col='target_direction'):
        self.generate_features()
        self.create_targets()
        self.prepare_data(target_col)
        self.train_models()
        return self.evaluate_and_compare()

def run_ml_pipeline(csv_file: str):
    """
    Standalone function to run complete ML pipeline
    Returns: (results_df, best_model_name)
    """
    print(f"\n{'='*70}")
    print(f"STOCK ML PIPELINE (for Agent Integration)")
    print(f"{'='*70}")
    
    pipeline = StockPricePredictionPipeline(csv_file=csv_file)
    results_df, best_model = pipeline.run_pipeline()
    
    print(f"\n✅ ML Pipeline complete! Best model: {best_model}")
    return results_df, best_model

if __name__ == '__main__':
    # Legacy standalone usage
    csv_file = '../data/raw/AAPL_10min_generated_data.csv'
    run_ml_pipeline(csv_file)
