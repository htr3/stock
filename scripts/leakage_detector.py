"""
Label Leakage Detector

Detects if any features contain future information that wouldn't be available
at prediction time. This is critical for model integrity.

Common leakage:
- Rolling mean including current candle
- Improper shift/lag operations
- Volume aggregated with future candles
- Close price vs future close in feature
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


class LeakageDetector:
    """Detect label leakage in features"""
    
    def __init__(self, features_df, target_series, threshold=0.75):
        """
        Args:
            features_df: Feature matrix
            target_series: Target variable
            threshold: High accuracy (>threshold) suggests leakage
        """
        self.features = features_df
        self.target = target_series
        self.threshold = threshold
        self.suspicious_features = []
        self.model = None
    
    def test_feature_importance_leakage(self):
        """Test if any single feature has suspiciously high predictive power"""
        print("\n" + "="*70)
        print("LEAKAGE DETECTION - FEATURE IMPORTANCE TEST")
        print("="*70 + "\n")
        
        suspicious = []
        
        for feature in self.features.columns:
            X = self.features[[feature]].fillna(0)
            y = self.target
            
            # Quick train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, random_state=42
            )
            
            clf = RandomForestClassifier(n_estimators=10, random_state=42, verbose=0)
            clf.fit(X_train, y_train)
            score = clf.score(X_test, y_test)
            
            print(f"{feature:30s} → Accuracy: {score*100:.1f}%", end="")
            
            if score > self.threshold:
                print(" ⚠️  SUSPICIOUS LEAKAGE")
                suspicious.append({
                    'feature': feature,
                    'accuracy': score,
                    'risk': 'HIGH'
                })
            else:
                print(" ✓")
        
        print("\n" + "="*70)
        if suspicious:
            print("⚠️  LEAKAGE DETECTED IN THESE FEATURES:")
            print("="*70)
            for item in suspicious:
                print(f"  {item['feature']} - {item['accuracy']*100:.1f}%")
            print("\n❌ These features likely contain future information!")
            print("   Remove them before retraining.")
        else:
            print("✅ NO OBVIOUS LEAKAGE DETECTED")
            print("="*70)
        
        return suspicious
    
    def test_train_test_accuracy_gap(self):
        """Huge gap between train and test accuracy suggests leakage"""
        print("\n" + "="*70)
        print("LEAKAGE DETECTION - TRAIN/TEST GAP TEST")
        print("="*70 + "\n")
        
        X_train, X_test, y_train, y_test = train_test_split(
            self.features, self.target, test_size=0.3, random_state=42
        )
        
        clf = RandomForestClassifier(n_estimators=50, random_state=42, verbose=0)
        clf.fit(X_train, y_train)
        
        train_accuracy = clf.score(X_train, y_train)
        test_accuracy = clf.score(X_test, y_test)
        
        print(f"Training Accuracy: {train_accuracy*100:.1f}%")
        print(f"Test Accuracy:     {test_accuracy*100:.1f}%")
        print(f"Gap:               {(train_accuracy - test_accuracy)*100:.1f}%\n")
        
        if train_accuracy > 0.90 or test_accuracy > 0.75:
            print("⚠️  WARNING: Very high accuracy suggests leakage!")
            print("   Expected range: 50-60% for financial prediction")
        else:
            print("✅ Accuracies in normal range")
        
        print("="*70)
        
        return {
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'gap': train_accuracy - test_accuracy
        }
    
    def check_shift_operations(self, df_original):
        """Verify shift operations don't include current/future data"""
        print("\n" + "="*70)
        print("LEAKAGE DETECTION - SHIFT OPERATIONS TEST")
        print("="*70 + "\n")
        
        issues = []
        
        # Check for common leakage patterns
        print("Checking for common leakage patterns...\n")
        
        # Pattern 1: Current close in features (should be lagged)
        if 'close' in self.features.columns or 'Close' in self.features.columns:
            print("⚠️  WARNING: Current close found in features")
            print("   Current close is part of label (target)")
            issues.append("Current close should not be in features")
        
        # Pattern 2: Check lag operations
        close_cols = [c for c in self.features.columns if 'close' in c.lower()]
        for col in close_cols:
            if 'lag' not in col.lower() and 'prev' not in col.lower():
                print(f"⚠️  {col} - unclear if properly lagged")
                issues.append(f"{col} - check lag operation")
        
        if not issues:
            print("✅ No obvious shift/lag issues detected")
        
        print("="*70)
        return issues
    
    def synthetic_leakage_test(self):
        """Test with synthetic target - model should randomly predict (~50%)"""
        print("\n" + "="*70)
        print("LEAKAGE DETECTION - SYNTHETIC TARGET TEST")
        print("="*70 + "\n")
        
        # Create random target
        synthetic_target = np.random.randint(0, 2, len(self.target))
        
        X_train, X_test, y_train, y_test = train_test_split(
            self.features, synthetic_target, test_size=0.3, random_state=42
        )
        
        clf = RandomForestClassifier(n_estimators=50, random_state=42, verbose=0)
        clf.fit(X_train, y_train)
        
        accuracy = clf.score(X_test, y_test)
        
        print(f"Model trained on RANDOM target")
        print(f"Test Accuracy: {accuracy*100:.1f}%\n")
        
        if accuracy > 0.55:
            print("⚠️  WARNING: Model still predicts random target!")
            print("   This should be ~50% - suggests severe leakage")
        else:
            print("✅ Model cannot predict random target - no leakage")
        
        print("="*70)
        
        return accuracy
    
    def comprehensive_report(self, df_original=None):
        """Run all leakage tests and provide comprehensive report"""
        print("\n\n")
        print("🔍 " + "="*66 + " 🔍")
        print("   COMPREHENSIVE LEAKAGE DETECTION REPORT")
        print("🔍 " + "="*66 + " 🔍")
        
        # Test 1: Feature importance leakage
        suspicious = self.test_feature_importance_leakage()
        
        # Test 2: Train/test gap
        gap_results = self.test_train_test_accuracy_gap()
        
        # Test 3: Shift operations
        if df_original is not None:
            shift_issues = self.check_shift_operations(df_original)
        else:
            shift_issues = []
        
        # Test 4: Synthetic leakage
        synthetic_acc = self.synthetic_leakage_test()
        
        # Final verdict
        print("\n\n")
        print("="*70)
        print("FINAL VERDICT")
        print("="*70 + "\n")
        
        risk_level = 'LOW'
        
        if suspicious:
            risk_level = 'CRITICAL'
            print("🔴 CRITICAL RISK - Definite leakage detected")
            print("   Action: Remove suspicious features and retrain\n")
        elif gap_results['train_accuracy'] > 0.80 or gap_results['test_accuracy'] > 0.70:
            risk_level = 'HIGH'
            print("🟠 HIGH RISK - Unusually high accuracy")
            print("   Action: Review features carefully\n")
        elif synthetic_acc > 0.55:
            risk_level = 'HIGH'
            print("🟠 HIGH RISK - Predicts random target")
            print("   Action: Investigate feature generation\n")
        elif shift_issues:
            risk_level = 'MEDIUM'
            print("🟡 MEDIUM RISK - Potential shift issues")
            print("   Action: Verify lag operations\n")
        else:
            print("🟢 LOW RISK - No obvious leakage detected")
            print("   Status: Model appears clean\n")
        
        print(f"Overall Risk Level: {risk_level}")
        print("="*70 + "\n")
        
        return {
            'risk_level': risk_level,
            'suspicious_features': suspicious,
            'train_test_gap': gap_results,
            'shift_issues': shift_issues,
            'synthetic_accuracy': synthetic_acc
        }
