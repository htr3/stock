#!/usr/bin/env python3
"""
🔥 LIVE TRADING INTEGRATION - Complete Workflow

This script demonstrates the complete live trading workflow
with all final quant upgrades.

Usage:
python live_trading_integration.py --model_path models/trained_model.pkl --capital 100000
"""

import sys
import io

# Fix Windows encoding issues for emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import your validator
from production_validator import ProductionValidator

def load_model_and_data(model_path: str, data_path: str = None):
    """Load trained model and historical data"""
    try:
        import joblib
        model = joblib.load(model_path)
        print(f"✅ Model loaded from {model_path}")
    except:
        print("⚠️  Could not load model - using dummy")
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(n_estimators=100, random_state=42)

    # Load or generate sample data
    if data_path and Path(data_path).exists():
        df = pd.read_csv(data_path)
    else:
        print("⚠️  No data provided - generating sample")
        # Generate sample data for demonstration
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=1000, freq='D')
        df = pd.DataFrame({
            'Close': 100 + np.cumsum(np.random.randn(1000) * 0.5),
            'Open': 100 + np.cumsum(np.random.randn(1000) * 0.5),
            'High': 105 + np.cumsum(np.random.randn(1000) * 0.5),
            'Low': 95 + np.cumsum(np.random.randn(1000) * 0.5),
            'Volume': np.random.randint(1000000, 5000000, 1000),
            'returns': np.random.randn(1000) * 0.02,
            'target_direction': np.random.choice([0, 1], 1000),
            'signal': np.random.choice([0, 1], 1000, p=[0.7, 0.3])
        })

    return model, df

def simulate_live_data(df: pd.DataFrame, drift_factor: float = 0.0) -> pd.DataFrame:
    """Simulate live market data (with optional drift)"""
    # Take recent data and add some noise + drift
    live_df = df.tail(100).copy()

    # Add drift if requested
    if drift_factor > 0:
        for col in ['returns', 'Close', 'Open', 'High', 'Low']:
            if col in live_df.columns:
                live_df[col] = live_df[col] * (1 + drift_factor * np.random.randn(len(live_df)))

    return live_df

def main():
    parser = argparse.ArgumentParser(description='Live Trading Integration Demo')
    parser.add_argument('--model_path', type=str, default='models/trained_model.pkl',
                       help='Path to trained model')
    parser.add_argument('--data_path', type=str, default=None,
                       help='Path to historical data CSV')
    parser.add_argument('--capital', type=float, default=100000,
                       help='Total trading capital')
    parser.add_argument('--simulate_drift', action='store_true',
                       help='Simulate data drift for testing')
    parser.add_argument('--confidence_threshold', type=float, default=0.6,
                       help='Minimum confidence for trading')

    args = parser.parse_args()

    print("🚀 LIVE TRADING INTEGRATION - QUANT UPGRADES")
    print("="*60)

    # Step 1: Load model and historical data
    print("\n📥 STEP 1: Loading Model & Data")
    model, df = load_model_and_data(args.model_path, args.data_path)

    # Step 2: Run production validation
    print("\n🔍 STEP 2: Production Validation")
    validator = ProductionValidator(df, model=model)
    validation_results = validator.run_all_gates()

    print(f"Decision: {validation_results['decision']}")
    print(f"Confidence: {validation_results['confidence']:.1%}")
    print(f"Gates: {validation_results['passed']}/{validation_results['total']} passed")

    # Check if ready for live trading
    if "SAFE" not in validation_results['decision'] and "READY" not in validation_results['decision']:
        print("❌ NOT READY FOR LIVE TRADING")
        print("Fix validation issues first")
        return

    # Step 3: Simulate/Generate live data
    print("\n📊 STEP 3: Live Data Preparation")
    drift_factor = 0.1 if args.simulate_drift else 0.0
    live_df = simulate_live_data(df, drift_factor)

    if args.simulate_drift:
        print("🔄 Simulating data drift for testing...")

    # Step 4: Check for data drift
    print("\n🔥 STEP 4: Data Drift Detection")
    drift_result = validator.check_data_drift(live_df)

    if drift_result['drift_detected']:
        print("⚠️  DATA DRIFT DETECTED!")
        print(f"Message: {drift_result['message']}")
        print(f"Recommendation: {drift_result['recommendation']}")

        # In real trading, you might pause or re-train here
        if len(drift_result['details']) > 2:
            print("🚨 HIGH DRIFT - Consider pausing trading")
    else:
        print("✅ No drift detected - proceeding")

    # Step 5: Confidence calibration
    print("\n🎯 STEP 5: Confidence Calibration")

    # Prepare training data for calibration
    skip_cols = ['Close', 'Open', 'High', 'Low', 'Volume', 'target_direction',
                'signal', 'return', 'signal_filtered', 'signal_regime']
    feature_cols = [col for col in df.columns if col not in skip_cols]

    if len(feature_cols) > 0:
        X_train = df[feature_cols].fillna(0)
        y_train = df['target_direction']

        # Prepare live features
        X_live = live_df[feature_cols].fillna(0) if len(feature_cols) > 0 else None

        calibration_result = validator.calibrate_confidence(X_train, y_train, X_live)

        if calibration_result['calibrated_model'] is not None:
            print("✅ Model calibrated successfully")
            print(".3f")
            if calibration_result['live_calibration']:
                print(".1%")

            calibrated_model = calibration_result['calibrated_model']
        else:
            print("⚠️  Calibration failed - using original model")
            calibrated_model = model
    else:
        print("⚠️  No features found - skipping calibration")
        calibrated_model = model

    # Step 6: Generate signals with confidence
    print("\n📈 STEP 6: Signal Generation")

    # Generate predictions with confidence
    try:
        if X_live is not None and len(X_live) > 0:
            # Get calibrated probabilities
            probs = calibrated_model.predict_proba(X_live)[:, 1]
            predictions = calibrated_model.predict(X_live)

            # Create signals dataframe
            signals_df = live_df.copy()
            signals_df['signal'] = predictions
            signals_df['confidence'] = probs
            signals_df['symbol'] = 'DEMO_STOCK'  # In real trading, you'd have multiple symbols

            print(f"Generated {len(signals_df)} signals")
            print(".1%")
            print(".1%")

            # Filter by confidence
            confident_signals = signals_df[signals_df['confidence'] > args.confidence_threshold]
            print(f"Confident signals (> {args.confidence_threshold}): {len(confident_signals)}")

        else:
            print("⚠️  No live features - creating dummy signals")
            signals_df = live_df.copy()
            signals_df['signal'] = np.random.choice([0, 1], len(live_df), p=[0.7, 0.3])
            signals_df['confidence'] = np.random.beta(2, 2, len(live_df))  # Realistic confidence
            signals_df['symbol'] = 'DEMO_STOCK'

    except Exception as e:
        print(f"⚠️  Error generating signals: {e}")
        # Fallback
        signals_df = live_df.copy()
        signals_df['signal'] = np.random.choice([0, 1], len(live_df), p=[0.7, 0.3])
        signals_df['confidence'] = 0.5
        signals_df['symbol'] = 'DEMO_STOCK'

    # Step 7: Portfolio allocation
    print("\n💰 STEP 7: Portfolio Allocation")

    portfolio_plan = validator.portfolio_allocation(
        signals_df=signals_df,
        total_capital=args.capital,
        max_position_pct=0.02  # 2% max per position
    )

    print(f"Message: {portfolio_plan['message']}")
    print(f"Positions: {portfolio_plan['total_positions']}")
    print(".0f")
    print(".1%")

    # Step 8: Execution summary
    print("\n🚀 STEP 8: EXECUTION SUMMARY")
    print("="*60)

    if portfolio_plan['total_positions'] > 0:
        print("✅ TRADING SIGNALS GENERATED")
        print("\nPosition Details:")
        for pos_id, details in list(portfolio_plan['allocation'].items())[:5]:  # Show first 5
            print("6s"
                  "4d"
                  "6.2f"
                  "8.2f"
                  "5.1%")

        if len(portfolio_plan['allocation']) > 5:
            print(f"  ... and {len(portfolio_plan['allocation']) - 5} more positions")

        print("\n💡 RECOMMENDATIONS:")
        print("  • Start with paper trading first")
        print("  • Monitor performance vs backtest")
        print("  • Adjust position sizes based on confidence")
        print("  • Run daily drift checks")

        if drift_result['drift_detected']:
            print("  • ⚠️  HIGH PRIORITY: Monitor for data drift impact")

    else:
        print("⏸️  NO TRADING SIGNALS")
        print("  • No signals meet confidence threshold")
        print("  • Consider lowering threshold or improving model")

    print("\n" + "="*60)
    print("🎯 LIVE TRADING INTEGRATION COMPLETE")
    print("="*60)

    # Return results for further processing
    return {
        'validation': validation_results,
        'drift_check': drift_result,
        'calibration': calibration_result,
        'portfolio': portfolio_plan,
        'signals': signals_df if 'signals_df' in locals() else None
    }

if __name__ == "__main__":
    results = main()

    # Optional: Save results
    # import json
    # with open('live_trading_results.json', 'w') as f:
    #     json.dump(results, f, default=str)