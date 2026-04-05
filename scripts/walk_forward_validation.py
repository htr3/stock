"""
Walk-Forward Validation

Simulates real-world trading by rolling train/test windows
Instead of single 80/20 split, we do:

Week 1-4: Train
Week 5: Test → Record metrics

Week 2-5: Train
Week 6: Test → Record metrics

... continue sliding

This is the proper way to validate time-series strategies
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier


class WalkForwardValidator:
    """Walk-forward validation for time-series strategies"""
    
    def __init__(self, features_df, targets_df, test_window=5, train_window=20):
        """
        Args:
            features_df: Feature matrix
            targets_df: Target variables
            test_window: Number of periods to test (candles)
            train_window: Number of periods to train (candles)
        """
        self.features = features_df
        self.targets = targets_df
        self.test_window = test_window
        self.train_window = train_window
        self.results = []
    
    def run_walk_forward(self, target_col='target_direction', model_type='xgboost'):
        """
        Run walk-forward validation
        
        Returns metrics for each fold
        """
        print("\n" + "="*70)
        print("WALK-FORWARD VALIDATION")
        print("="*70)
        print(f"Train Window: {self.train_window} candles")
        print(f"Test Window: {self.test_window} candles")
        print(f"Target: {target_col}\n")
        
        y = self.targets[target_col]
        
        # Calculate number of windows
        total_periods = len(self.features)
        num_windows = (total_periods - self.train_window) // self.test_window
        
        print(f"Total candles: {total_periods}")
        print(f"Number of folds: {num_windows}\n")
        print("-"*70)
        
        fold_results = []
        
        for fold in range(num_windows):
            # Calculate indices
            train_start = fold * self.test_window
            train_end = train_start + self.train_window
            test_start = train_end
            test_end = test_start + self.test_window
            
            if test_end > len(self.features):
                break
            
            # Get train/test data
            X_train = self.features.iloc[train_start:train_end]
            y_train = y.iloc[train_start:train_end]
            X_test = self.features.iloc[test_start:test_end]
            y_test = y.iloc[test_start:test_end]
            
            # Train model
            if model_type == 'xgboost':
                model = XGBClassifier(
                    n_estimators=50,
                    max_depth=5,
                    learning_rate=0.1,
                    random_state=42,
                    verbosity=0
                )
            else:
                model = RandomForestClassifier(
                    n_estimators=50,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
            
            model.fit(X_train, y_train)
            
            # Test
            predictions = model.predict(X_test)
            accuracy = (predictions == y_test).mean()
            
            # Store results
            fold_results.append({
                'fold': fold + 1,
                'train_period': f"{train_start}:{train_end}",
                'test_period': f"{test_start}:{test_end}",
                'accuracy': accuracy,
                'trades': len(y_test),
                'model_type': model_type
            })
            
            print(f"Fold {fold+1:2d}: Accuracy = {accuracy*100:5.1f}% | Test candles: {len(y_test):3d}")
        
        print("-"*70)
        
        # Calculate statistics
        accuracies = [r['accuracy'] for r in fold_results]
        mean_acc = np.mean(accuracies)
        std_acc = np.std(accuracies)
        min_acc = np.min(accuracies)
        max_acc = np.max(accuracies)
        
        print(f"\nSummary:")
        print(f"  Mean Accuracy:  {mean_acc*100:.1f}%")
        print(f"  Std Dev:        {std_acc*100:.1f}%")
        print(f"  Min:            {min_acc*100:.1f}%")
        print(f"  Max:            {max_acc*100:.1f}%")
        
        if std_acc < 0.05:
            print(f"\n✅ CONSISTENT - Low std dev indicates stable model")
        elif std_acc < 0.10:
            print(f"\n⚠️  VARIABLE - Model performance varies")
        else:
            print(f"\n❌ UNSTABLE - High std dev, model not robust")
        
        print("="*70 + "\n")
        
        self.results = fold_results
        return pd.DataFrame(fold_results)
    
    def plot_walk_forward_results(self):
        """Visualize walk-forward accuracy over time"""
        try:
            import matplotlib.pyplot as plt
            
            if not self.results:
                print("No results to plot. Run walk_forward() first.")
                return
            
            folds = [r['fold'] for r in self.results]
            accuracies = [r['accuracy'] * 100 for r in self.results]
            
            plt.figure(figsize=(12, 6))
            plt.plot(folds, accuracies, marker='o', linewidth=2, markersize=8)
            plt.axhline(y=50, color='r', linestyle='--', label='Random (50%)')
            plt.xlabel('Fold')
            plt.ylabel('Accuracy (%)')
            plt.title('Walk-Forward Validation - Accuracy Over Time')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig('../outputs/walk_forward_accuracy.png', dpi=150)
            plt.close()
            
            print("✅ Plot saved: outputs/walk_forward_accuracy.png")
        except Exception as e:
            print(f"Could not create plot: {e}")
    
    def stability_analysis(self):
        """Analyze model stability across folds"""
        if not self.results:
            print("No results. Run walk_forward() first.")
            return
        
        print("\n" + "="*70)
        print("STABILITY ANALYSIS")
        print("="*70 + "\n")
        
        accuracies = [r['accuracy'] * 100 for r in self.results]
        
        improving = 0
        declining = 0
        
        for i in range(1, len(accuracies)):
            if accuracies[i] > accuracies[i-1]:
                improving += 1
            else:
                declining += 1
        
        print(f"Performance Trend:")
        print(f"  Improving folds: {improving}")
        print(f"  Declining folds:  {declining}")
        
        if improving > declining:
            print(f"\n✅ Model improving over time")
        else:
            print(f"\n❌ Model deteriorating or unstable")
        
        # Drawdown in accuracy
        max_acc = max(accuracies)
        current_dd = max_acc - accuracies[-1]
        
        print(f"\nAccuracy Drawdown:")
        print(f"  Peak accuracy: {max_acc:.1f}%")
        print(f"  Latest:        {accuracies[-1]:.1f}%")
        print(f"  Drawdown:      {current_dd:.1f}%")
        
        print("="*70 + "\n")
