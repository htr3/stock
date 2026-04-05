"""
Train models with different feature sets and compare backtesting results
Shows which feature set actually makes money
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from backtesting import BacktestingEngine
from feature_engineering import FeatureEngineer
from target_variable import TargetVariable
from data_preparation import DataPipeline
import matplotlib.pyplot as plt


class FeatureSetComparison:
    """Compare different feature sets for trading profitability"""
    
    def __init__(self, df):
        self.df = df
        self.results = {}
        self.models = {}
    
    def load_feature_sets(self):
        """Load all generated feature sets"""
        feature_sets = {
            'Full_134': None,  # Use all features
            'Core_25': self._load_csv('../outputs/core_28_features.csv'),
            'Top_20': self._load_csv('../outputs/top_20_features.csv'),
            'Top_15_Indep': self._load_csv('../outputs/top_15_independent.csv'),
            'Top_20_Indep': self._load_csv('../outputs/top_20_independent.csv'),
            'Top_30_Indep': self._load_csv('../outputs/top_30_independent.csv'),
        }
        return feature_sets
    
    @staticmethod
    def _load_csv(filepath):
        """Load selected features from CSV"""
        try:
            df = pd.read_csv(filepath)
            return df['feature'].tolist()
        except:
            return None
    
    def train_and_test(self, X_train, X_test, y_train, y_test, feature_set_name):
        """Train XGBoost with given features"""
        
        # Select features
        features_to_use = X_train.columns.tolist()
        X_train_subset = X_train[features_to_use]
        X_test_subset = X_test[features_to_use]
        
        # Train XGBoost
        model = XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            verbosity=0
        )
        
        model.fit(X_train_subset, y_train, verbose=False)
        
        # Get predictions
        predictions = model.predict(X_test_subset)
        probabilities = model.predict_proba(X_test_subset)[:, 1]
        
        # Calculate accuracy
        accuracy = (predictions == y_test.values).mean()
        
        return model, predictions, probabilities, accuracy
    
    def run_comparison(self):
        """Compare all feature sets"""
        
        print("\nFEATURE SET COMPARISON: TRADING PROFITABILITY\n")
        
        # Load features  
        engineer = FeatureEngineer(self.df)
        all_features = engineer.generate_all_features()
        targets = TargetVariable.create_all_targets(self.df)
        
        # Prepare data
        pipeline = DataPipeline(all_features, targets)
        X_train, X_test, y_train, y_test = pipeline.prepare(
            target_col='target_direction'
        )
        
        # Load feature sets
        feature_sets = self.load_feature_sets()
        feature_sets['Full_134'] = X_train.columns.tolist()
        
        # Train and backtest each
        comparison_results = []
        
        for set_name, selected_features in feature_sets.items():
            if selected_features is None:
                continue
            
            print(f"Testing: {set_name}")
            
            # Check if features exist
            missing_features = [f for f in selected_features if f not in X_train.columns]
            if missing_features:
                print(f"  Skipped - missing features")
                continue
            
            # Select subset
            X_train_subset = X_train[selected_features]
            X_test_subset = X_test[selected_features]
            
            # Train model
            model, predictions, probabilities, accuracy = self.train_and_test(
                X_train_subset, X_test_subset, y_train, y_test, set_name
            )
            
            print(f"  Accuracy: {accuracy*100:.1f}% | Features: {len(selected_features)}")
            
            # Get returns
            returns = targets['price_change_pct'].iloc[len(X_train):]
            
            # Run backtest
            df_test = self.df.iloc[len(X_train):]
            
            backtest = BacktestingEngine(
                df_test,
                predictions,
                probabilities,
                returns,
                initial_balance=10000
            )
            
            # Test different confidence thresholds
            best_result = self._optimize_threshold(backtest, predictions, probabilities, returns)
            
            # Store results
            comparison_results.append({
                'Feature_Set': set_name,
                'Num_Features': len(selected_features),
                'Accuracy': accuracy,
                'Best_Threshold': best_result['threshold'],
                'Trades': best_result['trades'],
                'Win_Rate': best_result['win_rate'],
                'Total_Return': best_result['return'],
                'Final_Balance': best_result['final_balance'],
                'Sharpe_Ratio': best_result['sharpe'],
                'Max_Drawdown': best_result['drawdown']
            })
        
        # Create results dataframe
        results_df = pd.DataFrame(comparison_results)
        
        print(f"\n{'='*70}")
        print("COMPARISON SUMMARY")
        print(f"{'='*70}\n")
        
        # Sort by total return
        results_df = results_df.sort_values('Total_Return', ascending=False)
        
        print(results_df.to_string(index=False))
        
        # Save results
        results_df.to_csv('../outputs/feature_comparison_results.csv', index=False)
        print(f"\nSaved comparison results")
        
        # Recommendation
        print(f"\n{'='*70}")
        print("BEST FEATURE SET FOR TRADING")
        print(f"{'='*70}\n")
        
        best_row = results_df.iloc[0]
        print(f"Feature Set: {best_row['Feature_Set']}")
        print(f"Num Features: {int(best_row['Num_Features'])}")
        print(f"Accuracy: {best_row['Accuracy']*100:.1f}%")
        print(f"Profitability: {best_row['Total_Return']*100:.2f}%")
        print(f"Win Rate: {best_row['Win_Rate']*100:.1f}%")
        print(f"Sharpe Ratio: {best_row['Sharpe_Ratio']:.3f}")
        
        return results_df
    
    @staticmethod
    def _optimize_threshold(backtest, predictions, probabilities, returns):
        """Find best confidence threshold using the backtesting engine."""
        best_stats = {
            'threshold': 0.5,
            'trades': 0,
            'win_rate': 0,
            'return': 0,
            'final_balance': 10000,
            'sharpe': 0,
            'drawdown': 0,
            'profit_factor': 0,
            'stopped_early': False
        }
        
        for threshold in [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]:
            stats = backtest.run_backtest(
                confidence_threshold=threshold,
                position_size=0.02,
                stop_loss_pct=0.01,
                take_profit_pct=0.02,
                max_drawdown_stop=0.10,
                verbose=False
            )
            total_return = stats['total_return']
            
            if total_return > best_stats['return']:
                best_stats = {
                    'threshold': threshold,
                    'trades': stats['trades'],
                    'win_rate': stats['win_rate'],
                    'return': total_return,
                    'final_balance': stats['final_balance'],
                    'sharpe': stats['sharpe_ratio'],
                    'drawdown': stats['max_drawdown'],
                    'profit_factor': stats['profit_factor'],
                    'stopped_early': stats['stopped_due_to_drawdown']
                }
        
        return best_stats


def main():
    """Run feature set comparison"""
    df = pd.read_csv('../data/raw/AAPL_10min_generated_data.csv')
    
    comparator = FeatureSetComparison(df)
    results = comparator.run_comparison()
    
    return results


if __name__ == "__main__":
    results = main()
