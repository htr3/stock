# ⚡ Quick Start - Production Validator in 10 Lines

## The Absolute Minimum

```python
from production_validator import ProductionValidator
import pandas as pd

df = pd.read_csv('data.csv')
model = load_your_model()

validator = ProductionValidator(df, model=model)
results = validator.run_all_gates()

if "SAFE FOR PAPER TRADING" in results['decision']:
    print("✅ Deploy!")
else:
    print(f"❌ Fix: {results['failures']}")
```

That's it. That's the whole thing.

---

## What You Need

### Dataframe (df)
Must have these columns:
```
Open, High, Low, Close, Volume  (OHLCV data)
signal                          (0 or 1, your predictions)
target_direction               (0 or 1, labels)
return                         (price change next period)
```

### Model
Any ML model with:
```python
model.fit(X, y)
model.predict(X)
model.predict_proba(X)  # optional, for confidence
```

Can be:
- RandomForest
- XGBoost
- LightGBM
- LogisticRegression
- Neural Network
- Anything sklearn-compatible

---

## What You Get

```
GATE RESULTS:
├─ ✅ PASS   → Gate passed
├─ ❌ FAIL   → Gate failed (BLOCKS trading)
└─ ⏭️  SKIP   → Gate skipped (insufficient data)

FINAL DECISION:
├─ ✅ SAFE FOR PAPER TRADING      → Deploy
├─ ❌ DO NOT TRADE                 → Fix model
└─ ⚠️  INCONCLUSIVE                → Get more data
```

---

## Example Usage Patterns

### Pattern 1: One-Liner Check
```python
decision = ProductionValidator(df, model).run_all_gates()['decision']
print(decision)
```

### Pattern 2: Detailed Review
```python
validator = ProductionValidator(df, model, verbose=True)
results = validator.run_all_gates()

print(f"Passed: {results['passed']}")
print(f"Failed: {results['failed']}")
print(f"Confidence: {results['confidence']:.0%}")

if results['failed'] > 0:
    print(f"Issues: {results['failures']}")
```

### Pattern 3: Conditional Deployment
```python
results = ProductionValidator(df, model).run_all_gates()

if results['failed'] == 0 and results['passed'] >= 4:
    deploy_to_paper_trading()
elif results['failed'] > 0:
    alert_user(f"Failed gates: {results['failures']}")
    go_back_to_tuning()
else:
    collect_more_data()
```

---

## Gate Reference (Quick)

| Gate | Tests | Pass Criteria |
|------|-------|---------------|
| Alpha | Beats baselines | Return > Buy & Hold |
| Leakage | No future data | No shift(-), acc ~55% |
| Frequency | Prevents overtrading | Min 3-candle gap |
| Regime | Market-aware | Better in trends |
| Walk-Forward | Time-series stability | Acc 50-65%, std<5% |
| Execution | Real costs matter | Profitable after costs |
| Multi-Stock | Generalizes | >52% on all stocks |

**Result**: All pass = ✅ Trade. Any fail = ❌ Don't trade.

---

## Real Example

```python
# Load data
df = pd.read_csv('AAPL_data.csv')

# Train model on AAPL (XGBoost)
from xgboost import XGBClassifier
model = XGBClassifier(n_estimators=100)
model.fit(features, targets)

# Predict
df['signal'] = model.predict(features)
df['return'] = df['Close'].pct_change().shift(-1)

# Validate
validator = ProductionValidator(df, model=model)
results = validator.run_all_gates()

# Deploy if ready
if "SAFE FOR PAPER TRADING" in results['decision']:
    connect_to_broker()
    deploy_strategy()
    print("✅ Trading live!")
else:
    print(f"❌ Validation failed: {results['failures']}")
    improve_features()
```

---

## Common Issues & Fixes

### Issue: "Missing required columns"
**Fix**: Ensure df has Open, High, Low, Close, Volume, signal, target_direction, return

### Issue: "Gate 2 (Leakage) Failed"
**Fix**: Check for shift(-x) or future lookback in features

### Issue: "Gate 5 (Walk-Forward) Failed"
**Fix**: Model accuracy is dropping - may be overfitting

### Issue: "Gate 6 (Execution) Failed"
**Fix**: Margin too thin; costs eliminate profit

### Issue: All gates pass but low confidence (< 80%)
**Fix**: Gather more data and revalidate

---

## Expected Output

```
[1/7] ALPHA VALIDATION
  ✅ PASS: Model beats baselines

[2/7] LEAKAGE DETECTION
  ✅ PASS: No future lookahead

[3/7] TRADE FREQUENCY
  ✅ PASS: Trade frequency controlled

[4/7] REGIME FILTER
  ✅ PASS: Regime filter applied

[5/7] WALK-FORWARD VALIDATION
  ✅ PASS: Stable model

[6/7] EXECUTION COSTS
  ✅ PASS: Remains profitable

[7/7] MULTI-STOCK VALIDATION
  ✅ PASS: Model generalizes

🚦 DECISION GATE
✅ SAFE FOR PAPER TRADING
Confidence: 95%
```

---

## Files You Need

| File | Location |
|------|----------|
| production_validator.py | `scripts/` |
| That's it | - |

Optional but helpful:
- AUTOMATED_PRODUCTION_GATES.md (detailed docs)
- VALIDATION_STEP_BY_STEP.py (full example)
- run_validator.py (integration template)

---

## TL;DR

1. Load model + data
2. `ProductionValidator(df, model).run_all_gates()`
3. Check decision
4. If PASS → Paper trade
5. If FAIL → Improve model

Done.
