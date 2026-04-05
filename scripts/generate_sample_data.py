"""
Generate sample stock data for testing the ML model
Creates realistic OHLCV data with patterns
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_sample_stock_data(filename='stock_data.csv', num_candles=2000, 
                               initial_price=100, trend='random'):
    """
    Generate realistic sample stock data for testing
    
    Args:
        filename: Output CSV filename
        num_candles: Number of OHLCV candles to generate
        initial_price: Starting price
        trend: 'uptrend', 'downtrend', 'sideways', or 'random'
    """
    
    print(f"Generating {num_candles} sample candles with {trend} trend...")
    
    np.random.seed(42)
    dates = [datetime.now() - timedelta(minutes=i) for i in range(num_candles, 0, -1)]
    
    opens = []
    highs = []
    lows = []
    closes = []
    volumes = []
    
    price = initial_price
    
    for i in range(num_candles):
        # Determine trend direction
        if trend == 'uptrend':
            trend_factor = 0.0005
        elif trend == 'downtrend':
            trend_factor = -0.0005
        elif trend == 'sideways':
            trend_factor = 0.0
        else:  # random
            trend_factor = np.random.uniform(-0.001, 0.001)
        
        # Generate candle
        open_price = price
        close_price = price * (1 + trend_factor + np.random.normal(0, 0.004))
        high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.005)))
        low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.005)))
        
        volume = np.random.randint(1000000, 10000000)
        
        opens.append(open_price)
        highs.append(high_price)
        lows.append(low_price)
        closes.append(close_price)
        volumes.append(volume)
        
        price = close_price
    
    # Create DataFrame
    df = pd.DataFrame({
        'Date': dates,
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': closes,
        'Volume': volumes
    })
    
    # Save to CSV
    df.to_csv(filename, index=False)
    print(f"✓ Sample data saved to {filename}")
    print(f"  Price range: ${df['Low'].min():.2f} - ${df['High'].max():.2f}")
    print(f"  Volume: {df['Volume'].mean():.0f} average")
    
    return df


if __name__ == '__main__':
    # Generate sample data
    df = generate_sample_stock_data(
        filename='stock_data.csv',
        num_candles=2000,
        initial_price=100,
        trend='random'
    )
    
    print(f"\nFirst few rows:")
    print(df.head())
