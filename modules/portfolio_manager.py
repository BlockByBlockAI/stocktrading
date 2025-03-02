import pandas as pd
from datetime import datetime
from modules.trading_strategy import TradingStrategy
from modules.stock_data import get_sp500_stocks
from modules.utils import load_trades, save_trades
import logging

class PortfolioManager:
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.available_capital = initial_capital
        self.positions = {}
        self.trading_strategies = {}
        self.max_position_size = initial_capital * 0.02  # 2% per position
        self.initialize_portfolio()

    def initialize_portfolio(self):
        """Initialize trading strategies for top 50 S&P stocks"""
        try:
            # Get top 50 S&P stocks by market cap
            sp500_stocks = get_sp500_stocks()
            if sp500_stocks is None or sp500_stocks.empty:
                raise ValueError("Failed to get S&P 500 stocks data")

            top_50_stocks = sp500_stocks.head(50)

            # Initialize trading strategy for each stock
            for symbol in top_50_stocks['Symbol']:
                self.trading_strategies[symbol] = TradingStrategy(symbol, self.max_position_size)

            logging.info(f"Successfully initialized trading strategies for {len(self.trading_strategies)} stocks")
            return True
        except Exception as e:
            logging.error(f"Error initializing portfolio: {str(e)}")
            return False

    def check_signals(self):
        """Check trading signals for all stocks in portfolio"""
        signals = []
        logging.info(f"Checking signals for {len(self.trading_strategies)} stocks")

        for symbol, strategy in self.trading_strategies.items():
            try:
                # Skip if we don't have enough capital
                if self.available_capital < self.max_position_size:
                    logging.info(f"Skipping {symbol} - Insufficient capital")
                    continue

                logging.info(f"Analyzing {symbol} for trading opportunities...")
                trade_type = strategy.should_enter_trade()
                if trade_type:
                    trade = strategy.execute_trade(trade_type)
                    if trade:
                        self.available_capital -= (
                            trade['entry_price'] * trade['quantity'] 
                            if trade['type'] == 'equity' 
                            else trade['max_loss']
                        )
                        signals.append(trade)
                        logging.info(f"New trade signal for {symbol}: {trade['type']} - {trade.get('strategy_type', 'equity')}")
            except Exception as e:
                logging.error(f"Error checking signals for {symbol}: {str(e)}")
                continue

        return signals

    def monitor_portfolio(self):
        """Monitor all positions and update portfolio status"""
        portfolio_summary = {
            'total_positions': 0,
            'total_profit_loss': 0,
            'open_positions': [],
            'closed_positions': []
        }

        trades = load_trades()
        updated_trades = []

        for trade in trades:
            strategy = self.trading_strategies.get(trade['symbol'])
            if not strategy:
                continue

            if trade['status'] == 'open':
                portfolio_summary['total_positions'] += 1
                # Update position status
                updated_trade = strategy.monitor_position(trade)
                if updated_trade['status'] == 'closed':
                    self.available_capital += (
                        updated_trade['exit_price'] * updated_trade['quantity']
                        if updated_trade['type'] == 'equity'
                        else updated_trade['profit']
                    )
                    portfolio_summary['total_profit_loss'] += updated_trade['profit']
                    portfolio_summary['closed_positions'].append(updated_trade)
                    logging.info(f"Closed position for {trade['symbol']}: Profit = ${updated_trade['profit']:.2f}")
                else:
                    portfolio_summary['open_positions'].append(updated_trade)
                updated_trades.append(updated_trade)
            else:
                portfolio_summary['closed_positions'].append(trade)
                portfolio_summary['total_profit_loss'] += trade['profit']
                updated_trades.append(trade)

        save_trades(updated_trades)
        return portfolio_summary

    def get_portfolio_stats(self):
        """Get portfolio performance statistics"""
        trades = load_trades()

        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_profit': 0,
                'max_drawdown': 0,
                'current_capital': self.initial_capital,
                'available_capital': self.available_capital
            }

        closed_trades = [t for t in trades if t['status'] == 'closed']
        open_trades = [t for t in trades if t['status'] == 'open']

        total_profit = sum(t['profit'] for t in closed_trades if t['profit'] is not None)
        winning_trades = len([t for t in closed_trades if t.get('profit', 0) > 0])

        # Calculate unrealized P&L for open positions
        unrealized_pnl = 0
        for trade in open_trades:
            strategy = self.trading_strategies.get(trade['symbol'])
            if strategy:
                if trade['type'] == 'equity':
                    current_price = strategy.get_technical_signals()['price']
                    unrealized_pnl += (current_price - trade['entry_price']) * trade['quantity']
                else:  # options strategy
                    unrealized_pnl += strategy.calculate_options_pnl(trade)

        stats = {
            'total_trades': len(trades),
            'open_positions': len(open_trades),
            'win_rate': (winning_trades / len(closed_trades) * 100) if closed_trades else 0,
            'total_profit': total_profit,
            'unrealized_pnl': unrealized_pnl,
            'current_capital': self.initial_capital + total_profit + unrealized_pnl,
            'available_capital': self.available_capital
        }

        return stats
