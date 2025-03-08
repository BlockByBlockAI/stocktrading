import pandas as pd
import numpy as np
from datetime import datetime
from modules.technical_analysis import calculate_rsi, calculate_sma, calculate_support_resistance
from modules.options_analysis import calculate_options_statistics, get_options_chain
from modules.stock_data import get_historical_data
from modules.news_analysis import get_analyst_ratings
from modules.utils import load_trades, save_trades
from modules.options_strategies import OptionsStrategy
import logging

class TradingStrategy:
    def __init__(self, symbol, initial_capital=100000):
        self.symbol = symbol
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = []
        self.max_loss_pct = 0.20  # 20% max loss

    def get_technical_signals(self):
        """Analyze technical indicators for trading signals"""
        try:
            df = get_historical_data(self.symbol)

            # Guard clause for empty or insufficient data
            if df is None or df.empty or len(df) < 50:  # Need at least 50 data points for reliable signals
                logging.warning(f"Insufficient historical data for {self.symbol} (got {len(df) if df is not None else 0} rows)")
                return {
                    'price': None,
                    'rsi': None,
                    'oversold': False,
                    'overbought': False,
                    'uptrend': False,
                    'support': None,
                    'resistance': None,
                    'near_support': False,
                    'near_resistance': False,
                    'sma_20': None,
                    'sma_50': None
                }

            # Log data validation
            logging.info(f"Processing technical signals for {self.symbol} with {len(df)} data points")

            # Calculate indicators with validation
            df['RSI'] = calculate_rsi(df['Close'])
            if df['RSI'].isna().all():
                raise ValueError("RSI calculation failed")

            df['SMA_20'] = calculate_sma(df['Close'], 20)
            df['SMA_50'] = calculate_sma(df['Close'], 50)

            if df['SMA_20'].isna().all() or df['SMA_50'].isna().all():
                raise ValueError("SMA calculation failed")

            support, resistance = calculate_support_resistance(df)

            if support.empty or resistance.empty:
                raise ValueError("Support/Resistance calculation failed")

            # Get latest values with validation
            current_price = df['Close'].iloc[-1] if not df['Close'].empty else None
            current_rsi = df['RSI'].iloc[-1] if not df['RSI'].empty else None
            sma_20 = df['SMA_20'].iloc[-1] if not df['SMA_20'].empty else None
            sma_50 = df['SMA_50'].iloc[-1] if not df['SMA_50'].empty else None
            current_macd = df['MACD'].iloc[-1]
            current_signal = df['MACD_signal'].iloc[-1]
            current_upper = df['Bollinger_Upper'].iloc[-1]
            current_lower = df['Bollinger_Lower'].iloc[-1]
            current_atr = df['ATR'].iloc[-1]

            if any(x is None for x in [current_price, current_rsi, sma_20, sma_50]):
                raise ValueError("Failed to get current indicator values")

            signals = {
                'price': current_price,
                'rsi': current_rsi,
                'oversold': current_rsi < 30,
                'overbought': current_rsi > 70,
                'uptrend': sma_20 > sma_50,
                'support': support.iloc[-1] if not support.empty else None,
                'resistance': resistance.iloc[-1] if not resistance.empty else None,
                'near_support': current_price <= support.iloc[-1] * 1.02 if not support.empty else False,
                'near_resistance': current_price >= resistance.iloc[-1] * 0.98 if not resistance.empty else False,
                'sma_20': sma_20,
                'sma_50': sma_50,
                # New indicators:
                'macd': current_macd,
                'macd_signal_line': current_signal,
                'macd_bullish': current_macd > current_signal,         # True if MACD above signal (bullish momentum)
                'bollinger_upper': current_upper,
                'bollinger_lower': current_lower,
                'bollinger_width': ((current_upper - current_lower) / rolling_mean.iloc[-1]) if rolling_mean.iloc[-1] != 0 else 0,
                'below_bollinger': current_price < current_lower,
                'above_bollinger': current_price > current_upper,
                'atr': current_atr,
                'atr_percent': (current_atr / current_price * 100) if current_price != 0 else 0
            }

            # Log successful signal calculation and status
            logging.info(f"""
Technical Analysis for {self.symbol}:
- Price: ${current_price:.2f}
- RSI: {current_rsi:.2f} ({'Oversold' if signals['oversold'] else 'Overbought' if signals['overbought'] else 'Normal'})
- Trend: {'Uptrend' if signals['uptrend'] else 'Downtrend'}
- Support: ${signals['support']:.2f}
- Resistance: ${signals['resistance']:.2f}
- Near Support: {signals['near_support']}
- Near Resistance: {signals['near_resistance']}
""")
            return signals

        except Exception as e:
            logging.error(f"Error calculating technical signals for {self.symbol}: {str(e)}")
            return {
                'price': None,
                'rsi': None,
                'oversold': False,
                'overbought': False,
                'uptrend': False,
                'support': None,
                'resistance': None,
                'near_support': False,
                'near_resistance': False,
                'sma_20': None,
                'sma_50': None
            }

    def get_analyst_signals(self):
        """Get analyst ratings signals"""
        ratings = get_analyst_ratings(self.symbol)

        signals = {
            'recommendation': ratings.get('Recommendation', 'HOLD'),
            'mean_rating': float(ratings.get('Mean Rating', 3.0)),
            'bullish': ratings.get('Recommendation', 'HOLD') in ['BUY', 'STRONG_BUY'],
            'bearish': ratings.get('Recommendation', 'HOLD') in ['SELL', 'STRONG_SELL'],
            'target_price': float(ratings.get('Target Price', '0').replace('$', ''))
        }

        return signals

    def get_options_signals(self):
        """Analyze options flow for trading signals"""
        options_df, _ = get_options_chain(self.symbol, num_expiries=3)
        stats = calculate_options_statistics(options_df)

        signals = {
            'bullish_flow': stats['net_money_flow'] > 0,
            'strong_flow': abs(stats['money_flow_ratio']) > 0.3,  # Strong directional bias
            'put_call_ratio': stats['put_call_ratio'],
            'high_activity': (stats['total_call_volume'] + stats['total_put_volume']) > 1000
        }

        return signals

    def should_enter_trade(self):
        """Determine if we should enter a trade based on signals"""
        try:
            tech_signals = self.get_technical_signals()

            # Skip if we don't have valid technical data
            if tech_signals['price'] is None:
                logging.warning(f"Skipping trade check for {self.symbol} - No valid price data")
                return None

            options_signals = self.get_options_signals()
            analyst_signals = self.get_analyst_signals()

            # If an ML model is available, use it to evaluate the trade
            if hasattr(self, 'ml_model') and self.ml_model:
                # Prepare feature vector for prediction (example features)
                features = [
                    tech_signals['rsi'],
                    tech_signals['sma_20'] - tech_signals['sma_50'],   # trend strength
                    tech_signals['macd'] - tech_signals['macd_signal_line'],  # MACD histogram
                    options_signals['put_call_ratio'],
                    1 if options_signals['bullish_flow'] else 0,
                    analyst_signals['mean_rating']
                ]
            prob = self.ml_model.predict_proba([features])[0][1]  # probability of positive outcome
            logging.info(f"ML model confidence for {self.symbol}: {prob:.2f}")

            if prob < 0.5:
                # If predicted success probability is below 50%, skip this trade signal
                logging.info(f"ML model suggests low success probability for {self.symbol}, skipping trade")
                return None

            current_price = tech_signals['price']

            # Log analysis for debugging
            logging.info(f"Analyzing {self.symbol} at ${current_price:.2f}")
            logging.info(f"Technical Indicators: RSI={tech_signals['rsi']:.2f}, Trend={'Up' if tech_signals['uptrend'] else 'Down'}")
            logging.info(f"Options Flow: {'Bullish' if options_signals['bullish_flow'] else 'Bearish'}")
            logging.info(f"Analyst Rating: {analyst_signals['recommendation']}")

            # Relaxed entry conditions for simulation mode
            equity_conditions = (
                (tech_signals['oversold'] or tech_signals['rsi'] < 40) and  # Relaxed RSI condition
                (tech_signals['near_support'] or current_price <= tech_signals['support'] * 1.05) and  # Relaxed support condition
                (tech_signals['uptrend'] or tech_signals['price'] > tech_signals.get('sma_20', 0)) and  # Alternative trend condition
                analyst_signals['bullish']  # Keep analyst requirement
            )

            # Relaxed options conditions for simulation mode
            options_conditions = (
                (tech_signals['oversold'] or tech_signals['rsi'] < 45) and  # Relaxed RSI condition
                options_signals['bullish_flow'] and  # Keep options flow requirement
                (options_signals['strong_flow'] or options_signals['put_call_ratio'] < 0.8) and  # Relaxed flow strength
                options_signals['high_activity'] and  # Keep activity requirement
                analyst_signals['bullish']  # Keep analyst requirement
            )

            if equity_conditions:
                logging.info(f"Found equity trade signal for {self.symbol}")
                return 'equity'
            elif options_conditions:
                logging.info(f"Found options trade signal for {self.symbol}")
                return 'options'

            return None

        except Exception as e:
            logging.error(f"Error evaluating trade signals for {self.symbol}: {str(e)}")
            return None

    def execute_trade(self, trade_type):
        """Execute a paper trade based on signals"""
        tech_signals = self.get_technical_signals()
        current_price = tech_signals['price']

        # Calculate position size (risk 2% of capital per trade)
        risk_amount = self.current_capital * 0.02
        # Dynamic stop-loss and take-profit using ATR (if available)
        if tech_signals['atr'] and tech_signals['atr'] > 0:
            # For volatile stocks, use ATR-based bands (1.5 ATR stop, 3 ATR profit target)
            stop_loss_price = current_price - 1.5 * tech_signals['atr']
            take_profit_price = current_price + 3.0 * tech_signals['atr']
        else:
            # Fallback to fixed 5%/15% if ATR not available
            stop_loss_price = current_price * 0.95
            take_profit_price = current_price * 1.15

        # Record signals for ML training
        signal_data = {
            'technical': tech_signals,
            'options': self.get_options_signals(),
            'analyst': self.get_analyst_signals(),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        if trade_type == 'equity':
            quantity = int(risk_amount / current_price)
            if quantity < 1:
                return None

            trade = {
                'symbol': self.symbol,
                'type': 'equity',
                'action': 'buy',
                'quantity': quantity,
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'status': 'open',
                'entry_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'exit_date': None,
                'exit_price': None,
                'profit': None,
                'signals': signal_data
            }

        elif trade_type == 'options':
            # Initialize options strategy handler
            options_strategy = OptionsStrategy(self.symbol)

            # Get current market conditions
            tech_signals = self.get_technical_signals()
            options_signals = self.get_options_signals()

            # Select and create the best strategy for current conditions
            strategy_details = options_strategy.select_best_strategy(
                current_price,
                tech_signals,
                options_signals
            )

            if not strategy_details:
                return None

            # Execute the selected strategy
            trade = options_strategy.execute_strategy(strategy_details)
            if trade:
                # Attach signals record
                trade['signals'] = signal_data  # (we will flatten this later)
                # Dynamic stop-loss and take-profit based on conditions
                if tech_signals['uptrend'] and options_signals['bullish_flow']:
                    # Bullish scenario: allow more risk, aim for higher profit
                    trade['stop_loss'] = trade['max_loss'] * 1.0   # risk full max loss if confident
                    trade['take_profit'] = trade['max_profit'] * 0.7  # aim for 70% of max profit
                elif tech_signals['bollinger_width'] and tech_signals['bollinger_width'] > 0.10:
                    # Volatile market: tighten risk, take profits earlier
                    trade['stop_loss'] = trade['max_loss'] * 0.7
                    trade['take_profit'] = trade['max_profit'] * 0.4
                else:
                    # Normal conditions
                    trade['stop_loss'] = trade['max_loss'] * 0.8
                    trade['take_profit'] = trade['max_profit'] * 0.5
                
            if not trade:
                return None

            # Add additional trade information
            trade['signals'] = signal_data

            # Calculate and set stop loss and take profit based on max loss tolerance
            trade['stop_loss'] = trade['max_loss'] * 0.8  # Exit at 80% of max loss
            trade['take_profit'] = trade['max_profit'] * 0.5  # Take profit at 50% of max profit

            # Save the trade
            trades = load_trades()
            trades.append(trade)
            save_trades(trades)

            return trade

        # Save the trade
        trades = load_trades()
        trades.append(trade)
        save_trades(trades)

        return trade

    def monitor_positions(self):
        """Monitor open positions for exit signals"""
        trades = load_trades()
        updated_trades = []

        for trade in trades:
            if trade['status'] == 'open':
                current_price = self.get_technical_signals()['price']

               if trade['status'] == 'open' and trade['type'] == 'equity':
                    current_price = self.get_technical_signals()['price']
                    entry = trade['entry_price']
                    pnl_percent = (current_price - entry) / entry * 100

                    # Update trailing stop-loss if profit exceeds 10%
                    if pnl_percent > 10:
                        new_stop = current_price * 0.95  # trail stop to 5% below current price
                        if new_stop > trade['stop_loss']:
                            trade['stop_loss'] = new_stop  # move stop-loss up to protect profit

                    # Exit conditions: hit stop-loss or take-profit or max loss threshold
                    if current_price <= trade['stop_loss'] or current_price >= trade['take_profit'] or pnl_percent <= - (self.max_loss_pct * 100):
                        trade['status'] = 'closed'
                        trade['exit_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        trade['exit_price'] = current_price
                        trade['profit'] = (current_price - entry) * trade['quantity']

                elif trade['type'] == 'options':
                    # Get current options chain
                    options_df, _ = get_options_chain(self.symbol, num_expiries=1)

                    if not options_df.empty:
                        # Calculate current value of the strategy
                        current_value = 0
                        for leg in trade['legs']:
                            current_option = options_df[
                                (options_df['strike'] == leg['strike']) &
                                (options_df['optionType'] == leg['type']) &
                                (options_df['expiration'] == trade['expiration'])
                            ]

                            if not current_option.empty:
                                quantity = leg.get('quantity', 1)
                                if leg['action'] == 'buy':
                                    current_value -= current_option.iloc[0]['lastPrice'] * 100 * quantity
                                else:  # sell
                                    current_value += current_option.iloc[0]['lastPrice'] * 100 * quantity

                        # Calculate unrealized P&L
                        initial_value = sum(
                            (leg.get('quantity', 1) * leg['premium'] * 100 *
                             (1 if leg['action'] == 'sell' else -1))
                            for leg in trade['legs']
                        )

                        unrealized_pnl = current_value - initial_value

                        # Check exit conditions
                        if (unrealized_pnl <= -trade['stop_loss'] or  # Stop loss hit
                            unrealized_pnl >= trade['take_profit']):  # Take profit hit

                            trade['status'] = 'closed'
                            trade['exit_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            trade['profit'] = unrealized_pnl

            updated_trades.append(trade)

        save_trades(updated_trades)
        return updated_trades

    def get_trading_stats(self):
        """Calculate trading statistics for analysis"""
        trades = load_trades()
        closed_trades = [t for t in trades if t['status'] == 'closed']

        if not closed_trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_profit': 0,
                'max_drawdown': 0
            }

        total_trades = len(closed_trades)
        winning_trades = len([t for t in closed_trades if t.get('profit', 0) > 0])

        stats = {
            'total_trades': total_trades,
            'win_rate': (winning_trades / total_trades) * 100 if total_trades > 0 else 0,
            'avg_profit': sum(t.get('profit', 0) for t in closed_trades) / total_trades if total_trades > 0 else 0,
            'max_drawdown': min(t.get('profit', 0) for t in closed_trades) / self.initial_capital * 100 if closed_trades else 0
        }

        return stats
