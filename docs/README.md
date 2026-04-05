# Stock Price Prediction ML Model

A complete machine learning pipeline to predict intraday stock price movements **(UP: 70% probability or DOWN: 30% probability in next 10 minutes)** using candlestick patterns, technical indicators, and trading setups extracted from professional trading books.

## 📊 Project Overview

This project implements an end-to-end ML solution based on your instruction blueprint:

- **Phase 1**: Extract raw knowledge (candlestick patterns, trading setups, indicators)
- **Phase 2-3**: Convert technical analysis into machine learning features
- **Phase 4**: Define binary classification targets (UP vs DOWN)
- **Phase 5**: Prepare and clean data
- **Phase 6**: Train multiple ML models (Logistic Regression, Random Forest, XGBoost, LightGBM)
- **Phase 7**: Evaluate and compare models, select the best performer

## 🎯 What It Does

**Input**: OHLCV (Open, High, Low, Close, Volume) stock price data at 10-minute intervals

**Output**: ML model that predicts whether price will move UP or DOWN in the next 10 minutes

**Accuracy**: Depends on your data, typically 55-65% with proper feature engineering

## 📁 Project Structure

```
ml_stock_predictor/
├── main.py                      # Main pipeline execution
├── feature_engineering.py       # Convert patterns & indicators to features
├── target_variable.py           # Define prediction targets
├── data_preparation.py          # Data cleaning and preprocessing
├── model_training.py            # Model training and evaluation
├── generate_sample_data.py      # Create sample data for testing
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🔧 Features Generated

### Candlestick Patterns (8 features)
- Hollow White Candle (Bullish)
- Filled Black Candle (Bearish)
- Spinning Top (Neutral)
- Doji (Reversal)
- Hammer (Bullish reversal)
- Shooting Star (Bearish reversal)
- Bullish/Bearish Engulfing

### Technical Indicators (20+ features)
- **RSI** (Relative Strength Index) - Momentum
- **MACD** (Moving Average Convergence Divergence) - Trend
- **Bollinger Bands** - Volatility
- **Stochastic** - Momentum
- **ATR** (Average True Range) - Volatility
- **Moving Averages** (EMA 9, EMA 20, SMA 50)
- **Pivot Points** (S1, S2, R1, R2)
- **Volume features** - Volume ratio and moving average

### Time-Series Features (15+ features)
- Lag features (previous 1, 2, 3 candles)
- Price returns (1-period, 3-period, 5-period)
- Rolling statistics (mean, std, min, max)
- Momentum
- Volatility and Z-scores

### Combined Signals (5 features)
- Strong Buy Signal (multiple indicators align)
- Strong Sell Signal (multiple indicators align)
- Uptrend indicator
- Downtrend indicator
- High Volatility signal

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd ml_stock_predictor
pip install -r requirements.txt
```

### 2. Prepare Your Data

Create a CSV file with columns: **Date, Open, High, Low, Close, Volume**

Example structure:
```
Date,Open,High,Low,Close,Volume
2024-01-01 09:30:00,100.50,101.25,100.25,101.00,2500000
2024-01-01 09:40:00,101.00,101.75,100.75,101.50,2100000
...
```

Or generate sample data for testing:

```bash
python generate_sample_data.py
# Creates: stock_data.csv with 2000 sample candles
```

### 3. Run the Pipeline

Edit `main.py` and update the CSV file path:

```python
csv_file = 'your_data.csv'  # Change this to your file
```

Then run:

```bash
python main.py
```

### 4. View Results

The pipeline will:
- ✓ Generate 50+ features from your data
- ✓ Train 5 different ML models
- ✓ Compare performance metrics
- ✓ Save the best model
- ✓ Generate feature importance plots
- ✓ Create model comparison charts

Output files:
- `best_model_*.pkl` - Trained model (ready for predictions)
- `feature_importance_*.png` - Top 20 important features
- `model_comparison.png` - Performance comparison chart

## 📈 Model Performance Metrics

For each model, you'll see:
- **Accuracy**: Overall correctness
- **Precision**: True positive rate (reliability of UP predictions)
- **Recall**: Coverage (catching all UP movements)
- **F1-Score**: Balanced metric (recommended primary metric)
- **AUC**: Area under ROC curve

## 💡 Usage Example

```python
from main import StockPricePredictionPipeline

# Initialize and run pipeline
pipeline = StockPricePredictionPipeline('stock_data.csv')
results, best_model = pipeline.run_complete_pipeline('stock_data.csv')

# View results
print(results)
```

## 🎓 Making Predictions on New Data

```python
import joblib
import pandas as pd
from feature_engineering import FeatureEngineer

# Load trained model
model = joblib.load('best_model_xgboost_20240101_120000.pkl')

# Load new data
new_data = pd.read_csv('new_stock_data.csv')

# Generate features
engineer = FeatureEngineer(new_data)
features = engineer.generate_all_features()

# Make predictions
predictions = model.predict(features)
probabilities = model.predict_proba(features)

# predictions: 1 = UP, 0 = DOWN
# probabilities: [prob_down, prob_up]
```

## 🔍 Feature Importance

The pipeline ranks features by importance:
1. **RSI** - Momentum indicator (very important)
2. **MACD** - Trend direction (very important)
3. **Bollinger Bands** - Volatility (important)
4. **Previous close prices** - Trend continuation (important)
5. **Volume** - Buying/selling pressure (important)

Top 20 features are plotted for each model.

## 📊 Data Requirements

For best results:
- **Minimum 500 candles** (but 2000+ recommended)
- **10-minute timeframe** (or adjust code for your timeframe)
- **Complete OHLCV data** (no missing values)
- **Liquid stocks** (high volume, tight bid-ask)

## ⚠️ Important Notes

1. **Past performance ≠ Future results**: Use this for research, not trading without validation
2. **Backtest thoroughly** before live trading
3. **Paper trade first** to validate on real-time data
4. **Manage risk** - Use proper position sizing and stop-losses
5. **Market conditions change** - Retrain model periodically

## 🛠️ Customization

### Change timeframe
Edit `feature_engineering.py`:
```python
# For 5-minute candles, adjust RSI period:
IndicatorFeatures.rsi(df, period=7)  # Instead of 14
```

### Add your own patterns
In `feature_engineering.py`, add a method to `CandlestickPatternFeatures`:
```python
@staticmethod
def three_black_crows(df):
    """Your custom pattern logic"""
    # Your implementation
    return pattern.astype(int).rename('three_black_crows')
```

### Change prediction target
In `main.py`:
```python
self.prepare_data(target_col='target_multiclass')  # 3 classes instead of binary
```

## 📚 References

Features based on:
- Japanese Candlestick Charting Techniques
- Technical Analysis from A to Z (Baruch Murphy)
- A Complete Guide to Volume Price Analysis (Anna Coulling)
- Professional trading setups and indicators

## 📝 License

Open source - feel free to modify and use for research and trading

## 🤝 Contributing

Improvements welcome! Possible enhancements:
- Add more candlestick patterns
- Implement ensemble voting
- Add sentiment analysis features
- Optimize hyperparameters with Bayesian optimization
- Create live prediction API

---

**Happy Trading! 📈**
