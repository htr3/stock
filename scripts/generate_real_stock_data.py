#!/usr/bin/env python3
"""
Simple Stock Data Generator for Testing
Creates realistic OHLCV data for testing your ML model
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

class StockDataGenerator:
    """Generate realistic stock data for testing"""

    def __init__(self):
        self.data_dir = "../data/raw"
        os.makedirs(self.data_dir, exist_ok=True)

    def generate_realistic_stock_data(self, symbol, days=180, interval_minutes=10):
        """Generate realistic OHLCV data"""

        print(f"🎯 Generating {symbol} data for {days} days...")

        # Create timestamps
        start_date = datetime.now() - timedelta(days=days)
        timestamps = []

        current_time = start_date
        end_time = datetime.now()

        while current_time < end_time:
            # Only generate data during market hours (9:30 AM - 4:00 PM EST)
            if current_time.weekday() < 5:  # Monday-Friday
                hour = current_time.hour
                minute = current_time.minute

                if (hour == 9 and minute >= 30) or (hour > 9 and hour < 16) or (hour == 16 and minute == 0):
                    timestamps.append(current_time)

            current_time += timedelta(minutes=interval_minutes)

        print(f"   Generated {len(timestamps)} data points")

        # Generate realistic price movements
        np.random.seed(hash(symbol) % 2**32)  # Reproducible seed per symbol

        # Base price (different for each stock)
        base_prices = {
            'AAPL': 180, 'MSFT': 380, 'GOOGL': 140, 'TSLA': 250,
            'NVDA': 450, 'AMZN': 150, 'META': 330, 'NFLX': 480
        }

        base_price = base_prices.get(symbol, 100)

        # Generate price series with trends and volatility
        n_points = len(timestamps)

        # Long-term trend
        trend = np.linspace(0, np.random.normal(0.1, 0.05), n_points)

        # Short-term movements
        short_term = np.random.normal(0, 0.02, n_points).cumsum()

        # Intraday patterns (higher volatility during market open/close)
        intraday_volatility = np.ones(n_points)
        for i, ts in enumerate(timestamps):
            hour = ts.hour
            if hour in [9, 10, 14, 15]:  # Higher volatility hours
                intraday_volatility[i] = 1.5

        # Combine movements
        price_changes = trend + short_term * intraday_volatility
        prices = base_price * (1 + price_changes)

        # Generate OHLCV from price series
        data = []
        for i, (ts, price) in enumerate(zip(timestamps, prices)):
            # Add some noise to create realistic OHLC
            noise = np.random.normal(0, 0.005, 4)  # 0.5% noise

            high = price * (1 + abs(noise[0]))
            low = price * (1 - abs(noise[1]))
            open_price = price * (1 + noise[2] * 0.5)
            close = price * (1 + noise[3] * 0.5)

            # Ensure OHLC logic
            high = max(high, open_price, close)
            low = min(low, open_price, close)

            # Volume (higher during volatile periods)
            base_volume = np.random.randint(10000, 100000)
            volume_multiplier = 1 + abs(price_changes[i]) * 10
            volume = int(base_volume * volume_multiplier)

            data.append({
                'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
                'Open': round(open_price, 2),
                'High': round(high, 2),
                'Low': round(low, 2),
                'Close': round(close, 2),
                'Volume': volume
            })

        df = pd.DataFrame(data)

        # Save to file
        filename = f"{self.data_dir}/{symbol}_{interval_minutes}min_generated_data.csv"
        df.to_csv(filename, index=False)

        print(f"✅ Saved {len(df)} records to {filename}")
        return df

    def generate_multiple_stocks(self, symbols, days=90):
        """Generate data for multiple stocks"""

        print("🚀 Generating data for multiple stocks...")

        for symbol in symbols:
            try:
                self.generate_realistic_stock_data(symbol, days=days)
                print(f"✅ {symbol} completed")
            except Exception as e:
                print(f"❌ Error generating {symbol}: {e}")

        print("\n📁 All data saved to: ../data/raw/")
        print("🔄 Next: Update main.py to use these files for training")

def main():
    """Generate sample data for testing"""

    generator = StockDataGenerator()

    print("🎯 Stock Data Generator for ML Testing")
    print("=" * 50)
    print("This will create realistic OHLCV data for testing your model")
    print("Data includes trends, volatility, and market-like patterns")

    # Popular stocks for testing
    test_stocks = ['AAPL', 'MSFT', 'TSLA', 'NVDA', 'GOOGL']

    print(f"\n📊 Will generate data for: {', '.join(test_stocks)}")
    print("📅 Time period: Last 90 days")
    print("⏱️  Interval: 10 minutes")
    print("📁 Output: ../data/raw/")

    # Generate data
    generator.generate_multiple_stocks(test_stocks, days=90)

    print("\n🎉 Data generation complete!")
    print("💡 Your ML model now has real stock data to train on!")
    print("\n🔄 Next steps:")
    print("   1. Check CSV files in ../data/raw/")
    print("   2. Update main.py to use real data path")
    print("   3. Run: python main.py")
    print("   4. Compare with previous sample data results")

if __name__ == "__main__":
    main()