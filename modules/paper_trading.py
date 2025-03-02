import streamlit as st
import pandas as pd
from datetime import datetime
from modules.stock_data import get_historical_data
from modules.utils import load_trades, save_trades
from modules.trading_strategy import TradingStrategy
from modules.options_analysis import get_options_chain  # Fixed import

class PaperTrading:
    def __init__(self, symbol):
        self.symbol = symbol
        self.data = get_historical_data(symbol)
        self.current_price = self.data['Close'].iloc[-1]
        self.strategy = TradingStrategy(symbol)

    def execute_trade(self, action, quantity, stop_loss, take_profit, trade_type='equity', strike=None, expiration=None, option_type=None):
        """Execute a manual paper trade"""
        trade = {
            'symbol': self.symbol,
            'type': trade_type,
            'action': action,
            'quantity': quantity,
            'entry_price': self.current_price if trade_type == 'equity' else 0, # Placeholder, needs actual price
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'status': 'open',
            'entry_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'exit_date': None,
            'exit_price': None,
            'profit': None
        }
        if trade_type == 'option':
            trade['strike'] = strike
            trade['expiration'] = expiration
            trade['option_type'] = option_type
            #Fetch actual entry price from options chain
            options_df, _ = get_options_chain(self.symbol, num_expiries=1)
            if not options_df.empty:
                current_option = options_df[
                    (options_df['strike'] == strike) &
                    (options_df['optionType'] == option_type) &
                    (options_df['expiration'] == expiration)
                ]
                if not current_option.empty:
                    trade['entry_price'] = current_option.iloc[0]['lastPrice']
                else:
                    st.warning("Unable to fetch option entry price")
                    return None


        trades = load_trades()
        trades.append(trade)
        save_trades(trades)

        return trade

    def check_automated_signals(self):
        """Check for automated trading signals"""
        trade_type = self.strategy.should_enter_trade()
        if trade_type:
            return self.strategy.execute_trade(trade_type)
        return None

    def monitor_positions(self):
        """Monitor and update all positions"""
        return self.strategy.monitor_positions()

    def display_position_details(self, trade):
        """Display detailed position information"""
        col1, col2, col3, col4 = st.columns(4)

        # Calculate current P&L
        if trade['type'] == 'equity':
            current_price = self.current_price
            entry_price = trade['entry_price']
            pnl = (current_price - entry_price) / entry_price * 100
            unrealized_profit = (current_price - entry_price) * trade['quantity']

            col1.metric("Entry Price", f"${entry_price:.2f}")
            col2.metric("Current Price", f"${current_price:.2f}")

        else:  # Options position
            # Get current option price
            options_df, _ = get_options_chain(self.symbol, num_expiries=1)
            if not options_df.empty:
                current_option = options_df[
                    (options_df['strike'] == trade['strike']) &
                    (options_df['optionType'] == trade['option_type']) &
                    (options_df['expiration'] == trade['expiration'])
                ]

                if not current_option.empty:
                    current_price = current_option.iloc[0]['lastPrice']
                    entry_price = trade['entry_price']
                    pnl = (current_price - entry_price) / entry_price * 100
                    unrealized_profit = (current_price - entry_price) * trade['quantity'] * 100

                    col1.metric("Entry Premium", f"${entry_price:.2f}")
                    col2.metric("Current Premium", f"${current_price:.2f}")

                    # Display options-specific info
                    st.write(f"Strike: ${trade['strike']:.2f}")
                    st.write(f"Expiration: {trade['expiration']}")
                    st.write(f"Contracts: {trade['quantity']}")
                else:
                    st.warning("Unable to fetch current option price")
                    return
            else:
                st.warning("Unable to fetch options data")
                return

        col3.metric("P&L %", f"{pnl:.2f}%", 
                    delta="+" + str(pnl) if pnl > 0 else str(pnl))
        col4.metric("Unrealized P&L", f"${unrealized_profit:.2f}",
                    delta="+" + str(unrealized_profit) if unrealized_profit > 0 else str(unrealized_profit))

        # Risk management levels
        st.write("Risk Management:")
        risk_col1, risk_col2 = st.columns(2)
        risk_col1.metric("Stop Loss", f"${trade['stop_loss']:.2f}")
        risk_col2.metric("Take Profit", f"${trade['take_profit']:.2f}")

        # Display signals that triggered the trade
        if 'signals' in trade:
            with st.expander("Entry Signals"):
                st.write("Technical Signals:", trade['signals']['technical'])
                st.write("Options Flow:", trade['signals']['options'])
                st.write("Analyst Ratings:", trade['signals']['analyst'])


    def display_trading_interface(self):
        st.subheader(f"Paper Trading - {self.symbol}")
        st.write(f"Current Price: ${self.current_price:.2f}")

        # Add automated trading section
        st.subheader("Automated Trading Signals")

        # Display technical signals
        tech_signals = self.strategy.get_technical_signals()
        options_signals = self.strategy.get_options_signals()
        analyst_signals = self.strategy.get_analyst_signals()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("Technical Signals")
            st.write(f"RSI: {tech_signals['rsi']:.2f}")
            st.write(f"Trend: {'Uptrend' if tech_signals['uptrend'] else 'Downtrend'}")
            if tech_signals['oversold']:
                st.success("RSI Oversold - Potential Buy")
            elif tech_signals['overbought']:
                st.warning("RSI Overbought - Potential Sell")

        with col2:
            st.write("Options Flow Signals")
            st.write(f"Put/Call Ratio: {options_signals['put_call_ratio']:.2f}")
            if options_signals['bullish_flow']:
                st.success("Bullish Options Flow")
            else:
                st.warning("Bearish Options Flow")

        with col3:
            st.write("Analyst Ratings")
            st.write(f"Recommendation: {analyst_signals['recommendation']}")
            st.write(f"Target Price: ${analyst_signals['target_price']:.2f}")
            if analyst_signals['bullish']:
                st.success("Analysts Recommend Buy")
            elif analyst_signals['bearish']:
                st.warning("Analysts Recommend Sell")

        # Check for automated trade signals
        if st.button("Check for Trade Signals"):
            trade = self.check_automated_signals()
            if trade:
                st.success(f"Trade Signal Found: {trade['type'].upper()} {trade['action']}")
                st.write(trade)
            else:
                st.info("No trade signals at this time")

        # Position Monitoring
        st.subheader("Position Monitor")
        trades = load_trades()
        open_trades = [t for t in trades if t['status'] == 'open']

        if open_trades:
            for trade in open_trades:
                with st.expander(f"Position: {trade['symbol']} - {trade['type'].upper()}"):
                    self.display_position_details(trade)

        else:
            st.info("No open positions to monitor")

        # Manual trading interface
        st.subheader("Manual Trading")
        col1, col2, col3 = st.columns(3)

        with col1:
            action = st.selectbox("Action", ["Buy", "Sell"])
            quantity = st.number_input("Quantity", min_value=1, value=100)
            trade_type = st.selectbox("Trade Type", ["equity", "option"])

        with col2:
            stop_loss = st.number_input(
                "Stop Loss",
                min_value=0.0,
                value=self.current_price * 0.95 if action == "Buy" else self.current_price * 1.05
            )
            take_profit = st.number_input(
                "Take Profit",
                min_value=0.0,
                value=self.current_price * 1.05 if action == "Buy" else self.current_price * 0.95
            )

        with col3:
            if trade_type == "option":
                strike = st.number_input("Strike Price", value=self.current_price)
                expiration = st.date_input("Expiration Date")
                option_type = st.selectbox("Option Type", ["call", "put"])


        if st.button("Execute Manual Trade"):
            trade = self.execute_trade(action, quantity, stop_loss, take_profit, trade_type, strike if trade_type == "option" else None, expiration if trade_type == "option" else None, option_type if trade_type == "option" else None)
            if trade:
                st.success(f"Trade executed: {action} {quantity} of {self.symbol}")
                st.write(trade)
            else:
                st.error("Trade execution failed.")


        # Display trading statistics
        st.subheader("Trading Performance")
        stats = self.strategy.get_trading_stats()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Trades", stats['total_trades'])
        col2.metric("Win Rate", f"{stats['win_rate']:.1f}%")
        col3.metric("Avg Profit", f"${stats['avg_profit']:.2f}")
        col4.metric("Max Drawdown", f"{stats['max_drawdown']:.1f}%")

        # Auto-refresh positions button
        if st.button("Update All Positions"):
            updated_trades = self.monitor_positions()
            if updated_trades:
                st.success("Positions updated successfully")
                st.write("Updated positions:", 
                        [t for t in updated_trades if t['status'] == 'open'])
