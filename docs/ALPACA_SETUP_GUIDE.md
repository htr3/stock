# 🚀 Alpaca Paper Trading Setup Guide

## Why Alpaca?
- **Commission-free** trading
- **Excellent Python API** (alpaca-py)
- **Paper trading** (fake money, real market data)
- **Fast execution** (REST + WebSocket)
- **Professional features** (options, crypto coming)

## Step 1: Create Alpaca Account
1. Go to https://alpaca.markets/
2. Click "Get Started Free"
3. Complete registration
4. Verify email

## Step 2: Get API Keys
1. Login to Alpaca dashboard
2. Go to "Account" → "API Keys"
3. Create new key pair
4. **Save keys securely** (you'll need them)

## Step 3: Environment Setup
Set environment variables (recommended):
```bash
# Windows PowerShell
$env:APCA_API_KEY_ID = "your_api_key_here"
$env:APCA_API_SECRET_KEY = "your_secret_key_here"

# Or add to your system environment variables
```

Or edit `alpaca_paper_trading.py` directly (less secure):
```python
trader = AlpacaPaperTrader(
    api_key="YOUR_API_KEY_HERE",
    secret_key="YOUR_SECRET_KEY_HERE",
    paper=True
)
```

## Step 4: Test Connection
Run the paper trading script:
```bash
python scripts/alpaca_paper_trading.py
```

## Step 5: Paper Trading Workflow
1. **Get live data** (real-time market data)
2. **Run validation** (your 12-gate system)
3. **Generate signals** (using your trained model)
4. **Execute trades** (paper money)
5. **Monitor performance**

## Key Features for Your System:
- ✅ **Real-time data** (1-minute bars)
- ✅ **Instant execution** (market orders)
- ✅ **Position tracking**
- ✅ **Paper money** (no risk)
- ✅ **Python integration**

## Next Steps After Paper Trading:
1. **1-2 weeks** of paper trading
2. **Compare vs backtest** performance
3. **Scale up** position sizes
4. **Go live** with small capital

## Alternative Platforms:
- **Interactive Brokers (IBKR)**: Professional, more complex
- **TD Ameritrade**: Good for retail, Thinkorswim platform
- **Webull**: Commission-free, mobile-first

## Security Notes:
- Never share API keys
- Use paper trading first
- Start with small position sizes
- Monitor account regularly

---
**Ready to start?** Run the script and let me know if you need help! 🎯