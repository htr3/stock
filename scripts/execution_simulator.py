"""
Execution Simulator

Adds realistic trading costs:
- Slippage (price movement during order)
- Latency (delay between signal and fill)
- Order impact
- Commissions

Tests if strategy remains profitable after realistic execution costs
"""

import numpy as np
import pandas as pd


class ExecutionSimulator:
    """Simulate realistic order execution with costs"""
    
    def __init__(self, df, initial_balance=10000):
        """
        Args:
            df: OHLCV dataframe
            initial_balance: Starting capital
        """
        self.df = df.copy()
        self.initial_balance = initial_balance
    
    def simulate_trade_execution(
        self,
        prediction,
        confidence,
        entry_price,
        position_size=0.02,
        slippage_pct=0.0005,
        latency_candles=1,
        commission_pct=0.0005,
        market_impact_pct=0.0001
    ):
        """
        Simulate order execution
        
        Args:
            prediction: 1 for BUY, 0 for SELL
            confidence: Model confidence (0-1)
            entry_price: Current market price
            position_size: % of balance to risk
            slippage_pct: Price slippage (0.05% = 0.0005)
            latency_candles: How many candles delay before fill
            commission_pct: Broker commission
            market_impact_pct: Price impact of our order
            
        Returns: Effective fill price after all costs
        """
        
        fill_price = entry_price
        
        # 1. Market Impact - our order moves price
        if position_size > 0.01:  # Only for large orders
            fill_price *= (1 + market_impact_pct)
        
        # 2. Latency - we fill at worse price during delay
        if prediction == 1:  # BUY
            fill_price *= (1 + slippage_pct * (1 + latency_candles))
        else:  # SELL
            fill_price *= (1 - slippage_pct * (1 + latency_candles))
        
        # 3. Commission
        commission = fill_price * commission_pct
        
        return fill_price, commission
    
    def backtest_with_execution_costs(
        self,
        predictions,
        probabilities,
        returns,
        position_size=0.02,
        confidence_threshold=0.65,
        slippage_pct=0.0005,
        latency_candles=1,
        commission_pct=0.0005,
        verbose=True
    ):
        """
        Backtest with realistic execution costs
        
        Returns: Comparison of ideal vs realistic returns
        """
        
        if verbose:
            print("\n" + "="*70)
            print("EXECUTION SIMULATOR - REALISTIC COST ANALYSIS")
            print("="*70)
            print(f"Slippage:        {slippage_pct*100:.3f}%")
            print(f"Latency:         {latency_candles} candle(s)")
            print(f"Commission:      {commission_pct*100:.3f}%")
            print(f"Position Size:   {position_size*100:.1f}%\n")
        
        # Track both ideal and realistic PnL
        ideal_equity = self.initial_balance
        realistic_equity = self.initial_balance
        
        ideal_trades = 0
        realistic_trades = 0
        realistic_wins = 0
        
        total_commission = 0
        total_slippage = 0
        
        for i in range(len(predictions)):
            confidence = probabilities[i]
            prediction = predictions[i]
            actual_return = returns.iloc[i] if i < len(returns) else 0
            
            if confidence <= confidence_threshold:
                continue
            
            # Ideal scenario (no costs)
            if prediction == 1:
                ideal_return = actual_return
            else:
                ideal_return = -actual_return
            
            ideal_equity *= (1 + ideal_return * position_size)
            ideal_trades += 1
            
            # Realistic scenario (with costs)
            # Slippage reduces return
            slippage_cost = slippage_pct * (1 + latency_candles) * position_size
            commission_cost = commission_pct * position_size
            total_cost = slippage_cost + commission_cost
            
            realistic_return = ideal_return - total_cost
            
            realistic_equity *= (1 + realistic_return * position_size)
            realistic_trades += 1
            
            if realistic_return > 0:
                realistic_wins += 1
            
            total_commission += commission_cost
            total_slippage += slippage_cost
        
        # Calculate metrics
        ideal_return = (ideal_equity - self.initial_balance) / self.initial_balance
        realistic_return = (realistic_equity - self.initial_balance) / self.initial_balance
        
        cost_impact = ideal_return - realistic_return
        realistic_win_rate = realistic_wins / realistic_trades if realistic_trades > 0 else 0
        
        if verbose:
            print("RESULTS:")
            print("-"*70)
            print(f"Ideal (no costs):")
            print(f"  Final Balance:   ${ideal_equity:,.2f}")
            print(f"  Return:          {ideal_return*100:+.2f}%")
            print(f"  Trades:          {ideal_trades}\n")
            
            print(f"Realistic (with costs):")
            print(f"  Final Balance:   ${realistic_equity:,.2f}")
            print(f"  Return:          {realistic_return*100:+.2f}%")
            print(f"  Trade Count:     {realistic_trades}")
            print(f"  Win Rate:        {realistic_win_rate*100:.1f}%\n")
            
            print(f"Cost Impact:")
            print(f"  Total Commission: ${total_commission*self.initial_balance:,.2f}")
            print(f"  Total Slippage:   ${total_slippage*self.initial_balance:,.2f}")
            print(f"  Return Impact:   {cost_impact*100:.2f}%\n")
            
            print("-"*70)
            
            # Verdict
            if realistic_return > ideal_return * 0.95:
                print("✅ STRATEGY SURVIVES EXECUTION COSTS")
                print("   Profitable after realistic costs")
            elif realistic_return > 0:
                print("⚠️  MARGINAL - Profits reduced by costs")
                print("   Watch for slippage in live trading")
            else:
                print("❌ STRATEGY FAILS WITH EXECUTION COSTS")
                print("   NOT profitable after realistic costs")
                print("   Recommend: Backtesting only, do not trade live")
            
            print("="*70 + "\n")
        
        return {
            'ideal_return': ideal_return,
            'realistic_return': realistic_return,
            'cost_impact_pct': cost_impact * 100,
            'ideal_balance': ideal_equity,
            'realistic_balance': realistic_equity,
            'trades': realistic_trades,
            'win_rate': realistic_win_rate,
            'total_commission': total_commission * self.initial_balance,
            'total_slippage': total_slippage * self.initial_balance
        }
    
    def sensitivity_analysis(self, predictions, probabilities, returns, position_size=0.02, threshold=0.65):
        """
        Analyze sensitivity to different execution costs
        
        Shows how much different cost levels impact profitability
        """
        scenarios = [
            {'name': 'Best Case', 'slippage': 0.0001,  'commission': 0.0001, 'latency': 0},
            {'name': 'Good Broker', 'slippage': 0.0003, 'commission': 0.0002, 'latency': 1},
            {'name': 'Average', 'slippage': 0.0005,    'commission': 0.0005, 'latency': 1},
            {'name': 'Retail Trader', 'slippage': 0.001, 'commission': 0.001, 'latency': 2},
            {'name': 'Worst Case', 'slippage': 0.002, 'commission': 0.002, 'latency': 3},
        ]
        
        print("\n" + "="*70)
        print("EXECUTION COST SENSITIVITY ANALYSIS")
        print("="*70 + "\n")
        
        results = []
        
        for scenario in scenarios:
            result = self.backtest_with_execution_costs(
                predictions,
                probabilities,
                returns,
                position_size=position_size,
                confidence_threshold=threshold,
                slippage_pct=scenario['slippage'],
                latency_candles=scenario['latency'],
                commission_pct=scenario['commission'],
                verbose=False
            )
            
            result['scenario'] = scenario['name']
            results.append(result)
            
            print(f"{scenario['name']:20s}: {result['realistic_return']*100:+.2f}% return | {result['trades']} trades")
        
        print("\n" + "="*70)
        
        # Find breakeven cost level
        for i, result in enumerate(results):
            if result['realistic_return'] <= 0:
                print(f"⚠️  Strategy becomes unprofitable at: {scenarios[i]['name']}")
                break
        else:
            print("✅ Strategy remains profitable even in worst case")
        
        return pd.DataFrame(results)
