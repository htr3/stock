# 🎯 Symbol Configuration Guide

## Current Configuration

```json
STOCKS (ENABLED) - 5 symbols:
  ✓ AAPL   - Apple
  ✓ MSFT   - Microsoft  
  ✓ GOOGL  - Google
  ✓ TSLA   - Tesla
  ✓ NVDA   - NVIDIA

ETFs (DISABLED):
  ○ SPY    - S&P 500
  ○ QQQ    - Nasdaq 100
  ○ IWM    - Russell 2000

OPTIONS (DISABLED)
CRYPTO (DISABLED)
```

## How to Change Symbols

### Option 1: Edit JSON File Directly

Edit `config/trading_symbols.json`:

```json
{
  "stocks": {
    "enabled": true,
    "symbols": [
      "AAPL",    // Current
      "MSFT",
      "GOOGL",
      "YOUR_SYMBOL_HERE"  // Add new ones
    ]
  }
}
```

**To trade only Apple & Microsoft:**
```json
"symbols": ["AAPL", "MSFT"]
```

### Option 2: Use Symbol Manager

Run the interactive tool:
```powershell
python scripts/symbol_manager.py
```

Menu options:
- **1** - View current symbols
- **2** - Add stock
- **3** - Remove stock
- **4** - Enable/Disable category (stocks, ETFs, etc.)
- **5** - View full config
- **6** - Reset to default

### Option 3: Command-Line Editing

**Windows:**
```powershell
# Edit the file
notepad config/trading_symbols.json
```

**VS Code:**
```powershell
# Open directly in editor
code config/trading_symbols.json
```

---

## Popular Symbols

### Tech Stocks
- **AAPL** - Apple
- **MSFT** - Microsoft
- **GOOGL** - Google
- **TSLA** - Tesla
- **NVDA** - NVIDIA
- **META** - Meta (Facebook)
- **AMZN** - Amazon

### Finance/Banking
- **JPM** - JP Morgan
- **BAC** - Bank of America
- **GS** - Goldman Sachs
- **WFC** - Wells Fargo

### Consumer
- **COSTCO** - Costco
- **NKE** - Nike
- **MCD** - McDonald's
- **KO** - Coca-Cola

### Energy
- **XOM** - Exxon Mobil
- **CVX** - Chevron
- **COP** - ConocoPhillips

### ETFs (Index Funds)
- **SPY** - S&P 500
- **QQQ** - Nasdaq 100
- **IWM** - Russell 2000
- **VTI** - Total US Market
- **AGG** - Bond Market

### Cryptocurrencies (requires Alpaca Crypto)
- **BTC/USD** - Bitcoin
- **ETH/USD** - Ethereum
- **SOL/USD** - Solana

---

## Configuration Examples

### Example 1: Tech Giants Only
```json
{
  "stocks": {
    "enabled": true,
    "symbols": ["AAPL", "MSFT", "GOOGL", "META"]
  }
}
```

### Example 2: Diversified Portfolio
```json
{
  "stocks": {
    "enabled": true,
    "symbols": ["AAPL", "JPM", "NKE", "XOM"]
  },
  "etfs": {
    "enabled": true,
    "symbols": ["SPY", "QQQ"]
  }
}
```

### Example 3: Index Funds Only
```json
{
  "stocks": {
    "enabled": false,
    "symbols": []
  },
  "etfs": {
    "enabled": true,
    "symbols": ["SPY", "QQQ", "IWM", "VTI"]
  }
}
```

---

## How Symbols Flow Through System

```
config/trading_symbols.json
        ↓
continuous_paper_trading.py
        ↓
Loads symbols from config
        ↓
Runs trading cycle for EACH symbol
        ↓
Generates signals (SMA, RSI, MACD, etc.)
        ↓
Places BUY/SELL orders
        ↓
Logs all trades
        ↓
Dashboard displays all trades
```

---

## Real-Time View

**Check which symbols are currently trading:**

```powershell
# View the config
Get-Content "config/trading_symbols.json" | ConvertFrom-Json

# View recent trades
Get-Content "logs/trading_log_*.json" | ConvertFrom-Json | Select-Object -ExpandProperty symbol -Unique
```

---

## Restart Trading System After Changes

After editing `trading_symbols.json`:

```powershell
# Stop old system
Stop-Process -Name "python" -Force

# Restart with new symbols
$env:APCA_API_KEY_ID = "PKT7E4MZS3DZPMJTOOJCS5HBQB"
$env:APCA_API_SECRET_KEY = "591RCNtqAuoQ3XqVZnqGbpifCDTpBy1u4K14M8i1jwUr"
python scripts/continuous_paper_trading.py
```

---

## Key Points

✅ **Easy switching** - Just edit the JSON file  
✅ **Multiple categories** - Stocks, ETFs, Options, Crypto  
✅ **Symbol manager** - Interactive tool for changes  
✅ **Auto-loading** - Configuration loads on startup  
✅ **Real-time** - Dashboard shows all trades  
✅ **No code changes** - Just edit config JSON  

---

**Start trading with custom symbols now!** 🚀
