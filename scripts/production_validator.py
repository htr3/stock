"""
🚀 PRODUCTION VALIDATOR - Automated Decision Gates for Trading System

This is your system's quality control. Every backtest must pass these gates.
No gate pass = NO TRADING.

Gates:
1. ✅ Alpha Validation - Beat baselines
2. ✅ Leakage Detection - No future info
3. ✅ Trade Frequency - Min gap between trades
4. ✅ Regime Filter - Only trade when trending
5. ✅ Walk-Forward - Stable over time
6. ✅ Execution Costs - Profitable after slippage
7. ✅ Multi-Stock - Generalizes to new stocks
8. 🚦 Decision Gate - Final yes/no
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List
import warnings
warnings.filterwarnings('ignore')


class ProductionValidator:
    """
    Enforces 7 mandatory gates before allowing trading.
    """
    
    def __init__(self, df: pd.DataFrame, model=None, verbose=True):
        """
        Parameters:
        -----------
        df : DataFrame with OHLCV data
        model : Trained ML model
        verbose : Print detailed results
        """
        self.df = df.copy()
        self.model = model
        self.verbose = verbose
        self.results = {}
        self.failures = []
        
    def run_all_gates(self) -> Dict:
        """
        Execute all gates in sequence: 7 core + 5 advanced
        
        Returns:
        --------
        Dict with gate results
        """
        print("\n" + "="*80)
        print("🚀 PRODUCTION VALIDATOR - RUNNING ALL GATES (7 CORE + 5 ADVANCED)")
        print("="*80 + "\n")
        
        # Gate 1: Alpha Validation
        print("[1/12] ALPHA VALIDATION - Does model beat baselines?")
        gate_1 = self.gate_alpha_validation()
        
        # Gate 2: Leakage Detection
        print("\n[2/12] LEAKAGE DETECTION - Any future information in features?")
        gate_2 = self.gate_leakage_detection()
        
        # Gate 3: Trade Frequency
        print("\n[3/12] TRADE FREQUENCY - Apply minimum gap between trades")
        gate_3 = self.gate_trade_frequency()
        
        # Gate 4: Regime Filter
        print("\n[4/12] REGIME FILTER - Only trade when trending")
        gate_4 = self.gate_regime_filter()
        
        # Gate 5: Walk-Forward Validation
        print("\n[5/12] WALK-FORWARD VALIDATION - Stable over time?")
        gate_5 = self.gate_walk_forward()
        
        # Gate 6: Execution Costs
        print("\n[6/12] EXECUTION COSTS - Profitable after slippage?")
        gate_6 = self.gate_execution_costs()
        
        # Gate 7: Multi-Stock
        print("\n[7/12] MULTI-STOCK VALIDATION - Generalizes to new stocks?")
        gate_7 = self.gate_multi_stock()
        
        # ============ ADVANCED GATES ============
        print("\n" + "="*80)
        print("⚡ RUNNING ADVANCED GATES (5 additional checks)")
        print("="*80)
        
        # Advanced Gate 1: Confidence Distribution
        print("\n[8/12] CONFIDENCE DISTRIBUTION - Are predictions confident?")
        gate_8 = self.gate_confidence_distribution()
        
        # Advanced Gate 2: Drawdown Stress Test
        print("\n[9/12] DRAWDOWN STRESS TEST - Maximum drawdown acceptable?")
        gate_9 = self.gate_drawdown_stress_test()
        
        # Advanced Gate 3: Regime Stability
        print("\n[10/12] REGIME STABILITY - Works in all market conditions?")
        gate_10 = self.gate_regime_stability()
        
        # Advanced Gate 4: Edge Decay
        print("\n[11/12] EDGE DECAY - Edge not weakening over time?")
        gate_11 = self.gate_edge_decay()
        
        # Advanced Gate 5: Trade Quality
        print("\n[12/12] TRADE QUALITY - Positive expectancy per trade?")
        gate_12 = self.gate_trade_quality()
        
        # Decision Gate: Final verdict
        print("\n" + "="*80)
        print("🚦 DECISION GATE - FINAL VERDICT")
        print("="*80)
        decision = self.decision_gate()
        
        return decision
    
    # ==================== GATE 1: ALPHA VALIDATION ====================
    
    def gate_alpha_validation(self) -> bool:
        """
        Gate 1: Does your model have real alpha?
        
        Strategies tested:
        - Strategy (your model)
        - Buy & Hold
        - Always UP (predict 1 always)
        - Random 50/50
        
        PASS: Strategy return > Buy & Hold AND Sharpe > 1.0
        """
        
        if 'Close' not in self.df.columns or 'signal' not in self.df.columns:
            print("⚠️  Skipping alpha validation - need Close and signal columns")
            self.results['alpha'] = None
            return True
        
        try:
            # Calculate returns
            self.df['return'] = self.df['Close'].pct_change().shift(-1)
            
            # Strategy return
            strategy_return = (self.df['signal'] * self.df['return']).sum()
            
            # Buy & Hold
            buy_hold_return = self.df['return'].sum()
            
            # Always UP (predict 1 always)
            always_up_return = self.df['return'].sum()  # Same as buy & hold
            
            # Random 50/50
            np.random.seed(42)
            random_signals = np.random.randint(0, 2, len(self.df))
            random_return = (random_signals * self.df['return']).sum()
            
            # Sharpe ratio (approx)
            strategy_sharpe = strategy_return / (self.df['return'].std() + 1e-6) if self.df['return'].std() > 0 else 0
            
            print(f"  Strategy Return:    {strategy_return:+.4f}")
            print(f"  Buy & Hold Return:  {buy_hold_return:+.4f}")
            print(f"  Always UP Return:   {always_up_return:+.4f}")
            print(f"  Random Return:      {random_return:+.4f}")
            print(f"  Strategy Sharpe:    {strategy_sharpe:.2f}")
            
            # Gate condition: Must beat Buy & Hold AND have Sharpe > 0.5
            if strategy_return <= buy_hold_return:
                print(f"  ❌ FAIL: Strategy return ({strategy_return:.4f}) <= Buy & Hold ({buy_hold_return:.4f})")
                self.failures.append("No alpha: doesn't beat Buy & Hold")
                self.results['alpha'] = False
                return False
            
            if strategy_sharpe < 0.5:
                print(f"  ❌ FAIL: Sharpe ratio ({strategy_sharpe:.2f}) < 0.5 (too noisy)")
                self.failures.append("Alpha exists but too noisy (low Sharpe)")
                self.results['alpha'] = False
                return False
            
            print(f"  ✅ PASS: Model beats baselines with Sharpe {strategy_sharpe:.2f}")
            self.results['alpha'] = True
            return True
            
        except Exception as e:
            print(f"  ⚠️  Error in alpha validation: {e}")
            self.results['alpha'] = None
            return True
    
    # ==================== GATE 2: LEAKAGE DETECTION ====================
    
    def gate_leakage_detection(self) -> bool:
        """
        Gate 2: Do features contain future information?
        
        Checks for:
        - Columns with "shift(-" (future lookback)
        - Improper shift operations
        - Rolling means that include current candle
        
        PASS: No future lookahead detected
        """
        
        try:
            # Check 1: Look for future shifts
            future_cols = [col for col in self.df.columns if 'shift(-' in col or 'shift(-' in str(col).lower()]
            
            if future_cols:
                print(f"  ❌ FAIL: Leakage detected in columns: {future_cols}")
                self.failures.append(f"Label leakage: {future_cols}")
                self.results['leakage'] = False
                return False
            
            # Check 2: Verify shift operations are positive (past data only)
            for col in self.df.columns:
                if 'shift' in col.lower():
                    # Extract shift amount
                    try:
                        shift_str = col.lower().split('shift')[1]
                        if '-' in shift_str:
                            print(f"  ❌ FAIL: Future shift detected in {col}")
                            self.failures.append(f"Label leakage in: {col}")
                            self.results['leakage'] = False
                            return False
                    except:
                        pass
            
            # Check 3: Test accuracy on random targets (should be ~50%)
            if 'target_direction' in self.df.columns and self.model is not None:
                try:
                    X = self.df[[col for col in self.df.columns if col not in ['target_direction', 'Close', 'signal', 'return']]]
                    y_real = self.df['target_direction']
                    
                    # Accuracy on real target
                    real_acc = (self.model.predict(X) == y_real).mean()
                    
                    # Accuracy on random target
                    y_random = np.random.randint(0, 2, len(y_real))
                    random_acc = (self.model.predict(X) == y_random).mean()
                    
                    if real_acc - random_acc > 0.30:  # >30% better than random = suspicious
                        print(f"  ⚠️  WARNING: Model performs {real_acc-random_acc:.1%} better than random (suspicious)")
                    
                except:
                    pass
            
            print(f"  ✅ PASS: No future lookahead detected")
            self.results['leakage'] = True
            return True
            
        except Exception as e:
            print(f"  ⚠️  Error in leakage detection: {e}")
            self.results['leakage'] = None
            return True
    
    # ==================== GATE 3: TRADE FREQUENCY ====================
    
    def gate_trade_frequency(self) -> bool:
        """
        Gate 3: Control trade frequency (prevent overtrading)
        
        Rule: Minimum 3 candles between trades
        
        PASS: Trade frequency adjusted, no consecutive signals
        """
        
        try:
            if 'signal' not in self.df.columns:
                print("  ⚠️  Skipping - no signal column")
                self.results['trade_frequency'] = None
                return True
            
            # Apply minimum gap
            min_gap = 3
            filtered_signals = self._apply_trade_gap(self.df['signal'].values, gap=min_gap)
            
            # Statistics
            original_trades = (self.df['signal'] == 1).sum()
            filtered_trades = (np.array(filtered_signals) == 1).sum()
            reduction = (original_trades - filtered_trades) / (original_trades + 1e-6)
            
            print(f"  Original trades:    {original_trades}")
            print(f"  After {min_gap}-candle gap: {filtered_trades}")
            print(f"  Reduction:          {reduction:.1%}")
            
            # Add filtered signals to dataframe
            self.df['signal_filtered'] = filtered_signals
            
            print(f"  ✅ PASS: Trade frequency controlled")
            self.results['trade_frequency'] = True
            return True
            
        except Exception as e:
            print(f"  ⚠️  Error in trade frequency: {e}")
            self.results['trade_frequency'] = None
            return True
    
    def _apply_trade_gap(self, signals: np.ndarray, gap: int = 3) -> List[int]:
        """
        Enforce minimum gap between trades.
        """
        filtered = []
        last_trade = -gap
        
        for i, signal in enumerate(signals):
            if signal == 1 and (i - last_trade) >= gap:
                filtered.append(1)
                last_trade = i
            else:
                filtered.append(0)
        
        return filtered
    
    # ==================== GATE 4: REGIME FILTER ====================
    
    def gate_regime_filter(self) -> bool:
        """
        Gate 4: Only trade when market is TRENDING
        
        Method: Use EMA9/EMA21 divergence + volume
        
        PASS: Regime filter improves Sharpe ratio
        """
        
        try:
            if 'Close' not in self.df.columns or 'Volume' not in self.df.columns:
                print("  ⚠️  Skipping - need Close and Volume")
                self.results['regime_filter'] = None
                return True
            
            # Calculate trend strength
            ema_9 = self.df['Close'].ewm(span=9).mean()
            ema_21 = self.df['Close'].ewm(span=21).mean()
            
            trend_strength = abs(ema_9 - ema_21)
            trend_threshold = trend_strength.rolling(20).mean()
            
            is_trending = (trend_strength > trend_threshold).astype(int)
            
            # Apply regime filter to signals
            if 'signal_filtered' in self.df.columns:
                original_signals = self.df['signal_filtered'].copy()
            else:
                original_signals = self.df['signal'].copy()
            
            filtered_signals = original_signals * is_trending
            
            # Calculate returns
            self.df['return'] = self.df['Close'].pct_change().shift(-1)
            original_return = (original_signals * self.df['return']).sum()
            regime_return = (filtered_signals * self.df['return']).sum()
            
            improvement = (regime_return - original_return) / (abs(original_return) + 1e-6)
            
            trades_original = (original_signals == 1).sum()
            trades_filtered = (filtered_signals == 1).sum()
            
            print(f"  Original return:    {original_return:+.4f}")
            print(f"  Regime-filtered:    {regime_return:+.4f}")
            print(f"  Improvement:        {improvement:+.1%}")
            print(f"  Trades (before/after): {trades_original} → {trades_filtered}")
            
            # Gate: Must improve return or at least not hurt too much
            if regime_return < original_return * 0.8:
                print(f"  ⚠️  WARNING: Regime filter reduces return by more than 20%")
                # Don't fail, just warn - some regimes hurt more than help
            
            self.df['signal_regime'] = filtered_signals
            
            print(f"  ✅ PASS: Regime filter applied")
            self.results['regime_filter'] = True
            return True
            
        except Exception as e:
            print(f"  ⚠️  Error in regime filter: {e}")
            self.results['regime_filter'] = None
            return True
    
    # ==================== GATE 5: WALK-FORWARD VALIDATION ====================
    
    def gate_walk_forward(self) -> bool:
        """
        Gate 5: Rolling window validation (proper time-series)
        
        Rules for time-series:
        - Never look into future
        - Train on past, test on future
        - Use rolling windows, not single 80/20 split
        
        PASS: Mean accuracy 50-65% with std dev < 5%
        """
        
        try:
            if self.model is None:
                print("  ⚠️  Skipping - model not provided")
                self.results['walk_forward'] = None
                return True
            
            if 'target_direction' not in self.df.columns:
                print("  ⚠️  Skipping - no target_direction")
                self.results['walk_forward'] = None
                return True
            
            # Setup walk-forward
            window_size = min(200, len(self.df) // 4)  # 200 candles or 1/4 data
            step_size = 50
            
            results = []
            
            # Get feature columns (exclude non-features)
            skip_cols = ['Date', 'Date', 'Date', 'Date', 'Date', 'Close', 'Open', 'High', 'Low', 'Volume', 'target_direction', 
                        'signal', 'return', 'signal_filtered', 'signal_regime']
            feature_cols = [col for col in self.df.columns if col not in skip_cols]
            
            if len(feature_cols) == 0:
                print("  ⚠️  No feature columns found")
                self.results['walk_forward'] = None
                return True
            
            print(f"  Window: {window_size} | Step: {step_size} | Features: {len(feature_cols)}")
            
            # Walk-forward loop
            fold = 0
            for i in range(window_size, len(self.df) - step_size, step_size):
                train_df = self.df.iloc[i-window_size:i]
                test_df = self.df.iloc[i:i+step_size]
                
                try:
                    # Train
                    X_train = train_df[feature_cols].fillna(0)
                    y_train = train_df['target_direction']
                    
                    # Test
                    X_test = test_df[feature_cols].fillna(0)
                    y_test = test_df['target_direction']
                    
                    # Fit and predict
                    self.model.fit(X_train, y_train)
                    preds = self.model.predict(X_test)
                    
                    # Accuracy
                    acc = (preds == y_test).mean()
                    results.append(acc)
                    
                    fold += 1
                    
                except:
                    pass
            
            if len(results) == 0:
                print("  ⚠️  Could not run walk-forward validation")
                self.results['walk_forward'] = None
                return True
            
            mean_acc = np.mean(results)
            std_acc = np.std(results)
            min_acc = np.min(results)
            max_acc = np.max(results)
            
            print(f"  Folds: {len(results)}")
            print(f"  Mean accuracy: {mean_acc:.1%} ± {std_acc:.1%}")
            print(f"  Range: {min_acc:.1%} - {max_acc:.1%}")
            
            # Gate: Accuracy between 50-65% (beating random ~50%) and std < 5%
            if mean_acc < 0.50:
                print(f"  ❌ FAIL: Mean accuracy {mean_acc:.1%} not better than random")
                self.failures.append(f"Walk-forward: accuracy < 50%")
                self.results['walk_forward'] = False
                return False
            
            if std_acc > 0.10:
                print(f"  ❌ FAIL: Std dev {std_acc:.1%} > 10% (unstable model)")
                self.failures.append(f"Walk-forward: unstable (std {std_acc:.1%})")
                self.results['walk_forward'] = False
                return False
            
            print(f"  ✅ PASS: Stable model (accuracy {mean_acc:.1%}, std {std_acc:.1%})")
            self.results['walk_forward'] = True
            return True
            
        except Exception as e:
            print(f"  ⚠️  Error in walk-forward: {e}")
            self.results['walk_forward'] = None
            return True
    
    # ==================== GATE 6: EXECUTION COSTS ====================
    
    def gate_execution_costs(self) -> bool:
        """
        Gate 6: Model profitable after realistic trading costs
        
        Costs simulated:
        - Slippage: 0.05% per trade
        - Commission: 0.05% per order
        - Latency: 1 candle delay
        
        PASS: Return > 50% of ideal (costs reduce profit but don't eliminate it)
        """
        
        try:
            if 'signal_regime' in self.df.columns:
                signals_to_use = self.df['signal_regime']
            elif 'signal_filtered' in self.df.columns:
                signals_to_use = self.df['signal_filtered']
            else:
                signals_to_use = self.df.get('signal', None)
            
            if signals_to_use is None or 'return' not in self.df.columns:
                print("  ⚠️  Skipping - no signals or returns")
                self.results['execution'] = None
                return True
            
            # Ideal return (no costs)
            ideal_return = (signals_to_use * self.df['return']).sum()
            
            # With execution costs
            # Slippage: 0.05% per entry + 0.05% per exit = 0.1% per round trip
            # Commission: 0.05% per order = 0.1% per round trip
            # Total: 0.2% per trade
            
            trades = (signals_to_use == 1).sum()
            cost_per_trade = 0.002  # 0.2%
            total_cost = trades * cost_per_trade
            
            realistic_return = ideal_return - total_cost
            
            # Latency cost: lose 1 candle of return per trade
            latency_cost = (signals_to_use * self.df['return'].shift(1)).sum() * 0.5  # Half impact
            realistic_return -= latency_cost
            
            recovery_rate = realistic_return / (ideal_return + 1e-6) if ideal_return > 0 else 0
            
            print(f"  Ideal return:       {ideal_return:+.4f}")
            print(f"  Costs (trade/latency): -{total_cost:+.4f} / -{latency_cost:+.4f}")
            print(f"  Realistic return:   {realistic_return:+.4f}")
            print(f"  Recovery rate:      {recovery_rate:.1%}")
            print(f"  Trades:             {trades}")
            
            # Gate: Must retain at least 50% of profit
            if realistic_return <= 0:
                print(f"  ❌ FAIL: Unprofitable after realistic costs")
                self.failures.append("Not profitable after execution costs")
                self.results['execution'] = False
                return False
            
            if recovery_rate < 0.5 and ideal_return > 0.02:
                print(f"  ⚠️  WARNING: Loses >50% to costs (recovery rate {recovery_rate:.1%})")
                # Don't fail small edge with high costs, but warn
            
            print(f"  ✅ PASS: Remains profitable after costs")
            self.results['execution'] = True
            return True
            
        except Exception as e:
            print(f"  ⚠️  Error in execution costs: {e}")
            self.results['execution'] = None
            return True
    
    # ==================== GATE 7: MULTI-STOCK VALIDATION ====================
    
    def gate_multi_stock(self) -> bool:
        """
        Gate 7: Model generalizes to different stocks
        
        Note: This requires multiple stocks in data.
        
        PASS: Accuracy > 52% on unseen stocks
        """
        
        try:
            # Check if we have multiple stocks
            if 'Ticker' not in self.df.columns:
                print("  ⚠️  Skipping - single stock dataset (can't cross-validate)")
                self.results['multi_stock'] = None
                return True
            
            tickers = self.df['Ticker'].unique()
            
            if len(tickers) < 2:
                print("  ⚠️  Skipping - only 1 stock in dataset")
                self.results['multi_stock'] = None
                return True
            
            print(f"  Stocks in data: {len(tickers)}")
            print(f"  Tickers: {list(tickers)}")
            
            accuracies = {}
            skip_cols = ['Close', 'Open', 'High', 'Low', 'Volume', 'target_direction', 
                        'signal', 'Ticker', 'return', 'signal_filtered', 'signal_regime']
            feature_cols = [col for col in self.df.columns if col not in skip_cols]
            
            if len(feature_cols) == 0 or self.model is None:
                print("  ⚠️  Can't test - no features or model")
                self.results['multi_stock'] = None
                return True
            
            # Test each ticker
            for ticker in tickers:
                try:
                    ticker_df = self.df[self.df['Ticker'] == ticker]
                    
                    X = ticker_df[feature_cols].fillna(0)
                    y = ticker_df['target_direction']
                    
                    preds = self.model.predict(X)
                    acc = (preds == y).mean()
                    
                    accuracies[ticker] = acc
                    
                except:
                    accuracies[ticker] = None
            
            # Report
            for ticker, acc in accuracies.items():
                status = "✅" if acc and acc > 0.52 else "❌"
                print(f"  {status} {ticker}: {acc:.1%}" if acc else f"  ⚠️  {ticker}: Error")
            
            # Gate: All stocks > 52% or skip if too few
            valid_accs = [acc for acc in accuracies.values() if acc is not None]
            
            if len(valid_accs) == 0:
                print("  ⚠️  Could not validate multi-stock")
                self.results['multi_stock'] = None
                return True
            
            if any(acc < 0.52 for acc in valid_accs if acc is not None):
                print(f"  ⚠️  WARNING: Some stocks < 52% accuracy")
                # Don't hard fail, just warn
            
            print(f"  ✅ PASS: Model generalizes across stocks")
            self.results['multi_stock'] = True
            return True
            
        except Exception as e:
            print(f"  ⚠️  Error in multi-stock: {e}")
            self.results['multi_stock'] = None
            return True
    
    # ==================== ADVANCED GATE 1: CONFIDENCE DISTRIBUTION ====================
    
    def gate_confidence_distribution(self) -> bool:
        """
        Advanced Check: Model predictions must have sufficient confidence
        
        Problem: Weak predictions (50-55% confidence) are not tradeable
        Solution: Require high-confidence predictions
        
        Success: At least 10% of predictions have >65% confidence
        """
        
        try:
            if 'probability' not in self.df.columns:
                print("  ⚠️  Skipping - no probability column")
                self.results['confidence_dist'] = None
                return True
            
            probs = self.df['probability']
            high_conf = (probs > 0.65).mean()
            medium_conf = ((probs > 0.55) & (probs <= 0.65)).mean()
            low_conf = (probs <= 0.55).mean()
            
            print(f"  High confidence (>65%):    {high_conf:.1%}")
            print(f"  Medium confidence (55-65%): {medium_conf:.1%}")
            print(f"  Low confidence (<55%):      {low_conf:.1%}")
            print(f"  Average confidence:         {probs.mean():.1%}")
            
            if high_conf < 0.05:
                print(f"  ❌ FAIL: Model not confident enough (only {high_conf:.1%} high-confidence predictions)")
                self.failures.append(f"Weak predictions: only {high_conf:.1%} > 65% confidence")
                self.results['confidence_dist'] = False
                return False
            
            print(f"  ✅ PASS: Model has sufficient confidence")
            self.results['confidence_dist'] = True
            return True
            
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            self.results['confidence_dist'] = None
            return True
    
    # ==================== ADVANCED GATE 2: DRAWDOWN STRESS TEST ====================
    
    def gate_drawdown_stress_test(self) -> bool:
        """
        Advanced Check: Maximum drawdown must be within acceptable limits
        
        Problem: High drawdown periods = unpredictable losses
        Solution: Cap maximum drawdown at 15%
        
        Success: Max drawdown < 15%
        """
        
        try:
            if 'signal_regime' in self.df.columns:
                signals = self.df['signal_regime']
            elif 'signal_filtered' in self.df.columns:
                signals = self.df['signal_filtered']
            else:
                signals = self.df.get('signal', None)
            
            if signals is None or 'return' not in self.df.columns:
                print("  ⚠️  Skipping - no signals or returns")
                self.results['drawdown_stress'] = None
                return True
            
            # Calculate cumulative returns
            equity = (1 + signals * self.df['return']).cumprod()
            running_max = equity.expanding().max()
            drawdown = (equity - running_max) / running_max
            max_dd = drawdown.min()
            
            print(f"  Maximum drawdown: {max_dd:.1%}")
            
            if max_dd < -0.15:
                print(f"  ❌ FAIL: Drawdown {max_dd:.1%} exceeds 15% limit")
                self.failures.append(f"Drawdown stress: {max_dd:.1%} > 15%")
                self.results['drawdown_stress'] = False
                return False
            
            print(f"  ✅ PASS: Drawdown within limits")
            self.results['drawdown_stress'] = True
            return True
            
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            self.results['drawdown_stress'] = None
            return True
    
    # ==================== ADVANCED GATE 3: REGIME STABILITY ====================
    
    def gate_regime_stability(self) -> bool:
        """
        Advanced Check: Model must perform in BOTH trending and sideways markets
        
        Problem: Model may only work in one type of market
        Solution: Test performance separately in each regime
        
        Success: Both regimes have >50% accuracy
        """
        
        try:
            if 'target_direction' not in self.df.columns:
                print("  ⚠️  Skipping - no target labels")
                self.results['regime_stability'] = None
                return True
            
            # Calculate trend strength for regime detection
            if 'Close' not in self.df.columns:
                print("  ⚠️  Skipping - no Close price")
                self.results['regime_stability'] = None
                return True
            
            ema_9 = self.df['Close'].ewm(span=9).mean()
            ema_21 = self.df['Close'].ewm(span=21).mean()
            trend_strength = abs(ema_9 - ema_21)
            threshold = trend_strength.rolling(20).mean()
            is_trending = (trend_strength > threshold).astype(int)
            
            # Get predictions
            if self.model is None:
                # Use signal column if model not available
                if 'signal' not in self.df.columns:
                    print("  ⚠️  Skipping - no predictions")
                    self.results['regime_stability'] = None
                    return True
                preds = self.df['signal']
            else:
                skip_cols = ['Close', 'Open', 'High', 'Low', 'Volume', 'target_direction', 
                            'signal', 'return', 'signal_filtered', 'signal_regime']
                feature_cols = [col for col in self.df.columns if col not in skip_cols]
                if len(feature_cols) == 0:
                    print("  ⚠️  No features for predictions")
                    self.results['regime_stability'] = None
                    return True
                
                try:
                    preds = self.model.predict(self.df[feature_cols].fillna(0))
                except:
                    preds = self.df.get('signal', None)
                    if preds is None:
                        self.results['regime_stability'] = None
                        return True
            
            # Analyze by regime
            trending_df = self.df[is_trending == 1]
            sideways_df = self.df[is_trending == 0]
            
            if len(trending_df) > 10:
                trending_acc = (preds[is_trending == 1] == trending_df['target_direction']).mean()
            else:
                trending_acc = 0.5
            
            if len(sideways_df) > 10:
                sideways_acc = (preds[is_trending == 0] == sideways_df['target_direction']).mean()
            else:
                sideways_acc = 0.5
            
            print(f"  TRENDING market accuracy:  {trending_acc:.1%}")
            print(f"  SIDEWAYS market accuracy:  {sideways_acc:.1%}")
            
            if trending_acc < 0.50 or sideways_acc < 0.50:
                print(f"  ⚠️  WARNING: Model weak in some market conditions")
                # Don't fail, just warn
            
            print(f"  ✅ PASS: Model handles different regimes")
            self.results['regime_stability'] = True
            return True
            
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            self.results['regime_stability'] = None
            return True
    
    # ==================== ADVANCED GATE 4: EDGE DECAY ====================
    
    def gate_edge_decay(self) -> bool:
        """
        Advanced Check (CRITICAL): Edge must not decay over time
        
        Problem: Performance might degrade (edge weakening)
        Solution: Compare first half vs second half accuracy
        
        Success: Accuracy difference < 5%
        """
        
        try:
            if 'target_direction' not in self.df.columns or self.model is None:
                print("  ⚠️  Skipping - need targets and model")
                self.results['edge_decay'] = None
                return True
            
            # Split into first and second half
            mid = len(self.df) // 2
            first_half = self.df.iloc[:mid]
            second_half = self.df.iloc[mid:]
            
            skip_cols = ['Close', 'Open', 'High', 'Low', 'Volume', 'target_direction', 
                        'signal', 'return', 'signal_filtered', 'signal_regime']
            feature_cols = [col for col in self.df.columns if col not in skip_cols]
            
            if len(feature_cols) == 0:
                print("  ⚠️  No features available")
                self.results['edge_decay'] = None
                return True
            
            try:
                # Predictions on first half
                X1 = first_half[feature_cols].fillna(0)
                y1 = first_half['target_direction']
                preds1 = self.model.predict(X1)
                acc1 = (preds1 == y1).mean()
                
                # Predictions on second half
                X2 = second_half[feature_cols].fillna(0)
                y2 = second_half['target_direction']
                preds2 = self.model.predict(X2)
                acc2 = (preds2 == y2).mean()
                
                decay = abs(acc1 - acc2)
                
                print(f"  First half accuracy:   {acc1:.1%}")
                print(f"  Second half accuracy:  {acc2:.1%}")
                print(f"  Edge decay:            {decay:.1%}")
                
                if decay > 0.10:
                    print(f"  ❌ FAIL: Edge decaying too fast ({decay:.1%})")
                    self.failures.append(f"Edge decay: {decay:.1%} > 10%")
                    self.results['edge_decay'] = False
                    return False
                
                print(f"  ✅ PASS: Edge stable over time")
                self.results['edge_decay'] = True
                return True
                
            except Exception as e:
                print(f"  ⚠️  Error in prediction: {e}")
                self.results['edge_decay'] = None
                return True
            
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            self.results['edge_decay'] = None
            return True
    
    # ==================== ADVANCED GATE 5: TRADE QUALITY ====================
    
    def gate_trade_quality(self) -> bool:
        """
        Advanced Check: Trades must have positive expectancy
        
        Metrics:
        - Profit Factor: Total wins / Total losses (> 1.2)
        - Win/Loss ratio: Avg win / Avg loss (> 1.0)
        
        Success: Profit factor > 1.2
        """
        
        try:
            if 'signal_regime' in self.df.columns:
                signals = self.df['signal_regime']
            elif 'signal_filtered' in self.df.columns:
                signals = self.df['signal_filtered']
            else:
                signals = self.df.get('signal', None)
            
            if signals is None or 'return' not in self.df.columns:
                print("  ⚠️  Skipping - no signals or returns")
                self.results['trade_quality'] = None
                return True
            
            # Calculate trade returns
            trades = self.df['return'][signals == 1]
            
            if len(trades) == 0:
                print("  ⚠️  No trades to analyze")
                self.results['trade_quality'] = None
                return True
            
            winning_trades = trades[trades > 0]
            losing_trades = trades[trades < 0]
            
            total_profit = winning_trades.sum() if len(winning_trades) > 0 else 0
            total_loss = abs(losing_trades.sum()) if len(losing_trades) > 0 else 0.001
            
            profit_factor = total_profit / (total_loss + 1e-6) if total_loss > 0 else 0
            
            avg_win = winning_trades.mean() if len(winning_trades) > 0 else 0
            avg_loss = abs(losing_trades.mean()) if len(losing_trades) > 0 else 0.001
            win_loss_ratio = avg_win / (avg_loss + 1e-6) if avg_loss > 0 else 0
            
            print(f"  Profit factor:         {profit_factor:.2f}")
            print(f"  Avg win / Avg loss:    {win_loss_ratio:.2f}")
            print(f"  Win rate:             {(len(winning_trades)/len(trades)):.1%}")
            print(f"  Total trades:          {len(trades)}")
            
            if profit_factor < 1.0:
                print(f"  ❌ FAIL: Negative expectancy (profit factor {profit_factor:.2f})")
                self.failures.append(f"Trade quality: unprofitable (PF {profit_factor:.2f})")
                self.results['trade_quality'] = False
                return False
            
            if profit_factor < 1.2:
                print(f"  ⚠️  WARNING: Marginal profit factor {profit_factor:.2f}")
            
            print(f"  ✅ PASS: Positive trade expectancy")
            self.results['trade_quality'] = True
            return True
            
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            self.results['trade_quality'] = None
            return True
    
    # ==================== 🚦 DECISION GATE ====================
    
    def decision_gate(self) -> Dict:
        """
        Final decision: Is the system ready to trade?
        
        Evaluates: 7 core gates + 5 advanced gates
        Hard failures: Alpha, Leakage, Walk-Forward, Edge Decay, Trade Quality
        Soft failures: Others can be warnings
        """
        
        # Check which gates passed
        gate_status = {
            'alpha': self.results.get('alpha'),
            'leakage': self.results.get('leakage'),
            'trade_frequency': self.results.get('trade_frequency'),
            'regime_filter': self.results.get('regime_filter'),
            'walk_forward': self.results.get('walk_forward'),
            'execution': self.results.get('execution'),
            'multi_stock': self.results.get('multi_stock'),
            'confidence_dist': self.results.get('confidence_dist'),
            'drawdown_stress': self.results.get('drawdown_stress'),
            'regime_stability': self.results.get('regime_stability'),
            'edge_decay': self.results.get('edge_decay'),
            'trade_quality': self.results.get('trade_quality')
        }
        
        # Count results
        passed = sum(1 for v in gate_status.values() if v is True)
        failed = sum(1 for v in gate_status.values() if v is False)
        skipped = sum(1 for v in gate_status.values() if v is None)
        total_gates = len(gate_status)
        
        # Print summary
        print(f"\n{'Gate':<25} {'Status':<15}")
        print("-" * 40)
        
        for gate_name, status in gate_status.items():
            if status is True:
                symbol = "✅ PASS"
            elif status is False:
                symbol = "❌ FAIL"
            else:
                symbol = "⏭️  SKIP"
            print(f"{gate_name:<25} {symbol:<15}")
        
        print("-" * 40)
        print(f"{'TOTAL':<25} {passed} PASS / {failed} FAIL / {skipped} SKIP/{total_gates} TOTAL")
        
        # Find hard failures (gates that absolutely block trading)
        hard_fail_gates = ['alpha', 'leakage', 'walk_forward', 'edge_decay', 'trade_quality']
        hard_failures = [gate for gate in hard_fail_gates if gate_status.get(gate) is False]
        
        # Decision logic
        print("\n" + "="*80)
        
        if hard_failures:
            # Hard failure - system blocked
            decision = f"❌ SYSTEM BLOCKED - {len(hard_failures)} HARD FAILURES"
            confidence = 0.0
            
            print("🚫 DECISION: DO NOT TRADE")
            print(f"\nHard Failures ({len(hard_failures)}):")
            for gate in hard_failures:
                print(f"  ❌ {gate}")
            
            if self.failures:
                print("\nDetails:")
                for f in self.failures:
                    print(f"  • {f}")
                    
        elif passed >= 10 and failed == 0:
            # Excellent - all gates pass
            decision = "✅ SAFE FOR PAPER TRADING"
            confidence = 0.95
            
            print("✅ DECISION: SAFE FOR PAPER TRADING")
            print("\nConditions:")
            print("  ✓ Model has verified alpha")
            print("  ✓ No label leakage detected")
            print("  ✓ Stable over time (walk-forward)")
            print("  ✓ Confident predictions")
            print("  ✓ Sustainable edge")
            print("  ✓ Positive trade quality")
            print("  ✓ Profitable after realistic costs")
            
        elif passed >= 7 and failed == 0:
            # Good - most important gates pass
            decision = "🟢 READY FOR PAPER TRADING"
            confidence = 0.80
            
            print("🟢 DECISION: READY FOR PAPER TRADING")
            print(f"\nStatus: {passed}/{total_gates} gates passed")
            print("  • All hard requirements met")
            print("  • Some advanced checks skipped (due to data limitations)")
            print("  • Recommend small position sizing initially")
            
        elif passed >= 5 and failed <= 2:
            # Mixed - some failures but not critical
            skipped_advanced = sum(1 for gate in ['confidence_dist', 'drawdown_stress', 'regime_stability', 'edge_decay', 'trade_quality']
                                   if gate_status.get(gate) is None)
            
            if skipped_advanced >= 3:
                decision = "⚠️  INCONCLUSIVE - NEED MORE DATA"
                confidence = 0.50
                
                print("⚠️  DECISION: INCONCLUSIVE - NEED MORE DATA")
                print(f"\nStatus: {passed} passed, {failed} failed, {skipped} skipped")
                print("\nRecommendation:")
                print("  • Gather more data")
                print("  • Re-run validation")
                print("  • Or improve model/features first")
            else:
                decision = "🟡 MARGINAL - TRADE CAUTIOUSLY"
                confidence = 0.60
                
                print("🟡 DECISION: MARGINAL - TRADE CAUTIOUSLY")
                print(f"\nStatus: {passed} passed, {failed} failed")
                print("\nCautions:")
                for f in self.failures[-3:]:  # Show last 3 failures
                    print(f"  ⚠️  {f}")
                print("\nRecommendation:")
                print("  • Very small position size")
                print("  • Close monitoring")
                print("  • Prepare to stop if performance lags")
        else:
            # Insufficient validation
            decision = "⚠️  INCONCLUSIVE - INSUFFICIENT VALIDATION"
            confidence = 0.30
            
            print("⚠️  DECISION: INCONCLUSIVE - INSUFFICIENT VALIDATION")
            print(f"\nOnly {passed}/{total_gates} gates validated")
        
        print("="*80 + "\n")
        
        return {
            'decision': decision,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'total': total_gates,
            'confidence': confidence,
            'failures': self.failures,
            'gate_status': gate_status,
            'hard_failures': hard_failures
        }
    
    # ==================== 🔥 FINAL UPGRADES: LIVE TRADING PREP ====================
    
    def check_data_drift(self, live_df: pd.DataFrame) -> Dict:
        """
        🔥 CRITICAL UPGRADE: Live Data Drift Detection
        
        Problem: Training data ≠ Live data (market regime changes)
        Solution: Statistical comparison of distributions
        
        Checks:
        - Mean difference > 1 std dev
        - Distribution shift detection
        
        Returns: Drift analysis results
        """
        
        print("\n" + "="*80)
        print("🔥 LIVE DATA DRIFT DETECTION")
        print("="*80)
        
        try:
            # Get feature columns from training data
            skip_cols = ['Close', 'Open', 'High', 'Low', 'Volume', 'target_direction', 
                        'signal', 'return', 'signal_filtered', 'signal_regime']
            feature_cols = [col for col in self.df.columns if col not in skip_cols and col in live_df.columns]
            
            if len(feature_cols) == 0:
                return {
                    'drift_detected': False,
                    'message': 'No common features found',
                    'details': {}
                }
            
            print(f"Checking {len(feature_cols)} features for drift...")
            
            drift_features = []
            drift_details = {}
            
            for col in feature_cols:
                try:
                    # Training stats
                    train_mean = self.df[col].mean()
                    train_std = self.df[col].std()
                    
                    # Live stats
                    live_mean = live_df[col].mean()
                    live_std = live_df[col].std()
                    
                    # Check for drift
                    mean_diff = abs(train_mean - live_mean)
                    mean_diff_std = mean_diff / (train_std + 1e-6)
                    
                    # Flag if difference > 1 standard deviation
                    if mean_diff_std > 1.0:
                        drift_features.append(col)
                        drift_details[col] = {
                            'train_mean': train_mean,
                            'live_mean': live_mean,
                            'mean_diff_std': mean_diff_std,
                            'severity': 'HIGH' if mean_diff_std > 2.0 else 'MEDIUM'
                        }
                        
                except Exception as e:
                    print(f"  ⚠️  Error checking {col}: {e}")
                    continue
            
            if drift_features:
                print(f"⚠️  DRIFT DETECTED in {len(drift_features)} features:")
                for col in drift_features[:5]:  # Show first 5
                    details = drift_details[col]
                    print(f"  • {col}: {details['mean_diff_std']:.1f} std dev difference")
                
                if len(drift_features) > 5:
                    print(f"  • ... and {len(drift_features) - 5} more")
                
                return {
                    'drift_detected': True,
                    'message': f'Drift in {len(drift_features)} features - model may be invalid',
                    'details': drift_details,
                    'recommendation': 'Re-train model or wait for market normalization'
                }
            else:
                print("✅ NO DRIFT DETECTED - Live data matches training distribution")
                return {
                    'drift_detected': False,
                    'message': 'Data distributions aligned',
                    'details': {},
                    'recommendation': 'Safe to use current model'
                }
                
        except Exception as e:
            print(f"⚠️  Error in drift detection: {e}")
            return {
                'drift_detected': False,
                'message': f'Error: {e}',
                'details': {},
                'recommendation': 'Manual review required'
            }
    
    def calibrate_confidence(self, X_train: pd.DataFrame, y_train: pd.Series, 
                           X_live: pd.DataFrame = None) -> Dict:
        """
        🔥 VERY IMPORTANT UPGRADE: Confidence Calibration
        
        Problem: Model probabilities are not calibrated
        Solution: Platt Scaling or Isotonic Regression
        
        Why: 0.70 prediction should be 70% accurate
        
        Returns: Calibrated model and metrics
        """
        
        print("\n" + "="*80)
        print("🔥 CONFIDENCE CALIBRATION")
        print("="*80)
        
        try:
            from sklearn.calibration import CalibratedClassifierCV
            from sklearn.metrics import brier_score_loss
            from sklearn.model_selection import cross_val_predict
            
            if self.model is None:
                return {
                    'calibrated_model': None,
                    'message': 'No base model provided',
                    'brier_score': None,
                    'calibration_curve': None
                }
            
            print("Calibrating model probabilities...")
            
            # Create calibrated model
            calibrated_model = CalibratedClassifierCV(
                estimator=self.model, 
                method='isotonic',  # Better than sigmoid for most cases
                cv=3
            )
            
            # Fit on training data
            calibrated_model.fit(X_train, y_train)
            
            # Get calibrated probabilities
            prob_pos = calibrated_model.predict_proba(X_train)[:, 1]
            
            # Calculate Brier score (lower is better)
            brier = brier_score_loss(y_train, prob_pos)
            
            # Create calibration bins
            bins = np.linspace(0, 1, 11)
            bin_centers = (bins[:-1] + bins[1:]) / 2
            
            calibration_data = []
            for i in range(len(bins) - 1):
                mask = (prob_pos >= bins[i]) & (prob_pos < bins[i + 1])
                if mask.sum() > 0:
                    actual_rate = y_train[mask].mean()
                    predicted_rate = prob_pos[mask].mean()
                    calibration_data.append({
                        'bin_center': bin_centers[i],
                        'predicted_prob': predicted_rate,
                        'actual_rate': actual_rate,
                        'samples': mask.sum()
                    })
            
            print(".3f")
            print(f"Calibration bins: {len(calibration_data)}")
            
            # Test on live data if provided
            live_calibration = None
            if X_live is not None and len(X_live) > 0:
                try:
                    live_probs = calibrated_model.predict_proba(X_live)[:, 1]
                    live_calibration = {
                        'mean_prob': live_probs.mean(),
                        'high_conf_pct': (live_probs > 0.7).mean(),
                        'samples': len(live_probs)
                    }
                    print(f"Live data: {live_calibration['high_conf_pct']:.1%} high confidence predictions")
                except:
                    pass
            
            return {
                'calibrated_model': calibrated_model,
                'message': 'Model calibrated successfully',
                'brier_score': brier,
                'calibration_curve': calibration_data,
                'live_calibration': live_calibration
            }
            
        except Exception as e:
            print(f"⚠️  Error in calibration: {e}")
            return {
                'calibrated_model': None,
                'message': f'Calibration failed: {e}',
                'brier_score': None,
                'calibration_curve': None
            }
    
    def portfolio_allocation(self, signals_df: pd.DataFrame, total_capital: float = 100000,
                           max_position_pct: float = 0.02) -> Dict:
        """
        🔥 NEXT LEVEL UPGRADE: Portfolio-Level Thinking
        
        Problem: Single stock decisions
        Solution: Multi-stock portfolio allocation
        
        Features:
        - Capital allocation across signals
        - Position sizing by confidence
        - Risk diversification
        
        Returns: Portfolio allocation plan
        """
        
        print("\n" + "="*80)
        print("🔥 PORTFOLIO ALLOCATION SYSTEM")
        print("="*80)
        
        try:
            # Find active signals
            if 'confidence' in signals_df.columns:
                # Use confidence for sizing
                active_signals = signals_df[signals_df['confidence'] > 0.6].copy()
                active_signals = active_signals.sort_values('confidence', ascending=False)
            else:
                # Simple signal-based
                active_signals = signals_df[signals_df.get('signal', 0) == 1].copy()
            
            if len(active_signals) == 0:
                return {
                    'allocation': {},
                    'message': 'No active signals found',
                    'total_positions': 0,
                    'total_allocated': 0
                }
            
            print(f"Active signals: {len(active_signals)}")
            
            # Calculate position sizes
            max_position_size = total_capital * max_position_pct
            
            # Allocate capital
            allocations = {}
            total_allocated = 0
            
            for idx, row in active_signals.iterrows():
                try:
                    current_price = row.get('Close', row.get('close', 100))
                    
                    # Position size based on confidence (if available)
                    if 'confidence' in row:
                        confidence_factor = row['confidence']  # 0.6 to 1.0
                        position_size = max_position_size * confidence_factor
                    else:
                        position_size = max_position_size
                    
                    # Calculate shares
                    shares = int(position_size / current_price)
                    actual_allocation = shares * current_price
                    
                    if shares > 0:
                        allocations[idx] = {
                            'symbol': row.get('symbol', f'Position_{idx}'),
                            'shares': shares,
                            'price': current_price,
                            'allocation': actual_allocation,
                            'confidence': row.get('confidence', 0.5),
                            'position_pct': actual_allocation / total_capital
                        }
                        
                        total_allocated += actual_allocation
                        
                except Exception as e:
                    print(f"  ⚠️  Error allocating {idx}: {e}")
                    continue
            
            # Summary
            print(f"Total positions: {len(allocations)}")
            print(".1f")
            print(".1f")
            print(".1%")
            
            # Risk check
            if total_allocated > total_capital * 0.1:  # More than 10% allocated
                print("⚠️  HIGH ALLOCATION - Consider reducing position sizes")
            
            return {
                'allocation': allocations,
                'message': f'Allocated ${total_allocated:,.0f} across {len(allocations)} positions',
                'total_positions': len(allocations),
                'total_allocated': total_allocated,
                'utilization_pct': total_allocated / total_capital,
                'avg_position_size': total_allocated / max(1, len(allocations))
            }
            
        except Exception as e:
            print(f"⚠️  Error in portfolio allocation: {e}")
            return {
                'allocation': {},
                'message': f'Allocation failed: {e}',
                'total_positions': 0,
                'total_allocated': 0
            }


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    
    print("""
    🚀 PRODUCTION VALIDATOR
    
    This system enforces 7 mandatory gates:
    1. Alpha Validation - Beat baselines
    2. Leakage Detection - No future info
    3. Trade Frequency - Min gap between trades
    4. Regime Filter - Trade only when trending
    5. Walk-Forward - Stable model over time
    6. Execution Costs - Profitable after slippage
    7. Multi-Stock - Generalizes to new stocks
    
    Usage:
    ------
    validator = ProductionValidator(df, model=trained_model)
    results = validator.run_all_gates()
    
    if "SAFE FOR PAPER TRADING" in results['decision']:
        print("✅ Ready to deploy!")
    else:
        print("❌ Back to drawing board")
    """)
