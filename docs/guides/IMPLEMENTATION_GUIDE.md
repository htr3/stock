# Stock Price Prediction ML Model - Implementation Guide

## 📋 Quick Reference

**Goal**: Predict if stock price will move UP (≥70% probability) or DOWN (≤30% probability) in the next 10 minutes

**Data Required**: OHLCV (Open, High, Low, Close, Volume) at 10-minute intervals

**Models Trained**: 5 different ML algorithms to find the best performer

**Output**: Saved trained model ready for live predictions

---

## 🚀 Getting Started (5 minutes)

### Step 1: Install
```bash
cd ml_stock_predictor
python setup.py
```

### Step 2: Generate Sample Data
```bash
python generate_sample_data.py
```
This creates `stock_data.csv` with 2000 sample candles matching your timeframe.

### Step 3: Run Pipeline
```bash
python main.py
```

### Step 4: Check Results
- View console output for model performance metrics
- Open `model_comparison.png` to see which model performed best
- Check `feature_importance_*.png` files to see what indicators matter most
- Find `best_model_*.pkl` - your trained model file

```
Output files:
├── best_model_xgboost_20240101_120000.pkl    ← Use this for predictions
├── model_comparison.png
├── feature_importance_random_forest.png
├── feature_importance_xgboost.png
└── feature_importance_lightgbm.png
```

---

## 📊 Understanding the Output

### Model Comparison Results

```
                    accuracy  precision    recall      f1      auc
xgboost               0.5847    0.5892    0.5423   0.5651   0.6234
lightgbm              0.5734    0.5698    0.5612   0.5655   0.6108
gradient_boosting     0.5612    0.5634    0.5087   0.5349   0.5934
random_forest         0.5489    0.5512    0.4956   0.5221   0.5812
logistic_regression   0.5234    0.5267    0.4789   0.5016   0.5645
```

**What each metric means:**

| Metric | Meaning | Target |
|--------|---------|--------|
| **Accuracy** | % of correct predictions | Higher = Better |
| **Precision** | Of predicted UPs, how many were correct | 55-65% is good |
| **Recall** | % of actual UPs we caught | 50-60% is good |
| **F1-Score** | Balanced accuracy/recall (PRIMARY METRIC) | 55-65% is decent |
| **AUC** | ROC curve area (0.5 = random, 1.0 = perfect) | 55-65% is decent |

**Typical Results:**
- Random baseline: ~50% accuracy
- Good ML model: 52-58% accuracy
- Excellent model: 58-65% accuracy

### Top Features Example

```
XGBoost Top 20 Important Features:
1. rsi                     0.0847
2. macd                    0.0756
3. macd_histogram          0.0634
4. close_lag_1             0.0523
5. bb_upper                0.0487
6. atr                     0.0456
7. stoch_k                 0.0412
8. ema_20                  0.0398
9. momentum                0.0367
10. volume_ratio           0.0345
...
```

These show RF/XGBoost/LightGBM found RSI and MACD most predictive.

---

## 🔄 Complete Workflow

### 1. Prepare Your Data

Your CSV must have these columns:
```
Date,Open,High,Low,Close,Volume
2024-01-01 09:30:00,100.50,101.25,100.25,101.00,2500000
2024-01-01 09:40:00,101.00,101.75,100.75,101.50,2100000
```

**Data requirements:**
- ✓ Minimum 500 candles (2000+ recommended)
- ✓ 10-minute intervals (or edit code for your timeframe)
- ✓ No missing OHLCV values
- ✓ Volume > 0

### 2. Feature Engineering (Phases 2-3)

The pipeline automatically generates 50+ features:

**A. Candlestick Patterns (8 features)**
```python
- Hollow White Candle (bullish indicator)
- Filled Black Candle (bearish indicator)
- Spinning Top (neutral/reversal)
- Doji (reversal signal)
- Hammer (bullish reversal)
- Shooting Star (bearish reversal)
- Bullish/Bearish Engulfing patterns
```

**B. Technical Indicators (20+ features)**
```python
- RSI (14-period) → momentum, overbought/oversold
- MACD → trend direction and strength
- Bollinger Bands → volatility levels
- Stochastic → momentum oscillator
- ATR → average volatility
- Moving Averages → trend direction
- Pivot Points → support/resistance levels
```

**C. Time-Series Features (15+ features)**
```python
- Lag features (prev 1,2,3 candles)
- Returns (1%, 3%, 5%-period)
- Rolling statistics (mean, std, min, max)
- Momentum
- Volatility z-scores
```

**D. Combined Signals (5 features)**
```python
- Strong Buy Signal (RSI + MACD + BB + Stoch aligned)
- Strong Sell Signal (bearish indicators aligned)
- Uptrend/Downtrend indicators
- High Volatility signal
```

### 3. Target Variable (Phase 4)

The model learns to predict:
```python
target_direction = 1 if Next_Close > Current_Close else 0
                 = 1 (UP) or 0 (DOWN)
```

The model essentially learns:
- When will price go UP in next 10 min? → Predict 1
- When will price go DOWN in next 10 min? → Predict 0

Success = accurate predictions on unseen test data

### 4. Data Cleaning (Phase 5)

Automatically handled:
- ✓ Remove rows with NaN values
- ✓ Remove statistical outliers (IQR method)
- ✓ Balance classes (so 50% up isn't always predicted)
- ✓ Normalize/scale features for algorithms
- ✓ Time-series aware train/test split (no future leakage)

### 5. Model Training (Phase 6)

5 algorithms trained in parallel:

| Model | Type | Best For |
|-------|------|----------|
| **Logistic Regression** | Linear | Baseline, interpretable |
| **Random Forest** | Ensemble Trees | Robust, feature importance |
| **Gradient Boosting** | Sequential Boosting | Good accuracy, interpretable |
| **XGBoost** | Advanced Boosting | High accuracy, fast |
| **LightGBM** | Fast Boosting | Fast training, memory efficient |

Each model automatically:
- Trains on 80% of data
- Tests on 20% of data
- Applies hyperparameter tuning
- Calculates performance metrics
- Generates feature importance

### 6. Model Selection (Phase 7)

Best model is selected by F1-score (balances precision & recall)
```
Best Model: XGBoost (F1: 0.5651)
Saved as: best_model_xgboost_20240101_120000.pkl
```

---

## 💾 Making Predictions on New Data

### Method 1: Load and Use Saved Model

```python
import joblib
import pandas as pd
from feature_engineering import FeatureEngineer

# Step 1: Load your trained model
model = joblib.load('best_model_xgboost_20240101_120000.pkl')

# Step 2: Load new data
new_data = pd.read_csv('new_stock_data.csv')

# Step 3: Generate features (same process as training)
engineer = FeatureEngineer(new_data)
features = engineer.generate_all_features()

# Step 4: Make predictions
predictions = model.predict(features)         # 1=UP, 0=DOWN
probabilities = model.predict_proba(features) # confidence scores

# Step 5: Create results dataframe
results = pd.DataFrame({
    'Date': new_data['Date'],
    'Price': new_data['Close'],
    'Prediction': predictions,
    'Confidence': probabilities.max(axis=1)
})

# Step 6: Filter high confidence predictions (>65% confident)
high_conf = results[results['Confidence'] > 0.65]
print(high_conf)
```

Output:
```
         Date      Price  Prediction  Confidence
0  2024-01-02   101.50        1        0.72    ← UP prediction, 72% confident
3  2024-01-02   102.10        1        0.68    ← UP prediction, 68% confident
7  2024-01-02   101.80        0        0.71    ← DOWN prediction, 71% confident
```

### Method 2: Use Examples Script

```bash
python examples.py
# Select option 3: "Make Predictions on New Data"
```

---

## ✅ Validation & Backtesting

### Simple Backtest

```python
# Load model and historical data
model = joblib.load('best_model_xgboost_20240101_120000.pkl')
df = pd.read_csv('historical_data.csv')

# Generate features
engineer = FeatureEngineer(df)
features = engineer.generate_all_features()

# Get predictions
predictions = model.predict(features)
prob = model.predict_proba(features)

# Calculate actual outcomes
df['next_close'] = df['Close'].shift(-1)
df['actual_up'] = (df['next_close'] > df['Close']).astype(int)
df['pred_up'] = predictions
df['confidence'] = prob.max(axis=1)

# Filter high confidence (65%+)
trades = df[df['confidence'] > 0.65].copy()

# Calculate accuracy on high-confidence trades
accuracy = (trades['actual_up'] == trades['pred_up']).mean()
print(f"Accuracy on high-confidence trades: {accuracy:.2%}")
```

### What to Monitor

✓ **In-sample accuracy** (test set): 50-65%
✓ **Out-of-sample accuracy** (new data): 50-60%
✓ **Win rate on high-confidence**: 55-70%
✓ **Consistency**: Similar performance on different time periods

⚠️ **Red flags:**
- ✗ Accuracy drops >5% on new data (overfitting)
- ✗ Accuracy below 50% (worse than random!)
- ✗ High variance between different tests (unstable)

---

## 🔧 Customization Examples

### Example 1: Change Timeframe

If your data is 5-minute instead of 10-minute:

```python
# In feature_engineering.py, adjust indicator periods:
# RSI period for 5-min: 7 (instead of 14)
# MACD for 5-min: (6, 13, 5) instead of (12, 26, 9)

class IndicatorFeatures:
    @staticmethod
    def rsi(df, period: int = 7):  # Changed from 14
        ...
```

### Example 2: Add Your Own Pattern

```python
# In CandlestickPatternFeatures class:

@staticmethod
def three_black_crows(df: pd.DataFrame) -> pd.Series:
    """
    Bearish reversal: 3 consecutive down closes
    """
    is_pattern = (
        (df['Close'] < df['Open']) &  # Day 1: black
        (df['Close'].shift(1) < df['Open'].shift(1)) &  # Day 2: black
        (df['Close'].shift(2) < df['Open'].shift(2)) &  # Day 3: black
        (df['Close'] < df['Close'].shift(1)) &  # Each closes lower
        (df['Close'].shift(1) < df['Close'].shift(2))
    )
    return is_pattern.astype(int).rename('three_black_crows')
```

Then add to pipeline:
```python
# In FeatureEngineer.generate_all_features():
self.features['three_black_crows'] = \
    CandlestickPatternFeatures.three_black_crows(self.df)
```

### Example 3: Change Target Variable

For 3-class prediction (Strong UP, Neutral, Strong DOWN):

```python
# In main.py, change:
self.prepare_data(target_col='target_multiclass')  # Instead of 'target_direction'
```

Now model predicts: {-1: DOWN, 0: NEUTRAL, 1: UP}

### Example 4: Use Different Model

To focus on just one model:

```python
# In model_training.py:
trainer = ModelTrainer()

# Train only XGBoost (fastest)
trainer.train_xgboost(X_train, y_train, X_test, y_test)

best_model = trainer.models['xgboost']
trainer.save_best_model()
```

---

## 📈 Improving Performance

### 1. More/Better Data
- Get 6+ months of clean data
- Use 5-minute candles (more patterns)
- Ensure high-volume stocks (tight signals)

### 2. Feature Engineering
- Add technical indicators (Stochastic RSI, Vortex, etc.)
- Add market microstructure (bid-ask spread, order flow)
- Add macro features (VIX, sector momentum)

### 3. Model Tuning
```python
# Hyperparameter optimization
from sklearn.model_selection import GridSearchCV

params = {
    'n_estimators': [100, 200, 300],
    'max_depth': [5, 10, 15],
    'learning_rate': [0.01, 0.05, 0.1]
}

grid_search = GridSearchCV(xgb.XGBClassifier(), params, cv=5)
grid_search.fit(X_train, y_train)
best_model = grid_search.best_estimator_
```

### 4. Ensemble Methods
```python
# Combine multiple models
from sklearn.ensemble import VotingClassifier

voting = VotingClassifier([
    ('rf', RandomForestClassifier()),
    ('xgb', xgb.XGBClassifier()),
    ('lgb', lgb.LGBMClassifier())
], voting='soft')

voting.fit(X_train, y_train)
```

---

## ⚠️ Important Warnings

### Before Live Trading

1. **Backtest thoroughly** on multiple time periods
2. **Paper trade first** - validate on real-time data
3. **Understand the risks** - 60% accuracy means 40% losses
4. **Use proper position sizing** - risking only 1-2% per trade
5. **Set stop-losses** - protect against model failures
6. **Monitor performance** - retrain monthly with new data
7. **Account for slippage** - real execution costs and delays

### Common Mistakes

❌ Trading immediately without validation
❌ Overfitting to historical data
❌ Ignoring transaction costs
❌ Using too much leverage
❌ Not retraining with new data
❌ Assuming model works on all stocks

✓ Do: Validate → Paper trade → Live trade small → Monitor → Improve

---

## 🆘 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'xgboost'"

```bash
pip install xgboost lightgbm --upgrade
```

### Issue: "NaN values in predictions"

Check for:
- Missing data in CSV (check for blank cells)
- Insufficient historical data (need at least 30 candles)
- Invalid OHLC values (High < Low, etc.)

```python
# Debug:
print(df.isnull().sum())  # Check for NaN
print(df[df['High'] < df['Low']])  # Check validity
```

### Issue: "Model accuracy = 50% (random)"

Possible causes:
- Too little data (need 2000+ candles)
- Wrong target variable
- Indicators not suited to this timeframe
- Market conditions have changed

Solution:
- Get more data
- Try different indicators
- Check market regime (trending vs choppy)

### Issue: "Model works in backtest but fails live"

This is overfitting. Solutions:
- Use less features (remove weak ones)
- Retrain model weekly with new data
- Use ensemble of multiple models
- Monitor and rebuild if accuracy drops

---

## 📞 Quick Reference

### Key Files

```
feature_engineering.py    ← How features are created
target_variable.py        ← How to predict (UP/DOWN)
data_preparation.py       ← Data cleaning pipeline
model_training.py         ← Model training code
main.py                   ← Run complete pipeline
examples.py               ← Usage examples
```

### Key Functions

```python
# Generate features
engineer = FeatureEngineer(df)
features = engineer.generate_all_features()

# Create targets
targets = TargetVariable.create_all_targets(df)

# Prepare data
pipeline = DataPipeline(features, targets)
X_train, X_test, y_train, y_test = pipeline.prepare()

# Train models
trainer = ModelTrainer()
trainer.train_xgboost(X_train, y_train, X_test, y_test)

# Get predictions
model = joblib.load('best_model_xgboost_*.pkl')
predictions = model.predict(features_new)
confidence = model.predict_proba(features_new).max(axis=1)
```

### Command Reference

```bash
# Setup
python setup.py

# Generate sample data
python generate_sample_data.py

# Run complete pipeline
python main.py

# Explore examples
python examples.py

# Quick test
python -c "from main import StockPricePredictionPipeline; \
    p = StockPricePredictionPipeline('stock_data.csv')"
```

---

## ✨ Next Steps

1. ✓ **Initial Setup** → Run `python setup.py`
2. ✓ **Test Pipeline** → Run `python main.py` with sample data
3. ✓ **Use Your Data** → Prepare your CSV and run pipeline
4. ✓ **Validate Model** → Backtest on historical data
5. ✓ **Paper Trade** → Test on real-time data without money
6. ✓ **Live Trade** → Start small, monitor, improve

---

**Good luck with your trading! 📈**

Remember: The goal isn't perfect predictions (impossible), but consistent profitable trading with proper risk management.
