"""
Backtesting Engine
Real trading metrics: win rate, profit, drawdown, Sharpe ratio
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report


class BacktestingEngine:
    """Backtest trading strategy with real metrics"""
    
    def __init__(self, df, predictions, probabilities, returns, initial_balance=10000):
        """
        Args:
            df: Original dataframe with OHLCV
            predictions: Model predictions (0 or 1)
            probabilities: Prediction confidence (0-1)
            returns: Actual price returns for next period
            initial_balance: Starting capital
        """
        self.df = df.copy()
        self.predictions = predictions
        self.probabilities = probabilities
        self.returns = returns
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.trades = []
        self.equity_curve = []
    
    def run_backtest(
        self,
        confidence_threshold=0.7,
        position_size=0.02,
        stop_loss_pct=0.01,
        take_profit_pct=0.02,
        max_drawdown_stop=0.10,
        verbose=True
    ):
        """
        Run backtest with confidence threshold
        
        Args:
            confidence_threshold: Only trade if confidence > this (0.7 = 70%)
            position_size: Risk per trade as % of balance
            stop_loss_pct: Maximum loss per trade as a decimal
            take_profit_pct: Maximum profit per trade as a decimal
            max_drawdown_stop: Stop trading if drawdown exceeds this fraction
            verbose: Print progress and summary output
        """
        if verbose:
            print("\n" + "="*70)
            print("BACKTESTING ENGINE")
            print("="*70)
            print(f"Initial Balance: ${self.initial_balance:,.2f}")
            print(f"Confidence Threshold: {confidence_threshold*100:.0f}%")
            print(f"Position Size: {position_size*100:.0f}% of balance")
            print(f"Stop Loss: {stop_loss_pct*100:.2f}% | Profit Target: {take_profit_pct*100:.2f}%")
            print(f"Max Drawdown Stop: {max_drawdown_stop*100:.1f}%\n")
        
        equity = self.initial_balance
        trade_count = 0
        winning_trades = 0
        losing_trades = 0
        total_profit = 0
        peak_equity = equity
        max_drawdown = 0
        stopped_due_to_drawdown = False
        self.equity_curve = [equity]
        self.trades = []
        
        for i in range(len(self.predictions)):
            confidence = self.probabilities[i]
            prediction = self.predictions[i]
            actual_return = self.returns.iloc[i] if i < len(self.returns) else 0
            
            if confidence <= confidence_threshold:
                self.equity_curve.append(equity)
                continue
            
            if max_drawdown >= max_drawdown_stop:
                stopped_due_to_drawdown = True
                if verbose:
                    print(f"⛔ Stopped trading after drawdown exceeded {max_drawdown_stop*100:.1f}%")
                break
            
            position_value = equity * position_size
            trade_return_pct = actual_return if prediction == 1 else -actual_return
            trade_return_pct = min(max(trade_return_pct, -stop_loss_pct), take_profit_pct)
            trade_return = trade_return_pct * position_value
            equity += trade_return
            total_profit += trade_return
            
            if trade_return > 0:
                winning_trades += 1
            else:
                losing_trades += 1
            
            trade_count += 1
            
            if equity > peak_equity:
                peak_equity = equity
            else:
                drawdown = (peak_equity - equity) / peak_equity
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            self.trades.append({
                'index': i,
                'prediction': prediction,
                'confidence': confidence,
                'return_pct': trade_return_pct,
                'trade_profit': trade_return,
                'equity': equity
            })
            self.equity_curve.append(equity)
        
        final_balance = equity
        total_return = (final_balance - self.initial_balance) / self.initial_balance
        
        win_rate = winning_trades / trade_count if trade_count > 0 else 0
        avg_profit_per_trade = total_profit / trade_count if trade_count > 0 else 0
        average_trade_return_pct = (
            np.mean([t['return_pct'] for t in self.trades]) if self.trades else 0
        )
        
        gross_profit = sum(t['trade_profit'] for t in self.trades if t['trade_profit'] > 0)
        gross_loss = -sum(t['trade_profit'] for t in self.trades if t['trade_profit'] < 0)
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        if len(self.trades) > 1:
            trade_returns = [t['trade_profit'] for t in self.trades]
            sharpe_ratio = (
                np.mean(trade_returns) / np.std(trade_returns) * np.sqrt(252)
                if np.std(trade_returns) > 0 else 0
            )
        else:
            sharpe_ratio = 0
        
        if verbose:
            print(f"{'='*70}")
            print("BACKTEST RESULTS (Confidence > {:.0f}%)".format(confidence_threshold*100))
            print(f"{'='*70}\n")
            print(f"📊 ACCOUNT METRICS:")
            print(f"   Final Balance:        ${final_balance:,.2f}")
            print(f"   Total Return:         {total_return*100:.2f}%")
            print(f"   Total Profit:         ${total_profit:,.2f}\n")
            print(f"📈 TRADING METRICS:")
            print(f"   Total Trades:         {trade_count}")
            print(f"   Winning Trades:       {winning_trades}")
            print(f"   Losing Trades:        {losing_trades}")
            print(f"   Win Rate:             {win_rate*100:.2f}%")
            print(f"   Avg Profit/Trade:     ${avg_profit_per_trade:,.2f}")
            print(f"   Avg Return/Trade:     {average_trade_return_pct*100:.2f}%\n")
            print(f"📉 RISK METRICS:")
            print(f"   Max Drawdown:         {max_drawdown*100:.2f}%")
            print(f"   Sharpe Ratio:         {sharpe_ratio:.2f}")
            print(f"   Profit Factor:        {profit_factor:.2f}")
            print(f"   Stopped Early:        {stopped_due_to_drawdown}")
            print(f"\n{'='*70}\n")
        
        return {
            'final_balance': final_balance,
            'total_return': total_return,
            'total_profit': total_profit,
            'trades': trade_count,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_profit_per_trade': avg_profit_per_trade,
            'avg_trade_return_pct': average_trade_return_pct,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'profit_factor': profit_factor,
            'stopped_due_to_drawdown': stopped_due_to_drawdown
        }
    
    def optimize_confidence_threshold(
        self,
        position_size=0.02,
        stop_loss_pct=0.01,
        take_profit_pct=0.02,
        max_drawdown_stop=0.10
    ):
        """Test different confidence thresholds"""
        print("\n" + "="*70)
        print("CONFIDENCE THRESHOLD OPTIMIZATION")
        print("="*70)
        print("Testing different confidence levels...\n")
        
        thresholds = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]
        results = []
        
        for threshold in thresholds:
            stats = self.run_backtest(
                confidence_threshold=threshold,
                position_size=position_size,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct,
                max_drawdown_stop=max_drawdown_stop,
                verbose=False
            )
            results.append({
                'threshold': threshold,
                'trades': stats['trades'],
                'win_rate': stats['win_rate'],
                'return': stats['total_return'],
                'final_balance': stats['final_balance'],
                'max_drawdown': stats['max_drawdown'],
                'sharpe_ratio': stats['sharpe_ratio'],
                'profit_factor': stats['profit_factor'],
                'stopped_early': stats['stopped_due_to_drawdown']
            })
        
        results_df = pd.DataFrame(results)
        
        print(results_df.to_string(index=False))
        print(f"\n{'='*70}")
        print("Recommendation:")
        
        best = results_df.loc[results_df['return'].idxmax()]
        print(f"✅ Best Threshold: {best['threshold']:.2f}")
        print(f"   Return: {best['return']*100:.2f}%")
        print(f"   Trade Count: {int(best['trades'])}")
        print(f"   Win Rate: {best['win_rate']*100:.2f}%")
        print(f"   Max Drawdown: {best['max_drawdown']*100:.2f}%")
        print(f"   Profit Factor: {best['profit_factor']:.2f}")
        print(f"   Stopped Early: {best['stopped_early']}")
        
        return results_df
    
    def plot_equity_curve(self):
        """Plot equity curve"""
        plt.figure(figsize=(14, 6))
        plt.plot(self.equity_curve, linewidth=2, label='Strategy Equity')
        plt.axhline(y=self.initial_balance, color='r', linestyle='--', label='Starting Balance')
        plt.xlabel('Time Period')
        plt.ylabel('Account Balance ($)')
        plt.title('Strategy Equity Curve')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('../outputs/plots/equity_curve.png', dpi=150)
        plt.close()
        
        print("✅ Equity curve plot saved!")


def main():
    """Run backtest"""
    from feature_engineering import FeatureEngineer
    from target_variable import TargetVariable
    from data_preparation import DataPipeline
    from model_training import ModelTrainer
    import pandas as pd
    
    # Load data
    print("📊 Loading data...")
    df = pd.read_csv('../data/raw/AAPL_10min_generated_data.csv')
    
    # Generate features and targets
    print("🔧 Generating features and targets...")
    engineer = FeatureEngineer(df)
    features = engineer.generate_all_features()
    targets = TargetVariable.create_all_targets(df)
    
    # Prepare data
    print("📈 Preparing data...")
    pipeline = DataPipeline(features, targets)
    X_train, X_test, y_train, y_test = pipeline.prepare(
        target_col='target_direction'
    )
    
    # Train model
    print("🤖 Training model...")
    trainer = ModelTrainer()
    trainer.train_all_models(X_train, y_train, X_test, y_test)
    
    # Get predictions
    best_model = trainer.models['xgboost']
    predictions = best_model.predict(X_test)
    probabilities = best_model.predict_proba(X_test)[:, 1]
    
    # Get returns
    returns = targets['price_change_pct'].iloc[len(X_train):]
    
    # Run backtest
    backtest = BacktestingEngine(
        df.iloc[len(X_train):],
        predictions,
        probabilities,
        returns,
        initial_balance=10000
    )
    
    # Test different confidence thresholds
    results = backtest.optimize_confidence_threshold()
    
    # Run final backtest with best threshold
    best_threshold = results.loc[results['return'].idxmax()]['threshold']
    backtest_results = backtest.run_backtest(confidence_threshold=best_threshold)
    
    # Plot equity curve
    backtest.plot_equity_curve()
    
    return backtest_results


if __name__ == "__main__":
    results = main()
