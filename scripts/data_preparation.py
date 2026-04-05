"""
PHASE 5: Data Preparation and Cleaning
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split


class DataPreparation:
    """Prepare data for ML model training"""
    
    @staticmethod
    def remove_nan_rows(features: pd.DataFrame, targets: pd.DataFrame) -> tuple:
        """Remove rows with NaN values"""
        # Combine features and targets to handle NaN consistently
        combined = pd.concat([features, targets], axis=1)
        
        # Drop NaN rows
        combined_clean = combined.dropna()
        
        # Split back
        feature_cols = features.columns
        target_cols = targets.columns
        
        features_clean = combined_clean[feature_cols]
        targets_clean = combined_clean[target_cols]
        
        print(f"Removed {len(combined) - len(combined_clean)} rows with NaN values")
        print(f"Remaining rows: {len(combined_clean)}")
        
        return features_clean, targets_clean
    
    @staticmethod
    def remove_outliers(X: pd.DataFrame, method: str = 'iqr', threshold: float = 3.0) -> pd.DataFrame:
        """Remove outliers using IQR or Z-score"""
        X_clean = X.copy()
        
        if method == 'iqr':
            Q1 = X_clean.quantile(0.25)
            Q3 = X_clean.quantile(0.75)
            IQR = Q3 - Q1
            
            # Remove rows where any value is outside 1.5*IQR range
            mask = ~((X_clean < (Q1 - 1.5 * IQR)) | (X_clean > (Q3 + 1.5 * IQR))).any(axis=1)
            X_clean = X_clean[mask]
            
        elif method == 'zscore':
            mask = ~((np.abs(X_clean) > threshold).any(axis=1))
            X_clean = X_clean[mask]
        
        print(f"Removed {len(X) - len(X_clean)} outlier rows")
        return X_clean
    
    @staticmethod
    def scale_features(X_train: pd.DataFrame, X_test: pd.DataFrame, 
                      scaler_type: str = 'standard') -> tuple:
        """Scale features using StandardScaler or RobustScaler"""
        
        if scaler_type == 'standard':
            scaler = StandardScaler()
        else:
            scaler = RobustScaler()
        
        X_train_scaled = pd.DataFrame(
            scaler.fit_transform(X_train),
            columns=X_train.columns,
            index=X_train.index
        )
        
        X_test_scaled = pd.DataFrame(
            scaler.transform(X_test),
            columns=X_test.columns,
            index=X_test.index
        )
        
        return X_train_scaled, X_test_scaled, scaler
    
    @staticmethod
    def split_data(X: pd.DataFrame, y: pd.Series, 
                   test_size: float = 0.2, random_state: int = 42,
                   time_series: bool = True) -> tuple:
        """
        Split data into train and test sets
        
        time_series=True: Split by time (no future leakage)
        time_series=False: Random split (for cross-validation)
        """
        
        if time_series:
            # Time-series split: no future leakage
            split_point = int(len(X) * (1 - test_size))
            
            X_train = X.iloc[:split_point]
            X_test = X.iloc[split_point:]
            
            y_train = y.iloc[:split_point]
            y_test = y.iloc[split_point:]
            
            print(f"Time-series split: {len(X_train)} train, {len(X_test)} test")
            
        else:
            # Random split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )
            print(f"Random split: {len(X_train)} train, {len(X_test)} test")
        
        return X_train, X_test, y_train, y_test
    
    @staticmethod
    def handle_class_imbalance(X_train: pd.DataFrame, y_train: pd.Series,
                              method: str = 'undersample') -> tuple:
        """Handle class imbalance"""
        
        value_counts = y_train.value_counts()
        print(f"Class distribution before: {dict(value_counts)}")
        
        if method == 'undersample':
            # Keep minority class size
            min_class_size = value_counts.min()
            
            X_balanced = pd.DataFrame()
            y_balanced = pd.Series([], dtype=y_train.dtype)
            
            for class_label in y_train.unique():
                class_indices = y_train[y_train == class_label].index
                sample_indices = np.random.choice(class_indices, min_class_size, replace=False)
                
                X_balanced = pd.concat([X_balanced, X_train.loc[sample_indices]])
                y_balanced = pd.concat([y_balanced, y_train[sample_indices]])
            
            # Shuffle
            shuffle_idx = np.random.permutation(len(X_balanced))
            X_balanced = X_balanced.iloc[shuffle_idx].reset_index(drop=True)
            y_balanced = y_balanced.iloc[shuffle_idx].reset_index(drop=True)
            
        elif method == 'oversample':
            # Oversample minority class
            max_class_size = value_counts.max()
            
            X_balanced = pd.DataFrame()
            y_balanced = pd.Series([], dtype=y_train.dtype)
            
            for class_label in y_train.unique():
                class_indices = y_train[y_train == class_label].index
                sample_indices = np.random.choice(class_indices, max_class_size, replace=True)
                
                X_balanced = pd.concat([X_balanced, X_train.loc[sample_indices]])
                y_balanced = pd.concat([y_balanced, y_train[sample_indices]])
            
            # Shuffle
            shuffle_idx = np.random.permutation(len(X_balanced))
            X_balanced = X_balanced.iloc[shuffle_idx].reset_index(drop=True)
            y_balanced = y_balanced.iloc[shuffle_idx].reset_index(drop=True)
        
        print(f"Class distribution after: {dict(y_balanced.value_counts())}")
        return X_balanced, y_balanced


class DataPipeline:
    """Complete data preparation pipeline"""
    
    def __init__(self, features: pd.DataFrame, targets: pd.DataFrame):
        self.features = features
        self.targets = targets
        self.scaler = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
    
    def prepare(self, target_col: str = 'target_direction', 
                remove_outliers: bool = True,
                handle_imbalance: bool = True,
                test_size: float = 0.2) -> tuple:
        """
        Complete preparation pipeline
        """
        print("Starting data preparation pipeline...")
        
        # Select target
        y = self.targets[target_col]
        X = self.features.copy()
        
        # Remove NaN
        print("\n1. Removing NaN values...")
        mask = ~(X.isna().any(axis=1) | y.isna())
        X = X[mask]
        y = y[mask]
        
        # Remove outliers
        if remove_outliers:
            print("\n2. Removing outliers...")
            X_clean = DataPreparation.remove_outliers(X, method='iqr')
            valid_indices = X_clean.index
            X = X.loc[valid_indices]
            y = y.loc[valid_indices]
        
        # Train-test split
        print("\n3. Splitting data (time-series aware)...")
        self.X_train, self.X_test, self.y_train, self.y_test = \
            DataPreparation.split_data(X, y, test_size=test_size, time_series=True)
        
        # Handle class imbalance
        if handle_imbalance:
            print("\n4. Handling class imbalance...")
            self.X_train, self.y_train = \
                DataPreparation.handle_class_imbalance(
                    self.X_train, self.y_train, method='undersample'
                )
        
        # Scale features
        print("\n5. Scaling features...")
        self.X_train, self.X_test, self.scaler = \
            DataPreparation.scale_features(self.X_train, self.X_test)
        
        print("\n[OK] Data preparation complete!")
        print(f"Training set: {len(self.X_train)} samples, {self.X_train.shape[1]} features")
        print(f"Test set: {len(self.X_test)} samples")
        
        return self.X_train, self.X_test, self.y_train, self.y_test
