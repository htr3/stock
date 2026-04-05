"""
MAIN PIPELINE: Complete ML Model for Stock Price Prediction
Combines all phases into one executable script
"""

import pandas as pd
import numpy as np
import sys
from datetime import datetime

# Import custom modules
from feature_engineering import FeatureEngineer
from target_variable import TargetVariable
from data_preparation import DataPipeline
from model_training import ModelTrainer


class StockPricePredictionPipeline:
    """Complete end-to-end ML pipeline for stock price prediction"""
    
    def __init__(self, csv_file: str):
        """
        Initialize pipeline
        
        Args:
            csv_file: Path to CSV file with OHLCV data
                     Columns required: Date, Open, High, Low, Close, Volume
        """
        print(f"\n{'='*70}")
        print(f"STOCK PRICE PREDICTION ML MODEL")
        print(f"Predicting 10-minute UP (+70%) vs DOWN (-30%) movements")
        print(f"{'='*70}\n")
        
        self.df = None
        self.features = None
        self.targets = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.trainer = None
        
        self.load_data(csv_file)
    
    def load_data(self, csv_file: str):
        """Load OHLCV data from CSV"""
        print(f"[PHASE 1] Loading data from {csv_file}...")
        
        try:
            self.df = pd.read_csv(csv_file)
            
            # Ensure required columns exist
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_cols:
                if col not in self.df.columns:
                    raise ValueError(f"Missing required column: {col}")
            
            print(f"✓ Loaded {len(self.df)} candles")
            print(f"  Columns: {', '.join(self.df.columns.tolist())}")
            print(f"  Date range: {self.df.index[0]} to {self.df.index[-1]}")
            
        except Exception as e:
            print(f"✗ Error loading data: {e}")
            sys.exit(1)
    
    def generate_features(self):
        """PHASE 2-3: Generate all features"""
        print(f"\n[PHASE 2-3] Generating features from technical analysis...")
        
        try:
            engineer = FeatureEngineer(self.df)
            self.features = engineer.generate_all_features()
            
            print(f"✓ Generated {len(self.features.columns)} features")
            print(f"  Feature categories:")
            print(f"    - Candlestick patterns")
            print(f"    - Technical indicators (RSI, MACD, Bollinger Bands, Stochastic, etc.)")
            print(f"    - Moving averages")
            print(f"    - Time-series features (lags, returns, rolling stats)")
            print(f"    - Volume features")
            print(f"    - Combined trading signals")
            
        except Exception as e:
            print(f"✗ Error generating features: {e}")
            sys.exit(1)
    
    def create_targets(self):
        """PHASE 4: Create target variables"""
        print(f"\n[PHASE 4] Creating target variables...")
        
        try:
            self.targets = TargetVariable.create_all_targets(self.df)
            
            print(f"✓ Created {len(self.targets.columns)} target variables:")
            print(f"  - target_direction: Next candle UP (1) or DOWN (0)")
            print(f"  - price_change_pct: Percentage change")
            print(f"  - price_change_points: Absolute point change")
            print(f"  - target_binary: Binary classification (threshold 0%)")
            print(f"  - target_multiclass: 3-class (Strong UP, Neutral, Strong DOWN)")
            
        except Exception as e:
            print(f"✗ Error creating targets: {e}")
            sys.exit(1)
    
    def prepare_data(self, target_col: str = 'target_direction'):
        """PHASE 5: Data preparation and cleaning"""
        print(f"\n[PHASE 5] Preparing data for model training...")
        
        try:
            pipeline = DataPipeline(self.features, self.targets)
            self.X_train, self.X_test, self.y_train, self.y_test = pipeline.prepare(
                target_col=target_col,
                remove_outliers=True,
                handle_imbalance=True,
                test_size=0.2
            )
            
        except Exception as e:
            print(f"✗ Error preparing data: {e}")
            sys.exit(1)
    
    def train_models(self):
        """PHASE 6: Model training and evaluation"""
        print(f"\n[PHASE 6] Training ML models...")
        
        try:
            self.trainer = ModelTrainer()
            
            # Train multiple models
            self.trainer.train_logistic_regression(
                self.X_train, self.y_train, self.X_test, self.y_test
            )
            
            self.trainer.train_random_forest(
                self.X_train, self.y_train, self.X_test, self.y_test
            )
            
            self.trainer.train_gradient_boosting(
                self.X_train, self.y_train, self.X_test, self.y_test
            )
            
            self.trainer.train_xgboost(
                self.X_train, self.y_train, self.X_test, self.y_test
            )
            
            self.trainer.train_lightgbm(
                self.X_train, self.y_train, self.X_test, self.y_test
            )
            
        except Exception as e:
            print(f"✗ Error training models: {e}")
            sys.exit(1)
    
    def evaluate_and_compare(self):
        """Compare all models and save the best one"""
        print(f"\n[PHASE 7] Evaluating and comparing models...")
        
        try:
            results_df = self.trainer.compare_models()
            best_model_name, filename = self.trainer.save_best_model()
            
            print(f"\n✓ Best performing model: {best_model_name.upper()}")
            
            return results_df, best_model_name
            
        except Exception as e:
            print(f"✗ Error evaluating models: {e}")
            sys.exit(1)
    
    def run_complete_pipeline(self, csv_file: str):
        """Run the complete pipeline"""
        
        self.load_data(csv_file)
        self.generate_features()
        self.create_targets()
        self.prepare_data(target_col='target_direction')
        self.train_models()
        results_df, best_model = self.evaluate_and_compare()
        
        print(f"\n{'='*70}")
        print(f"PIPELINE COMPLETE!")
        print(f"{'='*70}")
        print(f"\nNext steps:")
        print(f"1. Use the saved model for live predictions")
        print(f"2. Fine-tune hyperparameters based on results")
        print(f"3. Integrate with paper trading for validation")
        print(f"4. Deploy to production when confident")
        
        return results_df, best_model


def main():
    """Main execution"""
    
    # Example usage - replace with your data file
    csv_file = '../data/raw/AAPL_10min_generated_data.csv'  # Generated realistic stock data
    
    try:
        pipeline = StockPricePredictionPipeline(csv_file)
        results, best_model = pipeline.run_complete_pipeline(csv_file)
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
