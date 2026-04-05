"""
Alpha Validation: Compare model against naive baselines

Baselines:
1. Buy & Hold - simple hold forever
2. Random - 50/50 coin flip
3. Always UP - always predict direction 1
4. Always DOWN - always predict direction 0
"""

import pandas as pd
import numpy as np
from backtesting import BacktestingEngine


class BaselineComparison:
    """Compare ML model against naive baselines"""
    
    def __init__(self, df, returns, initial_balance=10000):
        """
        Args:
            df: OHLCV dataframe
            returns: Series of price changes (next period return)
            initial_balance: Starting capital
        """
        self.df = df
        self.returns = returns
        self.initial_balance = initial_balance
        self.results = {}
    
    def buy_and_hold(self):
        """Buy at start, hold until end"""
        # Take all returns
        total_return = np.sum(self.returns)
        final_balance = self.initial_balance * (1 + total_return)
        
        winning_trades = len(self.returns[self.returns > 0])
        total_trades = len(self.returns)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Sharpe
        if np.std(self.returns) > 0:
            sharpe = (np.mean(self.returns) / np.std(self.returns)) * np.sqrt(252)
        else:
            sharpe = 0
        
        # Max drawdown
        equity_curve = [self.initial_balance]
        equity = self.initial_balance
        for ret in self.returns:
            equity *= (1 + ret)
            equity_curve.append(equity)
        
        peak = self.initial_balance
        max_dd = 0
        for eq in equity_curve:
            if eq > peak:
                peak = eq
            else:
                dd = (peak - eq) / peak
                max_dd = max(max_dd, dd)
        
        return {
            'strategy': 'Buy & Hold',
            'final_balance': final_balance,
            'total_return': total_return,
            'trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd
        }
    
    def random_walk(self, seed=42):
        """Random 50/50 predictions"""
        np.random.seed(seed)
        predictions = np.random.randint(0, 2, len(self.returns))
        
        equity = self.initial_balance
        winning_trades = 0
        trade_returns = []
        
        for i, ret in enumerate(self.returns):
            if predictions[i] == 1:
                trade_ret = ret
            else:
                trade_ret = -ret
            
            equity *= (1 + trade_ret * 0.02)  # 2% position size
            trade_returns.append(trade_ret * 0.02)
            
            if trade_ret > 0:
                winning_trades += 1
        
        total_return = (equity - self.initial_balance) / self.initial_balance
        win_rate = winning_trades / len(predictions) if len(predictions) > 0 else 0
        
        if len(trade_returns) > 0 and np.std(trade_returns) > 0:
            sharpe = (np.mean(trade_returns) / np.std(trade_returns)) * np.sqrt(252)
        else:
            sharpe = 0
        
        return {
            'strategy': 'Random 50/50',
            'final_balance': equity,
            'total_return': total_return,
            'trades': len(predictions),
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe,
            'max_drawdown': 0.0  # Placeholder
        }
    
    def always_up(self):
        """Always predict UP (direction 1)"""
        equity = self.initial_balance
        winning_trades = 0
        trade_returns = []
        
        for ret in self.returns:
            trade_ret = ret  # Always take the return (predict UP)
            equity *= (1 + trade_ret * 0.02)
            trade_returns.append(trade_ret * 0.02)
            
            if trade_ret > 0:
                winning_trades += 1
        
        total_return = (equity - self.initial_balance) / self.initial_balance
        win_rate = winning_trades / len(self.returns) if len(self.returns) > 0 else 0
        
        if len(trade_returns) > 0 and np.std(trade_returns) > 0:
            sharpe = (np.mean(trade_returns) / np.std(trade_returns)) * np.sqrt(252)
        else:
            sharpe = 0
        
        return {
            'strategy': 'Always UP',
            'final_balance': equity,
            'total_return': total_return,
            'trades': len(self.returns),
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe,
            'max_drawdown': 0.0
        }
    
    def always_down(self):
        """Always predict DOWN (direction 0)"""
        equity = self.initial_balance
        winning_trades = 0
        trade_returns = []
        
        for ret in self.returns:
            trade_ret = -ret  # Always take opposite (predict DOWN)
            equity *= (1 + trade_ret * 0.02)
            trade_returns.append(trade_ret * 0.02)
            
            if trade_ret > 0:
                winning_trades += 1
        
        total_return = (equity - self.initial_balance) / self.initial_balance
        win_rate = winning_trades / len(self.returns) if len(self.returns) > 0 else 0
        
        if len(trade_returns) > 0 and np.std(trade_returns) > 0:
            sharpe = (np.mean(trade_returns) / np.std(trade_returns)) * np.sqrt(252)
        else:
            sharpe = 0
        
        return {
            'strategy': 'Always DOWN',
            'final_balance': equity,
            'total_return': total_return,
            'trades': len(self.returns),
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe,
            'max_drawdown': 0.0
        }
    
    def run_comparison(self, model_result=None):
        """Run all baselines and compare"""
        print("\n" + "="*70)
        print("BASELINE COMPARISON - ALPHA VALIDATION")
        print("="*70 + "\n")
        
        results = []
        
        # Run baselines
        bh = self.buy_and_hold()
        results.append(bh)
        
        rand = self.random_walk()
        results.append(rand)
        
        aup = self.always_up()
        results.append(aup)
        
        adown = self.always_down()
        results.append(adown)
        
        # Add model if provided
        if model_result is not None:
            model_result['strategy'] = 'ML Model'
            results.append(model_result)
        
        # Create comparison dataframe
        comparison_df = pd.DataFrame(results)
        comparison_df = comparison_df.sort_values('sharpe_ratio', ascending=False)
        
        # Display
        print(comparison_df[['strategy', 'total_return', 'win_rate', 'sharpe_ratio', 'max_drawdown']].to_string(index=False))
        
        # Analysis
        print("\n" + "="*70)
        print("ALPHA VALIDATION REPORT")
        print("="*70 + "\n")
        
        if model_result is not None:
            best_baseline = comparison_df[comparison_df['strategy'] != 'ML Model'].iloc[0]
            model_row = comparison_df[comparison_df['strategy'] == 'ML Model'].iloc[0]
            
            print(f"Best Baseline: {best_baseline['strategy']}")
            print(f"  Return: {best_baseline['total_return']*100:.2f}%")
            print(f"  Sharpe: {best_baseline['sharpe_ratio']:.2f}\n")
            
            print(f"ML Model:")
            print(f"  Return: {model_row['total_return']*100:.2f}%")
            print(f"  Sharpe: {model_row['sharpe_ratio']:.2f}\n")
            
            # Verdict
            if model_row['sharpe_ratio'] > best_baseline['sharpe_ratio']:
                print("✅ MODEL HAS ALPHA - Outperforms all baselines!")
            elif model_row['total_return'] > best_baseline['total_return']:
                print("✅ MODEL HAS ALPHA - Higher return than baselines")
            else:
                print("❌ NO ALPHA - Model underperforms baselines")
                print("   Recommendation: Back to feature engineering")
        else:
            print("Run with model_result to compare against ML model")
        
        print("="*70 + "\n")
        
        return comparison_df
