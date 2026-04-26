#!/usr/bin/env python3
"""
Live Data Fetcher: Dynamic Alpaca 10min bars replacing static CSV.
Fetches last N bars per symbol for ML feature generation.
"""

import os
import json
import logging
import sys
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.client import TradingClient  # For account check
from alpaca.data.enums import DataFeed

# Module level logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class LiveDataFetcher:
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None, paper: bool = True):
        """
        Initialize with Alpaca credentials.
        Uses env vars APCA_API_KEY_ID/APCA_API_SECRET_KEY if not provided.
        """
        self.api_key = api_key or os.getenv("APCA_API_KEY_ID")
        self.secret_key = secret_key or os.getenv("APCA_API_SECRET_KEY")
        self.paper = paper
        
        if not self.api_key or not self.secret_key:
            raise ValueError(
                "❌ Alpaca API keys missing!\n"
                "Set: export APCA_API_KEY_ID='your_key'\n"
                "     export APCA_API_SECRET_KEY='your_secret'\n"
                "Get free keys: https://alpaca.markets/"
            )
        
        # Data client for bars
        self.data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
        
        # Trading client for account status
        self.trading_client = TradingClient(self.api_key, self.secret_key, paper=paper)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"✅ LiveDataFetcher initialized (paper={self.paper})")

    def get_symbols(self, config_path: str = None) -> List[str]:
        """
        Load trading symbols from config/trading_symbols.json or default.
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "trading_symbols.json"
        
        symbols = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
        
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                all_symbols = []
                for category in config.values():
                    if not isinstance(category, dict) or "symbols" not in category:
                        continue
                    # Respect 'enabled' flag if present; default to True for back-compat
                    if not category.get("enabled", True):
                        continue
                    all_symbols.extend(category["symbols"])
                if all_symbols:
                    symbols = all_symbols[:10]  # Limit to 10
                print(f"📋 Loaded {len(symbols)} symbols from {config_path}: {', '.join(symbols[:5])}...")
            except Exception as e:
                self.logger.warning(f"⚠️ Config load failed ({e}), using US defaults")
        
        return symbols

    def fetch_live_bars(
        self,
        bars_back: int = 200,
        timeframe: TimeFrame = TimeFrame(10, TimeFrameUnit.Minute),
        symbols: List[str] = None
    ) -> Dict[str, pd.DataFrame]:
        if symbols is None:
            symbols = []
        if not symbols:
            raise ValueError("symbols list cannot be empty")
        """
        Fetch LIVE 10min bars from Alpaca for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            bars_back: Number of recent bars (200 = ~33h for 10min)
            timeframe: TimeFrame (default 10min)
            
        Returns:
            Dict[symbol, DataFrame(OHLCV)] - Ready for FeatureEngineer
        """
        self.logger.info(f"📡 Fetching {bars_back} x 10min bars for {len(symbols)} symbols...")
        
        end = datetime.now()
        start = end - timedelta(minutes=10 * bars_back)
        
        request = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=timeframe,
            start=start,
            end=end,
            adjustment="raw",  # Use raw prices for ML
            feed=DataFeed.SIP  # SIP for better US coverage
        )
        
        try:
            bars = self.data_client.get_stock_bars(request)
            
            data = {}
            if not bars or bars.df.empty:
                self.logger.warning("❌ No data returned from Alpaca.")
                return {symbol: pd.DataFrame() for symbol in symbols}
                
            full_df = bars.df
            
            for symbol in symbols:
                try:
                    if not full_df.empty and symbol in full_df.index.get_level_values(0):
                        df = full_df.xs(symbol, level=0).copy()
                        df.index.name = 'timestamp'
                        df = df[["open", "high", "low", "close", "volume"]]
                        df.columns = [col.lower() for col in df.columns]
                        data[symbol] = df
                        self.logger.info(f"  ✅ {symbol}: {len(df)} bars ({df.index[0].strftime('%Y-%m-%d %H:%M')} → now)")
                        self.logger.info(f"  📊 Columns: {list(df.columns)} (lowercase for ML)")
                    else:
                        self.logger.warning(f"  ❌ {symbol}: No data")
                        data[symbol] = pd.DataFrame()
                except Exception as e:
                    self.logger.error(f"  ❌ {symbol}: Error extracting data: {e}")
                    data[symbol] = pd.DataFrame()
            
            success_count = len([s for s in data if not data[s].empty])
            self.logger.info(f"✅ Fetched live data for {success_count}/{len(symbols)} symbols")
            return data
            
        except Exception as e:
            self.logger.error(f"❌ Fetch failed: {e}")
            self.logger.info("💡 Check: API keys, internet, market hours, symbol validity")
            return {symbol: pd.DataFrame() for symbol in symbols}

    def account_status(self) -> Dict:
        """
        Check paper trading account status.
        """
        try:
            account = self.trading_client.get_account()
            return {
                "equity": float(account.equity),
                "cash": float(account.cash),
                "status": account.status,
                "buying_power": float(account.buying_power)
            }
        except Exception as e:
            self.logger.warning(f"⚠️ Account check failed: {e}")
            return {"error": str(e)}

    def test_connection(self, symbols: List[str] = None):
        """
        Quick test: Fetch 10 bars/symbol + account status.
        """
        print("🔌 Testing LiveDataFetcher...")
        
        status = self.account_status()
        print(f"💰 Account: Equity ${status.get('equity', 0):,.0f}, Status: {status.get('status', 'ERROR')}")
        
        if symbols is None:
            symbols = self.get_symbols()
        
        test_data = self.fetch_live_bars(symbols=symbols[:3], bars_back=10)
        print("✅ Connection OK! Ready for live ML trading.")

def main():
    """
    CLI usage: python live_data_fetcher.py [test|fetch AAPL,MSFT]
    """
    import sys
    args = sys.argv[1:]
    
    fetcher = LiveDataFetcher(paper=True)
    
    if len(args) == 0 or args[0] == "test":
        fetcher.test_connection()
    elif args[0] == "fetch":
        symbols = args[1].split(",") if len(args) > 1 else ["AAPL"]
        data = fetcher.fetch_live_bars(symbols=symbols)
        print(f"Fetched data keys: {list(data.keys())}")
    else:
        print("Usage: python live_data_fetcher.py [test|fetch AAPL,MSFT]")
        print("Or: from live_data_fetcher import LiveDataFetcher")

if __name__ == "__main__":
    main()

