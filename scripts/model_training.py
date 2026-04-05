"""
PHASE 6: Model Training and Evaluation
Train multiple ML models for stock price prediction
"""

import pandas as pd
import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                             f1_score, confusion_matrix, classification_report,
                             roc_auc_score, roc_curve)
import xgboost as xgb
import lightgbm as lgb
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime


class ModelTrainer:
    """Train and evaluate ML models"""
    
    def __init__(self):
        self.models = {}
        self.results = {}
        self.predictions = {}
    
    def train_logistic_regression(self, X_train, y_train, X_test, y_test):
        """Logistic Regression baseline"""
        print("\n" + "="*50)
        print("Training Logistic Regression...")
        print("="*50)
        
        model = LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        self.models['logistic_regression'] = model
        self._evaluate_model('logistic_regression', y_test, y_pred, y_pred_proba)
    
    def train_random_forest(self, X_train, y_train, X_test, y_test):
        """Random Forest"""
        print("\n" + "="*50)
        print("Training Random Forest...")
        print("="*50)
        
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        self.models['random_forest'] = model
        self._evaluate_model('random_forest', y_test, y_pred, y_pred_proba)
        
        # Feature importance
        self._plot_feature_importance(model, X_train, 'Random Forest')
    
    def train_gradient_boosting(self, X_train, y_train, X_test, y_test):
        """Gradient Boosting"""
        print("\n" + "="*50)
        print("Training Gradient Boosting...")
        print("="*50)
        
        model = GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            min_samples_split=10,
            min_samples_leaf=5,
            subsample=0.8,
            random_state=42
        )
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        self.models['gradient_boosting'] = model
        self._evaluate_model('gradient_boosting', y_test, y_pred, y_pred_proba)
        
        # Feature importance
        self._plot_feature_importance(model, X_train, 'Gradient Boosting')
    
    def train_xgboost(self, X_train, y_train, X_test, y_test):
        """XGBoost"""
        print("\n" + "="*50)
        print("Training XGBoost...")
        print("="*50)
        
        model = xgb.XGBClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            min_child_weight=1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            eval_metric='logloss'
        )
        model.fit(X_train, y_train, 
                 eval_set=[(X_test, y_test)],
                 verbose=False)
        
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        self.models['xgboost'] = model
        self._evaluate_model('xgboost', y_test, y_pred, y_pred_proba)
        
        # Feature importance
        self._plot_feature_importance(model, X_train, 'XGBoost')
    
    def train_lightgbm(self, X_train, y_train, X_test, y_test):
        """LightGBM"""
        print("\n" + "="*50)
        print("Training LightGBM...")
        print("="*50)
        
        model = lgb.LGBMClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            num_leaves=31,
            min_child_samples=20,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train,
                 eval_set=[(X_test, y_test)])
        
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        self.models['lightgbm'] = model
        self._evaluate_model('lightgbm', y_test, y_pred, y_pred_proba)
        
        # Feature importance
        self._plot_feature_importance(model, X_train, 'LightGBM')
    
    def _evaluate_model(self, name, y_test, y_pred, y_pred_proba):
        """Evaluate model performance"""
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        try:
            auc = roc_auc_score(y_test, y_pred_proba)
        except:
            auc = 0.0
        
        self.results[name] = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'auc': auc
        }
        
        self.predictions[name] = {
            'y_pred': y_pred,
            'y_pred_proba': y_pred_proba,
            'y_test': y_test
        }
        
        print(f"\n✓ {name.upper()} Results:")
        print(f"  Accuracy:  {accuracy:.4f}")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall:    {recall:.4f}")
        print(f"  F1-Score:  {f1:.4f}")
        print(f"  AUC:       {auc:.4f}")
        print(f"\nConfusion Matrix:\n{confusion_matrix(y_test, y_pred)}")
    
    def _plot_feature_importance(self, model, X_train, model_name):
        """Plot feature importance"""
        
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            feature_names = X_train.columns
            
            # Get top 20 features
            indices = np.argsort(importances)[-20:]
            
            plt.figure(figsize=(10, 8))
            plt.barh(range(len(indices)), importances[indices])
            plt.yticks(range(len(indices)), feature_names[indices])
            plt.xlabel('Feature Importance')
            plt.title(f'{model_name} - Top 20 Important Features')
            plt.tight_layout()
            plt.savefig(os.path.join('..', 'outputs', 'plots', f'feature_importance_{model_name.lower().replace(" ", "_")}.png'), dpi=150)
            plt.close()
            
            print(f"\n✓ Feature importance plot saved!")
    
    def compare_models(self):
        """Compare all trained models"""
        print("\n" + "="*50)
        print("MODEL COMPARISON")
        print("="*50)
        
        results_df = pd.DataFrame(self.results).T
        results_df = results_df.sort_values('f1', ascending=False)
        
        print("\n" + results_df.to_string())
        
        # Plot comparison
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        for idx, metric in enumerate(['accuracy', 'precision', 'recall', 'f1']):
            ax = axes[idx // 2, idx % 2]
            results_df[metric].plot(kind='bar', ax=ax, color='steelblue')
            ax.set_title(f'{metric.upper()} Comparison')
            ax.set_ylabel('Score')
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join('..', 'outputs', 'plots', 'model_comparison.png'), dpi=150)
        plt.close()
        
        print("\n✓ Model comparison plot saved!")
        
        return results_df
    
    def save_best_model(self):
        """Save the best model"""
        
        best_model_name = max(self.results, key=lambda x: self.results[x]['f1'])
        best_model = self.models[best_model_name]
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'best_model_{best_model_name}_{timestamp}.pkl'
        filepath = os.path.join('..', 'models', 'saved', filename)
        
        joblib.dump(best_model, filepath)
        print(f"\n✓ Best model saved: {filepath}")
        
        return best_model_name, filename
