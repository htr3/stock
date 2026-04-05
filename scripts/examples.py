"""
Quick start and usage examples
"""

# ============================================================================
# EXAMPLE 1: Generate Sample Data & Run Complete Pipeline
# ============================================================================

def example_complete_pipeline():
    """Run the complete ML pipeline with sample data"""
    
    from generate_sample_data import generate_sample_stock_data
    from main import StockPricePredictionPipeline
    
    # Step 1: Generate sample data
    print("Step 1: Generating sample stock data...")
    df = generate_sample_stock_data(
        filename='sample_stock_data.csv',
        num_candles=2000,
        initial_price=100.0,
        trend='random'
    )
    
    # Step 2: Run the complete pipeline
    print("\nStep 2: Running ML pipeline...")
    pipeline = StockPricePredictionPipeline('sample_stock_data.csv')
    results_df, best_model_name = pipeline.run_complete_pipeline('sample_stock_data.csv')
    
    # Step 3: View results
    print("\nStep 3: Model comparison results:")
    print(results_df)
    print(f"\n✓ Best model: {best_model_name}")
    
    return pipeline, results_df


# ============================================================================
# EXAMPLE 2: Use Your Own Stock Data
# ============================================================================

def example_with_own_data(csv_file):
    """Run pipeline with your own stock data"""
    
    from main import StockPricePredictionPipeline
    
    pipeline = StockPricePredictionPipeline(csv_file)
    results_df, best_model_name = pipeline.run_complete_pipeline(csv_file)
    
    return pipeline, results_df


# ============================================================================
# EXAMPLE 3: Make Predictions on New Data
# ============================================================================

def example_make_predictions():
    """Load model and make predictions on new data"""
    
    import joblib
    import pandas as pd
    from feature_engineering import FeatureEngineer
    
    # Load the trained model (adjust filename to your saved model)
    model = joblib.load('best_model_xgboost_20240101_120000.pkl')
    
    # Load new data
    new_data = pd.read_csv('new_stock_data.csv')
    
    # Generate features
    engineer = FeatureEngineer(new_data)
    features = engineer.generate_all_features()
    
    # Make predictions
    predictions = model.predict(features)  # 1 = UP, 0 = DOWN
    probabilities = model.predict_proba(features)  # [prob_down, prob_up]
    
    # Create results dataframe
    results = pd.DataFrame({
        'Date': new_data['Date'],
        'Close': new_data['Close'],
        'Prediction': predictions,
        'Prob_Down': probabilities[:, 0],
        'Prob_Up': probabilities[:, 1],
        'Confidence': probabilities.max(axis=1)
    })
    
    # Filter high confidence predictions
    high_confidence = results[results['Confidence'] > 0.65]
    
    print("\nHigh Confidence Predictions (>65%):")
    print(high_confidence)
    
    return results


# ============================================================================
# EXAMPLE 4: Custom Feature Exploration
# ============================================================================

def example_explore_features():
    """Explore and analyze generated features"""
    
    import pandas as pd
    import matplotlib.pyplot as plt
    import os
    from feature_engineering import FeatureEngineer
    from target_variable import TargetVariable
    
    # Load data
    df = pd.read_csv('stock_data.csv')
    
    # Generate features
    engineer = FeatureEngineer(df)
    features = engineer.generate_all_features()
    
    # Generate targets
    targets = TargetVariable.create_all_targets(df)
    
    # Analyze correlation with target
    combined = pd.concat([features, targets[['target_direction']]], axis=1)
    correlation = combined.corr()['target_direction'].sort_values(ascending=False)
    
    print("\nTop 20 Features Correlated with UP Movement:")
    print(correlation.head(20))
    
    # Plot correlation
    correlation.head(20).plot(kind='barh', figsize=(12, 8))
    plt.title('Feature Correlation with Stock Price Movement (UP=1)')
    plt.xlabel('Correlation Coefficient')
    plt.tight_layout()
    plt.savefig(os.path.join('..', 'outputs', 'plots', 'feature_correlation.png'))
    plt.show()
    
    return correlation


# ============================================================================
# EXAMPLE 5: Train Custom Model with Specific Parameters
# ============================================================================

def example_custom_model():
    """Train a single model with custom parameters"""
    
    import pandas as pd
    from feature_engineering import FeatureEngineer
    from target_variable import TargetVariable
    from data_preparation import DataPipeline
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, f1_score, classification_report
    
    # Load and prepare data
    df = pd.read_csv('stock_data.csv')
    engineer = FeatureEngineer(df)
    features = engineer.generate_all_features()
    targets = TargetVariable.create_all_targets(df)
    
    # Prepare data
    pipeline = DataPipeline(features, targets)
    X_train, X_test, y_train, y_test = pipeline.prepare(
        target_col='target_direction',
        remove_outliers=True,
        handle_imbalance=True,
        test_size=0.2
    )
    
    # Train custom Random Forest
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print(f"\nCustom Random Forest Results:")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"F1-Score: {f1:.4f}")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    return model


# ============================================================================
# EXAMPLE 6: Backtest on Historical Data
# ============================================================================

def example_backtest():
    """Simple backtest of predictions"""
    
    import joblib
    import pandas as pd
    from feature_engineering import FeatureEngineer
    
    # Load model
    model = joblib.load('best_model_xgboost_20240101_120000.pkl')
    
    # Load data
    df = pd.read_csv('stock_data.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Generate features
    engineer = FeatureEngineer(df)
    features = engineer.generate_all_features()
    
    # Make predictions
    predictions = model.predict(features)
    probabilities = model.predict_proba(features)
    
    # Calculate actual results
    df['Next_Close'] = df['Close'].shift(-1)
    df['Actual_Direction'] = (df['Next_Close'] > df['Close']).astype(int)
    df['Predicted_Direction'] = predictions
    df['Confidence'] = probabilities.max(axis=1)
    
    # Filter high confidence trades
    df['Trade'] = df['Predicted_Direction'] * (df['Confidence'] > 0.65)
    
    # Calculate returns
    df['Trade_Return'] = (df['Next_Close'] - df['Close']) / df['Close']
    df['Strategy_Return'] = df['Trade'] * df['Trade_Return']
    
    # Performance metrics
    total_trades = (df['Trade'] != 0).sum()
    winning_trades = ((df['Trade'] == 1) & (df['Trade_Return'] > 0)).sum()
    losing_trades = ((df['Trade'] == 1) & (df['Trade_Return'] < 0)).sum()
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    
    cumulative_return = (1 + df['Strategy_Return']).cumprod() - 1
    
    print(f"\nBacktest Results:")
    print(f"Total Trades: {total_trades}")
    print(f"Winning Trades: {winning_trades}")
    print(f"Losing Trades: {losing_trades}")
    print(f"Win Rate: {win_rate:.2%}")
    print(f"Cumulative Return: {cumulative_return.iloc[-1]:.2%}")
    print(f"Avg Trade Return: {df['Trade_Return'].mean():.4f}")
    
    return df


# ============================================================================
# Run Examples
# ============================================================================

if __name__ == '__main__':
    
    import sys
    
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║   Stock Price Prediction ML Model - Usage Examples              ║
    ║   Predict 10-min UP/DOWN movements                              ║
    ╚══════════════════════════════════════════════════════════════════╝
    
    Choose an example to run:
    1. Complete pipeline (generate sample data + train models)
    2. Use your own stock data
    3. Make predictions on new data
    4. Explore feature importance
    5. Train custom model
    6. Backtest strategy
    """)
    
    choice = input("Enter example number (1-6): ").strip()
    
    try:
        if choice == '1':
            print("\n" + "="*70)
            print("Running Example 1: Complete Pipeline")
            print("="*70)
            pipeline, results = example_complete_pipeline()
            
        elif choice == '2':
            csv_file = input("Enter CSV file path: ").strip()
            print("\n" + "="*70)
            print(f"Running Example 2: Custom Data ({csv_file})")
            print("="*70)
            pipeline, results = example_with_own_data(csv_file)
            
        elif choice == '3':
            print("\n" + "="*70)
            print("Running Example 3: Make Predictions")
            print("="*70)
            results = example_make_predictions()
            
        elif choice == '4':
            print("\n" + "="*70)
            print("Running Example 4: Explore Features")
            print("="*70)
            correlation = example_explore_features()
            
        elif choice == '5':
            print("\n" + "="*70)
            print("Running Example 5: Custom Model Training")
            print("="*70)
            model = example_custom_model()
            
        elif choice == '6':
            print("\n" + "="*70)
            print("Running Example 6: Backtest")
            print("="*70)
            df = example_backtest()
            
        else:
            print("Invalid choice!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
