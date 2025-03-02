import streamlit as st
import yfinance as yf
import pandas as pd
from modules.stock_data import get_sp500_stocks, get_stock_info
from modules.technical_analysis import display_technical_analysis
from modules.news_analysis import display_news, display_analyst_ratings, display_earnings_calendar
from modules.options_analysis import display_options_analysis
from modules.paper_trading import PaperTrading
from modules.portfolio_manager import PortfolioManager
from modules.utils import load_trades, save_trades

st.set_page_config(page_title="Stock Market Analysis Tool", layout="wide")

# Initialize portfolio manager in session state
if 'portfolio_manager' not in st.session_state:
    st.session_state.portfolio_manager = PortfolioManager()

def main():
    st.title("Stock Market Analysis & Paper Trading Tool")

    # Sidebar for navigation
    page = st.sidebar.selectbox(
        "Navigate",
        ["Portfolio Dashboard", "Stock Analysis", "Paper Trading"]
    )

    # Get S&P 500 stocks
    sp500_stocks = get_sp500_stocks()
    selected_stock = st.sidebar.selectbox(
        "Select Stock",
        sp500_stocks['Symbol'].tolist()
    )

    if page == "Portfolio Dashboard":
        st.subheader("Automated Trading Portfolio")

        # Portfolio Statistics
        portfolio_stats = st.session_state.portfolio_manager.get_portfolio_stats()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Capital", f"${portfolio_stats['current_capital']:,.2f}",
                   delta=f"{((portfolio_stats['current_capital']/100000)-1)*100:.1f}%")
        col2.metric("Available Capital", f"${portfolio_stats['available_capital']:,.2f}")
        col3.metric("Win Rate", f"{portfolio_stats['win_rate']:.1f}%")
        col4.metric("Total Trades", portfolio_stats['total_trades'])

        # Check for new signals
        if st.button("Check for New Trading Signals"):
            signals = st.session_state.portfolio_manager.check_signals()
            if signals:
                st.success(f"Found {len(signals)} new trading opportunities!")
                for signal in signals:
                    st.write(f"New {signal['type']} trade for {signal['symbol']}")
            else:
                st.info("No new trading signals at this time")

        # Monitor Portfolio
        st.subheader("Portfolio Monitor")
        portfolio_summary = st.session_state.portfolio_manager.monitor_portfolio()

        # Display open positions
        st.write("### Open Positions")
        if portfolio_summary['open_positions']:
            for position in portfolio_summary['open_positions']:
                with st.expander(f"{position['symbol']} - {position['type'].upper()}"):
                    col1, col2, col3 = st.columns(3)

                    entry_price = position['entry_price']
                    current_price = st.session_state.portfolio_manager.trading_strategies[position['symbol']].get_technical_signals()['price']
                    pnl = (current_price - entry_price) / entry_price * 100

                    col1.metric("Entry Price", f"${entry_price:.2f}")
                    col2.metric("Current Price", f"${current_price:.2f}")
                    col3.metric("P&L %", f"{pnl:.2f}%",
                              delta="+" + str(pnl) if pnl > 0 else str(pnl))

                    st.write(f"Quantity: {position['quantity']}")
                    st.write(f"Stop Loss: ${position['stop_loss']:.2f}")
                    st.write(f"Take Profit: ${position['take_profit']:.2f}")
        else:
            st.info("No open positions")

        # Recent trades
        st.write("### Recent Closed Trades")
        if portfolio_summary['closed_positions']:
            recent_trades = pd.DataFrame(portfolio_summary['closed_positions'][-5:])
            st.dataframe(recent_trades)
        else:
            st.info("No closed trades yet")

    elif page == "Stock Analysis":
        # Create three columns for better layout
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"Technical Analysis - {selected_stock}")
            display_technical_analysis(selected_stock)

            # Add options analysis below technical analysis
            display_options_analysis(selected_stock)

        with col2:
            st.subheader("Company Information")
            stock_info = get_stock_info(selected_stock)
            st.write(stock_info)

            # Add earnings calendar
            display_earnings_calendar(selected_stock)

            # Add analyst ratings
            display_analyst_ratings(selected_stock)

            # Display news
            display_news(selected_stock)

    elif page == "Paper Trading":
        paper_trading = PaperTrading(selected_stock)
        paper_trading.display_trading_interface()

    else:  # Performance Dashboard (This section is now redundant due to the new Portfolio Dashboard)
        st.subheader("Trading Performance")
        trades = load_trades()

        if trades:
            df_trades = pd.DataFrame(trades)

            # Performance metrics
            total_trades = len(trades)
            winning_trades = len(df_trades[df_trades['profit'] > 0])
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Trades", total_trades)
            col2.metric("Winning Trades", winning_trades)
            col3.metric("Win Rate", f"{win_rate:.2f}%")

            st.subheader("Trade History")
            st.dataframe(df_trades)
        else:
            st.info("No trades recorded yet. Start paper trading to see performance metrics.")


if __name__ == "__main__":
    main()
