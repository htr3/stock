# Stock Data Sources for Training Your ML Model

Your model requires OHLCV data in CSV format with these columns:
- `timestamp`: Date/time (YYYY-MM-DD HH:MM:SS format)
- `open`: Opening price
- `high`: High price
- `low`: Low price
- `close`: Closing price
- `volume`: Trading volume

## 🎯 **Recommended Sources (Easiest to Use)**

### 1. **Yahoo Finance** (FREE - Best for Beginners)
```python
import yfinance as yf
import pandas as pd

# Download data for a stock (e.g., Apple)
ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01", end="2024-01-01", interval="10m")

# Format for your model
data = data.reset_index()
data = data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
data.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

# Save to CSV
data.to_csv('AAPL_10min_data.csv', index=False)
```

**Pros**: Free, reliable, 10-minute data available
**Cons**: Limited historical data for some stocks

### 2. **Alpha Vantage** (FREE API - Professional)
```python
import requests
import pandas as pd

API_KEY = "YOUR_API_KEY"  # Get free key at https://www.alphavantage.co/

def get_intraday_data(symbol, interval='10min'):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&apikey={API_KEY}&outputsize=full"
    response = requests.get(url)
    data = response.json()

    # Parse the data
    time_series = data[f"Time Series ({interval})"]
    df = pd.DataFrame.from_dict(time_series, orient='index')
    df = df.reset_index()
    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

    return df

# Get Apple data
apple_data = get_intraday_data('AAPL')
apple_data.to_csv('AAPL_intraday.csv', index=False)
```

**Pros**: High-quality data, real-time updates
**Cons**: 5 API calls/minute limit on free tier

### 3. **Polygon.io** (FREE Tier Available)
```python
import requests
import pandas as pd

API_KEY = "YOUR_API_KEY"  # Free tier available

def get_polygon_data(symbol, start_date, end_date):
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/10/minute/{start_date}/{end_date}?apiKey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    # Parse results
    records = []
    for result in data['results']:
        records.append({
            'timestamp': pd.to_datetime(result['t'], unit='ms'),
            'open': result['o'],
            'high': result['h'],
            'low': result['l'],
            'close': result['c'],
            'volume': result['v']
        })

    df = pd.DataFrame(records)
    return df

# Get data
data = get_polygon_data('AAPL', '2023-01-01', '2024-01-01')
data.to_csv('AAPL_polygon.csv', index=False)
```

## 📊 **Other Free Sources**

### 4. **Twelve Data** (FREE API)
```python
import requests
import pandas as pd

API_KEY = "YOUR_API_KEY"

def get_twelve_data(symbol):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=10min&apikey={API_KEY}&outputsize=5000"
    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame(data['values'])
    df['timestamp'] = pd.to_datetime(df['datetime'])
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    df = df.astype({'open': float, 'high': float, 'low': float, 'close': float, 'volume': int})

    return df

data = get_twelve_data('AAPL')
data.to_csv('AAPL_twelve.csv', index=False)
```

### 5. **IEX Cloud** (FREE Tier)
```python
import requests
import pandas as pd

# Free tier available at https://iexcloud.io/
TOKEN = "YOUR_TOKEN"

def get_iex_data(symbol, range='6m'):  # 1m, 3m, 6m, 1y, 2y, 5y
    url = f"https://cloud.iexapis.com/stable/stock/{symbol}/chart/{range}?token={TOKEN}"
    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['minute'].fillna('09:30'))
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    df = df.dropna()

    return df

data = get_iex_data('AAPL', '6m')
data.to_csv('AAPL_iex.csv', index=False)
```

## 💰 **Premium Sources (For Serious Trading)**

### 6. **Interactive Brokers** (Professional)
- Real-time and historical data
- Multiple asset classes
- Professional-grade API

### 7. **Bloomberg Terminal** (Institutional)
- Comprehensive market data
- News and analytics
- Expensive but complete

### 8. **Refinitiv** (Eikon)
- Global market data
- Real-time feeds
- Enterprise solution

## 🛠️ **Quick Setup Scripts**

### Automated Data Downloader
```python
# Save this as data_downloader.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def download_stock_data(ticker, start_date, end_date, interval='10m'):
    """Download and format stock data for your ML model"""

    print(f"Downloading {ticker} data from {start_date} to {end_date}")

    # Download data
    data = yf.download(ticker, start=start_date, end=end_date, interval=interval)

    if data.empty:
        print(f"No data found for {ticker}")
        return None

    # Format for your model
    data = data.reset_index()
    if 'Datetime' in data.columns:
        data = data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
        data.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    else:
        data = data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        data.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

    # Clean data
    data = data.dropna()
    data = data.sort_values('timestamp')

    return data

# Example usage
if __name__ == "__main__":
    # Popular stocks to test with
    stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']

    for stock in stocks:
        data = download_stock_data(stock, '2023-01-01', '2024-01-01')
        if data is not None:
            filename = f'{stock}_10min_data.csv'
            data.to_csv(filename, index=False)
            print(f"Saved {len(data)} records to {filename}")
```

### Multi-Stock Data Collector
```python
# Save this as multi_stock_downloader.py
import yfinance as yf
import pandas as pd
from datetime import datetime

def collect_multiple_stocks(stocks, start_date, end_date):
    """Collect data for multiple stocks"""

    all_data = []

    for stock in stocks:
        print(f"Downloading {stock}...")
        try:
            data = yf.download(stock, start=start_date, end=end_date, interval='10m')

            if not data.empty:
                data = data.reset_index()
                data['symbol'] = stock  # Add stock symbol column
                all_data.append(data)

        except Exception as e:
            print(f"Error downloading {stock}: {e}")

    if all_data:
        combined_data = pd.concat(all_data, ignore_index=True)
        combined_data.to_csv('multi_stock_data.csv', index=False)
        print(f"Saved {len(combined_data)} total records")
        return combined_data

    return None

# Popular tech stocks
tech_stocks = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META',
    'NFLX', 'CRM', 'AMD', 'INTC', 'ORCL', 'CSCO', 'ADBE'
]

# Collect data
data = collect_multiple_stocks(tech_stocks, '2023-01-01', '2024-01-01')
```

## 📋 **Data Quality Checklist**

Before using data for training:

```python
def validate_stock_data(df):
    """Validate data quality for ML training"""

    issues = []

    # Check required columns
    required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        issues.append(f"Missing columns: {missing_cols}")

    # Check for null values
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        issues.append(f"Null values found: {null_counts[null_counts > 0].to_dict()}")

    # Check OHLC logic
    invalid_ohlc = (
        (df['high'] < df['low']) |
        (df['high'] < df['open']) |
        (df['high'] < df['close']) |
        (df['low'] > df['open']) |
        (df['low'] > df['close'])
    ).sum()
    if invalid_ohlc > 0:
        issues.append(f"Invalid OHLC relationships: {invalid_ohlc} rows")

    # Check volume
    negative_volume = (df['volume'] < 0).sum()
    if negative_volume > 0:
        issues.append(f"Negative volume: {negative_volume} rows")

    if not issues:
        print("✅ Data validation passed!")
        return True
    else:
        print("❌ Data quality issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False

# Validate your data
is_valid = validate_stock_data(your_dataframe)
```

## 🚀 **Quick Start Guide**

1. **Install required packages:**
```bash
pip install yfinance requests pandas
```

2. **Get your first dataset:**
```python
import yfinance as yf

# Download Apple 10-minute data
data = yf.download('AAPL', start='2023-01-01', end='2024-01-01', interval='10m')
data.to_csv('AAPL_training_data.csv')
```

3. **Test with your model:**
```bash
cd scripts
python main.py  # Update the data path in main.py first
```

## 📊 **Recommended Testing Stocks**

**Large Cap (Stable)**: AAPL, MSFT, GOOGL, AMZN
**Tech Growth**: TSLA, NVDA, META, NFLX
**Volatile (Good for testing)**: TSLA, AMD, NVDA
**Index ETFs**: SPY, QQQ, IWM

## ⚠️ **Important Notes**

- **Data Quality**: Always validate your data before training
- **Time Zones**: Ensure consistent timezone handling
- **Data Gaps**: Check for missing data points
- **Volume**: Some sources may have incomplete volume data
- **API Limits**: Respect rate limits on free APIs
- **Historical Data**: Free sources may limit historical depth

## 🎯 **Next Steps**

1. Choose a data source from above
2. Download data for 1-2 stocks to start
3. Validate data quality
4. Update your `main.py` to use real data instead of sample data
5. Train and test your enhanced model!

Would you like me to help you set up data collection for a specific stock or source?</content>
<parameter name="filePath">c:\Users\visha\All\stocks\docs\references\data_sources_guide.md