"""
INTEGRATED VALIDATOR RUNNER

This script runs the complete validation pipeline:
1. Load data
2. Generate features
3. Train model
4. Run production validator (all 7 gates)
5. Generate report

Quick start guide.
"""

import pandas as pd
import numpy as np
import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from production_validator import ProductionValidator


def run_complete_validation(df, model, features_list=None):
    """
    Complete validation pipeline.
    
    Parameters:
    -----------
    df : DataFrame with OHLCV data + signal column
    model : Trained ML model with fit() and predict() methods
    features_list : List of feature column names (optional)
    
    Returns:
    --------
    Dictionary with complete validation results
    """
    
    print("\n" + "="*80)
    print("🚀 COMPLETE VALIDATION PIPELINE")
    print("="*80)
    
    # 1. Basic checks
    print("\n[SETUP] Validating inputs...")
    
    if df is None or len(df) == 0:
        print("  ❌ ERROR: Empty dataframe")
        return None
    
    required_cols = ['Close', 'Open', 'High', 'Low']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f"  ❌ ERROR: Missing required columns: {missing}")
        return None
    
    print(f"  ✅ Data shape: {df.shape}")
    print(f"  ✅ Date range: {df.index[0] if hasattr(df.index, '__getitem__') else 'N/A'} to {df.index[-1] if hasattr(df.index, '__getitem__') else 'N/A'}")
    
    if model is None:
        print("  ⚠️  WARNING: No model provided - skipping walk-forward validation")
    
    # 2. Run production validator
    print("\n[VALIDATOR] Running 7 mandatory gates...\n")
    
    validator = ProductionValidator(df, model=model, verbose=True)
    results = validator.run_all_gates()
    
    # 3. Generate report
    print("\n[REPORT] VALIDATION COMPLETE\n")
    
    return results


def print_decision_report(results):
    """Pretty print validation results."""
    
    if results is None:
        print("  No results to report")
        return
    
    print("="*80)
    print("📊 VALIDATION REPORT")
    print("="*80)
    
    print(f"\nFinal Decision: {results['decision']}")
    print(f"Confidence Level: {results['confidence']:.0%}")
    
    print(f"\nGates Passed: {results['passed']}")
    print(f"Gates Failed: {results['failed']}")
    print(f"Gates Skipped: {results['skipped']}")
    
    if results['failures']:
        print("\n⚠️  Failures:")
        for failure in results['failures']:
            print(f"  • {failure}")
    
    print("\n" + "="*80)
    
    if "SAFE FOR PAPER TRADING" in results['decision']:
        print("✅ RECOMMENDATION: Proceed to paper trading")
        print("\nNext steps:")
        print("  1. Deploy on paper trading account")
        print("  2. Monitor for 1-2 weeks")
        print("  3. If performance matches backtest, go live")
        
    elif "DO NOT TRADE" in results['decision']:
        print("❌ RECOMMENDATION: DO NOT TRADE")
        print("\nNext steps:")
        print("  1. Review failed gates")
        print("  2. Improve features or model")
        print("  3. Re-run validation")
        
    else:
        print("⚠️  RECOMMENDATION: Gather more data and re-validate")


# ==================== TEMPLATE USAGE ====================

if __name__ == "__main__":
    
    print("""
    ╔════════════════════════════════════════════════════════════════════════════╗
    ║                                                                            ║
    ║               🚀 PRODUCTION VALIDATOR - INTEGRATED RUNNER                  ║
    ║                                                                            ║
    ║  This script validates trading systems against 7 mandatory gates:          ║
    ║                                                                            ║
    ║  1. ✅ Alpha Validation - Beat baselines                                   ║
    ║  2. ✅ Leakage Detection - No future info                                  ║
    ║  3. ✅ Trade Frequency - Min gap between trades                            ║
    ║  4. ✅ Regime Filter - Trade only trending                                 ║
    ║  5. ✅ Walk-Forward - Stable over time                                     ║
    ║  6. ✅ Execution Costs - Profitable after slippage                         ║
    ║  7. ✅ Multi-Stock - Generalizes to new stocks                            ║
    ║                                                                            ║
    ║  NO GATE PASS = NO TRADING 🚫                                             ║
    ║                                                                            ║
    ╚════════════════════════════════════════════════════════════════════════════╝
    
    USAGE:
    ------
    1. Import validator:
       from production_validator import ProductionValidator
       
    2. Load your data and model:
       df = pd.read_csv('data.csv')
       model = load_trained_model()
       
    3. Run validation:
       validator = ProductionValidator(df, model=model)
       results = validator.run_all_gates()
       
    4. Check decision:
       if "SAFE FOR PAPER TRADING" in results['decision']:
           print("✅ Ready!")
       else:
           print("❌ Need improvements")
    
    GATE OUTCOMES:
    ---------------
    ✅ PASS    - Gate condition satisfied
    ❌ FAIL    - Gate condition failed (backs prevents trading)
    ⏭️  SKIP    - Gate skipped (insufficient data or setup)
    
    FINAL DECISION:
    ----------------
    ✅ SAFE FOR PAPER TRADING
       → All required gates pass
       → Ready for paper trading (risk-free)
       → Monitor for 1-2 weeks
    
    ❌ DO NOT TRADE
       → One or more gates failed
       → High risk of losses
       → Back to feature/model improvement
    
    ⚠️  INCONCLUSIVE
       → Not enough validation data
       → Gather more data and retry
    """)
    
    print("\n" + "="*80)
    print("📌 NEXT STEPS")
    print("="*80)
    print("""
    1. Prepare your data:
       - Ensure you have OHLCV data
       - Generate features (technical indicators)
       - Create target labels (UP/DOWN direction)
       
    2. Train your model:
       - Use any ML algorithm (XGBoost, Random Forest, etc.)
       - Model must have fit() and predict() methods
       
    3. Create signals:
       - predictions = model.predict(test_features)
       - df['signal'] = predictions
       
    4. Run validation:
       validator = ProductionValidator(df, model=model)
       results = validator.run_all_gates()
       
    5. Review results:
       - If PASS: Paper trading ready
       - If FAIL: Go back to step 1-2
    
    """)
