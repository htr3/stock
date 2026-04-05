"""
MASTER INTEGRATION GUIDE - Convert Your ML Model to Trading System

This guide shows exactly how to:
1. Load your trained model
2. Generate signals
3. Run through ALL 7 gates
4. Get final trading decision
"""

# ==================== STEP 1: SETUP ====================

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import sys
import os

# Force UTF-8 output on Windows terminals to support emoji and clear console output
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.insert(0, 'scripts')
from production_validator import ProductionValidator


# ==================== STEP 2: LOAD DATA ====================

# Example: Load your OHLCV data
df = pd.read_csv('data/processed/stock_data.csv')

# Ensure required columns exist
required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
if not all(col in df.columns for col in required_cols):
    raise Exception(f"Missing required columns: {required_cols}")

print(f"✅ Data loaded: {df.shape[0]} rows")


# ==================== STEP 3: GENERATE FEATURES ====================

# Load or generate your features
# Option A: Load pre-generated features
features_df = None
try:
    features_df = pd.read_csv('outputs/selected_features.csv', index_col=0)
    print(f"✅ Features loaded: {features_df.shape[1]} features")
except FileNotFoundError:
    print("⚠️  Features file not found - generating...")
    # You would call your feature engineering here
    # Example: features_df = feature_engineering(df)
    pass


# ==================== STEP 4: GENERATE TARGETS ====================

# Create target labels (1 = UP, 0 = DOWN)
df['target_direction'] = (df['Close'].shift(-1) > df['Close']).astype(int)

print(f"✅ Targets created: {df['target_direction'].sum()} UP moves")


# ==================== STEP 5: TRAIN MODEL ====================

# Example: Train a RandomForest (or use your pre-trained model)
model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)

# Get features and target
feature_names = []
if features_df is not None and not features_df.empty:
    selected_feature_names = features_df.index.tolist()
    feature_names = [name for name in selected_feature_names if name in df.columns]
    if len(feature_names) > 0:
        X = df[feature_names].fillna(0)
        print(f"✅ Using selected features from outputs/selected_features.csv: {len(feature_names)} columns")
    else:
        print("⚠️  selected_features.csv loaded, but no matching columns were found in df.")
        features_df = None

if features_df is None or not feature_names:
    # Fallback: create sample features from raw OHLCV data
    print("⚠️  Generating demo features from raw OHLCV data")
    df['feature_return_1'] = df['Close'].pct_change(1)
    df['feature_return_5'] = df['Close'].pct_change(5)
    df['feature_high_low_spread'] = (df['High'] - df['Low']) / df['Close']
    df['feature_close_open_diff'] = (df['Close'] - df['Open']) / df['Open']
    df['feature_volume_change'] = df['Volume'].pct_change().fillna(0)
    df['feature_volatility_3'] = df['Close'].pct_change().rolling(3).std().fillna(0)
    df['feature_volatility_10'] = df['Close'].pct_change().rolling(10).std().fillna(0)
    df['feature_ma_5'] = df['Close'].rolling(5).mean().bfill()
    df['feature_ma_10'] = df['Close'].rolling(10).mean().bfill()
    feature_names = [col for col in df.columns if col.startswith('feature_')]
    X = df[feature_names].fillna(0)
    print(f"✅ Generated {len(feature_names)} demo features from raw data")

# Align target
y = df['target_direction']

# Train (you'd normally do proper train/test split)
model.fit(X, y)

print(f"✅ Model trained on {X.shape[0]} samples")


# ==================== STEP 6: GENERATE SIGNALS ====================

# Make predictions
df['prediction'] = model.predict(X)
df['probability'] = model.predict_proba(X)[:, 1]

# Simple signal: predict UP with confidence > 60%
df['signal'] = ((df['prediction'] == 1) & (df['probability'] > 0.60)).astype(int)

print(f"✅ Signals generated: {df['signal'].sum()} total signals")


# ==================== STEP 7: CALCULATE RETURNS ====================

df['return'] = df['Close'].pct_change().shift(-1)

print(f"✅ Returns calculated")


# ==================== STEP 8: RUN PRODUCTION VALIDATOR ====================

print("\n" + "="*80)
print("🚀 RUNNING PRODUCTION VALIDATOR")
print("="*80 + "\n")

# This is the CRITICAL step
validator = ProductionValidator(df, model=model, verbose=True)
results = validator.run_all_gates()


# ==================== STEP 9: INTERPRET RESULTS ====================

print("\n" + "="*80)
print("📊 VALIDATION RESULTS")
print("="*80 + "\n")

# Extract key metrics from results
gate_status = results['gate_status']

print("Gate Results:")
for gate, status in gate_status.items():
    if status is True:
        symbol = "✅ PASS"
    elif status is False:
        symbol = "❌ FAIL"
    else:
        symbol = "⏭️  SKIP"
    print(f"  {gate:<20} {symbol}")

print(f"\nOverall Score: {results['passed']}/{results['passed'] + results['failed']} gates passed")
print(f"Confidence: {results['confidence']:.0%}")


# ==================== STEP 10: FINAL DECISION ====================

decision = results['decision']

if "SAFE FOR PAPER TRADING" in decision or "READY FOR PAPER TRADING" in decision:
    print("\n" + "🟢" * 40)
    if "SAFE FOR PAPER TRADING" in decision:
        print("✅ DECISION: SAFE FOR PAPER TRADING")
    else:
        print("🟢 DECISION: READY FOR PAPER TRADING")
    print("🟢" * 40)
    
    print("""
    Your system is ready for paper trading because:
    ✓ Model beats naive baselines
    ✓ No label leakage detected
    ✓ Consistent accuracy over time (walk-forward)
    ✓ Profitable after realistic execution costs
    
    NEXT STEPS:
    1. Deploy to paper trading account
    2. Monitor for 1-2 weeks
    3. If matches backtest, go live
    """)
    
elif "MARGINAL" in decision:
    print("\n" + "🟡" * 40)
    print("⚠️  DECISION: MARGINAL")
    print("🟡" * 40)
    print("""
    Your system is marginally tradable.
    Use very small position sizes and monitor closely.
    """)

elif "DO NOT TRADE" in decision:
    print("\n" + "🔴" * 40)
    print("❌ DECISION: DO NOT TRADE YET")
    print("🔴" * 40)
    
    print("\nReasons:")
    for failure in results['failures']:
        print(f"  • {failure}")
    
    print("""
    NEXT STEPS:
    1. Review failed gates
    2. Improve features or model
    3. Re-run validation
    """)

else:
    print("\n" + "🟡" * 40)
    print("⚠️  DECISION: INCONCLUSIVE")
    print("🟡" * 40)
    print("""
    Need more validation data.
    """)


# ==================== OPTIONAL: DETAILED GATE ANALYSIS ====================

print("\n" + "="*80)
print("🔍 DETAILED GATE BREAKDOWN")
print("="*80 + "\n")

gates_explained = {
    'alpha': """
    GATE 1: Alpha Validation
    Question: Does your model beat simple baselines?
    What it checks: 
      • Strategy return vs Buy & Hold return
      • Sharpe ratio (risk-adjusted returns)
      • Comparison with Always UP and Random strategies
    Success: Returns > Buy & Hold AND Sharpe > 0.5
    Why it matters: Proves you have actual edge, not luck
    """,
    
    'leakage': """
    GATE 2: Leakage Detection
    Question: Do features contain future information?
    What it checks:
      • Any "shift(-" operations (looking into future)
      • Rolling means that include current candle
      • Model performs too well on training data
    Success: No future lookahead, accuracy 50-65%
    Why it matters: Prevents overfitting to "magic" features
    """,
    
    'trade_frequency': """
    GATE 3: Trade Frequency Control
    Question: Is the model overtrading?
    What it checks:
      • Minimum 3-candle gap between trades
      • Prevents noise trading
      • Reduces transaction costs
    Success: Trades reduced, quality improved
    Why it matters: Each trade has costs; fewer = better
    """,
    
    'regime_filter': """
    GATE 4: Regime Detection
    Question: Does model only trade when market is favorable?
    What it checks:
      • Market is TRENDING vs SIDEWAYS
      • Uses EMA9/EMA21 divergence + volume
      • Skips trades in choppy markets
    Success: Return improves or stays same
    Why it matters: Trending markets are easier to predict
    """,
    
    'walk_forward': """
    GATE 5: Walk-Forward Validation
    Question: Is model stable over time?
    What it checks:
      • Accuracy on rolling windows (past→future)
      • NOT just single 80/20 split
      • Model doesn't deteriorate
    Success: Accuracy 50-65%, std dev < 5%
    Why it matters: Proves edge works in real market conditions
    """,
    
    'execution': """
    GATE 6: Execution Costs
    Question: Is strategy profitable after real costs?
    What it checks:
      • Slippage: 0.05% per entry/exit
      • Commission: 0.05% per order
      • Latency: 1 candle delay
    Success: Return > 50% of ideal
    Why it matters: Backtest is perfect; real world isn't
    """,
    
    'multi_stock': """
    GATE 7: Multi-Stock Generalization
    Question: Does model work on different stocks?
    What it checks:
      • Accuracy on unseen stocks (if available)
      • Model generalizes beyond training set
    Success: Accuracy > 52% on all stocks
    Why it matters: Proves skill, not luck on single stock
    """
}

for gate_name, explanation in gates_explained.items():
    status = gate_status.get(gate_name)
    if status is not None:
        print(explanation)
        print(f"Status: {status}\n")


# ==================== OPTIONAL: SENSITIVITY ANALYSIS ====================

print("\n" + "="*80)
print("📈 SENSITIVITY ANALYSIS")
print("="*80 + "\n")

print("""
How confident should you be in these results?

Variables that could change results:
1. Market regime (bull vs bear)
2. Stock selection (highly volatile vs stable)
3. Time period (recent vs historical)
4. Feature engineering (are features predictive?)
5. Model hyperparameters (overfitting?)

If you change any of these, re-run the validator!
""")


# ==================== SUMMARY ====================

print("\n" + "="*80)
print("✅ VALIDATION COMPLETE")
print("="*80)

print(f"""
Final Decision: {decision}
Confidence: {results['confidence']:.0%}

Gates Passed: {results['passed']}
Gates Failed: {results['failed']}
Gates Skipped: {results['skipped']}

Ready to proceed? Check the decision above.
""")
