#!/usr/bin/env python3
"""
Stock Data Downloader for ML Training
Quick script to get OHLCV data for your stock prediction model
"""

import yfinance as yf
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
import os

class StockDataDownloader:
    """Download and format stock data for ML training"""

    def __init__(self):
        self.data_dir = "../data/raw"
        os.makedirs(self.data_dir, exist_ok=True)

    def download_yahoo_data(self, ticker, start_date, end_date, interval='10m'):
        """Download data from Yahoo Finance (FREE)"""

        print(f"📈 Downloading {ticker} data from Yahoo Finance...")
        print(f"   Period: {start_date} to {end_date}")
        print(f"   Interval: {interval}")

        try:
            # Download data
            data = yf.download(ticker, start=start_date, end=end_date, interval=interval)

            if data.empty:
                print(f"❌ No data found for {ticker}")
                return None

            # Format for your model
            data = data.reset_index()
            if 'Datetime' in data.columns:
                # Intraday data
                data = data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
                data.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            else:
                # Daily data
                data = data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
                data.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

            # Clean data
            data = data.dropna()
            data = data.sort_values('timestamp')

            # Convert timestamp to string format
            data['timestamp'] = data['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

            filename = f"{self.data_dir}/{ticker}_{interval}_data.csv"
            data.to_csv(filename, index=False)

            print(f"✅ Saved {len(data)} records to {filename}")
            return data

        except Exception as e:
            print(f"❌ Error downloading {ticker}: {e}")
            return None

    def download_alpha_vantage(self, ticker, api_key, interval='10min'):
        """Download from Alpha Vantage (FREE API)"""

        print(f"📊 Downloading {ticker} from Alpha Vantage...")

        try:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval={interval}&apikey={api_key}&outputsize=full"
            response = requests.get(url)
            data = response.json()

            if "Time Series (10min)" not in data:
                print(f"❌ API Error: {data.get('Error Message', 'Unknown error')}")
                return None

            # Parse data
            time_series = data[f"Time Series ({interval})"]
            records = []

            for timestamp, values in time_series.items():
                records.append({
                    'timestamp': timestamp,
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(values['5. volume'])
                })

            df = pd.DataFrame(records)
            df = df.sort_values('timestamp')

            filename = f"{self.data_dir}/{ticker}_alphavantage_{interval}_data.csv"
            df.to_csv(filename, index=False)

            print(f"✅ Saved {len(df)} records to {filename}")
            return df

        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def validate_data(self, df):
        """Validate data quality"""

        print("🔍 Validating data quality...")

        issues = []

        # Check required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing columns: {missing_cols}")

        # Check for null values
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            issues.append(f"Null values: {null_counts[null_counts > 0].to_dict()}")

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

        if not issues:
            print("✅ Data validation passed!")
            return True
        else:
            print("❌ Data quality issues:")
            for issue in issues:
                print(f"   - {issue}")
            return False

def main():
    """Main function to download sample data"""

    downloader = StockDataDownloader()

    print("🚀 Stock Data Downloader for ML Training")
    print("=" * 50)

    # Test stocks - mix of stable and volatile
    test_stocks = [
        ('AAPL', 'Apple Inc.'),
        ('MSFT', 'Microsoft Corp.'),
        ('TSLA', 'Tesla Inc.'),
        ('NVDA', 'NVIDIA Corp.'),
        ('GOOGL', 'Alphabet Inc.')
    ]

    print("📋 Available test stocks:")
    for i, (ticker, name) in enumerate(test_stocks, 1):
        print(f"   {i}. {ticker} - {name}")

    # Download recent data (last 6 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 6 months

    print(f"\n📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print("⏱️  Interval: 10 minutes")

    # Download data for each stock
    for ticker, name in test_stocks:
        print(f"\n{'='*50}")
        print(f"🎯 Downloading {name} ({ticker})")

        data = downloader.download_yahoo_data(
            ticker=ticker,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            interval='10m'
        )

        if data is not None:
            # Validate data
            is_valid = downloader.validate_data(data)

            if is_valid:
                print(f"🎉 {ticker} data ready for ML training!")
            else:
                print(f"⚠️  {ticker} data has quality issues - review before training")
        else:
            print(f"❌ Failed to download {ticker} data")

        # Rate limiting
        time.sleep(1)

    print(f"\n{'='*50}")
    print("📁 Data saved to: ../data/raw/")
    print("🔄 Next steps:")
    print("   1. Check downloaded CSV files")
    print("   2. Update main.py to use real data path")
    print("   3. Run: python main.py")
    print("   4. Compare results with sample data")

if __name__ == "__main__":
    main()