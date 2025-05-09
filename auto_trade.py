# auto_trade.py - Automated Trading Engine

This file runs the automated trading system during market hours, handling portfolio initialization, trade signal monitoring, and position management.

```python
import logging
import os
from datetime import datetime, time
import pytz
from time import sleep
from modules.portfolio_manager import PortfolioManager
from modules.utils import load_trades, save_trades

# =============================================================================
# Logging Setup
# =============================================================================
# Set up logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading.log'),
        logging.StreamHandler()
    ]
)

# =============================================================================
# Market Hours Check
# =============================================================================
def is_market_open():
    """Check if US market is open"""
    et_timezone = pytz.timezone('US/Eastern')
    current_time = datetime.now(et_timezone).time()
    market_open = time(9, 30)  # 9:30 AM ET
    market_close = time(16, 0)  # 4:00 PM ET

    # Check if it's a weekday (0 = Monday, 4 = Friday)
    is_weekday = datetime.now(et_timezone).weekday() < 5

    return is_weekday and market_open <= current_time <= market_close

# =============================================================================
# Automated Trading Logic
# =============================================================================
def run_automated_trading(simulation_mode=True):
    """Run automated trading during market hours"""
    logging.info(f"Starting automated trading system in {'simulation' if simulation_mode else 'live'} mode...")

    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Initialize portfolio manager
            portfolio = PortfolioManager()
            if not portfolio.initialize_portfolio():
                retry_count += 1
                logging.error(f"Failed to initialize portfolio (attempt {retry_count}/{max_retries}). Retrying in 60 seconds...")
                sleep(60)
                continue

            logging.info("Portfolio successfully initialized")
            break
        except Exception as e:
            retry_count += 1
            logging.error(f"Error during portfolio initialization (attempt {retry_count}/{max_retries}): {str(e)}")
            if retry_count < max_retries:
                sleep(60)
            else:
                logging.error("Max retries reached. Exiting...")
                return

    while True:
        try:
            if simulation_mode or is_market_open():
                logging.info(f"\nChecking for trading signals at {datetime.now()}")

                # Check for new signals
                signals = portfolio.check_signals()
                if signals:
                    logging.info(f"Found {len(signals)} new trading opportunities!")
                    for signal in signals:
                        logging.info(f"New {signal['type']} trade for {signal['symbol']}")
                        if signal['type'] == 'options':
                            logging.info(f"Strategy: {signal['strategy_type']}")
                            logging.info(f"Max Profit: ${signal['max_profit']:.2f}")
                            logging.info(f"Max Loss: ${signal['max_loss']:.2f}")
                            for leg in signal['legs']:
                                logging.info(f"Leg: {leg['action']} {leg['type']} at strike ${leg['strike']}")

                # Monitor and update portfolio
                portfolio_summary = portfolio.monitor_portfolio()

                # Print portfolio status
                stats = portfolio.get_portfolio_stats()
                
                # Prepare CSV entry for performance tracking
                perf_entry = (
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},"
                    f"{stats['current_capital']:.2f},"
                    f"{stats['available_capital']:.2f},"
                    f"{stats['total_trades']},"
                    f"{stats['win_rate']:.2f},"
                    f"{stats['total_profit']:.2f}\n"
                )
                
                # Append to performance log CSV
                os.makedirs('logs', exist_ok=True)

                perf_file = open('logs/performance.csv', 'a')
                if perf_file.tell() == 0:
                    # write header if file is new
                    perf_file.write("timestamp,current_capital,available_capital,total_trades,win_rate,total_profit\n")
                
                perf_file.write(perf_entry)
                perf_file.close()

                logging.info("\nPortfolio Status:")
                logging.info(f"Total Capital: ${stats['current_capital']:,.2f}")
                logging.info(f"Available Capital: ${stats['available_capital']:,.2f}")
                logging.info(f"Win Rate: {stats['win_rate']:.1f}%")
                logging.info(f"Total Trades: {stats['total_trades']}")

                # If there are open positions, print their status
                if portfolio_summary['open_positions']:
                    logging.info("\nOpen Positions:")
                    for pos in portfolio_summary['open_positions']:
                        if pos['type'] == 'equity':
                            logging.info(f"{pos['symbol']}: {pos['type']} - Entry: ${pos['entry_price']:.2f}")
                        else:  # options strategy
                            logging.info(f"{pos['symbol']}: {pos['strategy_type']} - Expiry: {pos['expiry']}")

                # Wait for 5 minutes before next check
                logging.info("Waiting 5 minutes for next check...")
                sleep(300)  # 5 minutes
            else:
                logging.info("Market is closed. Waiting for market hours...")
                sleep(1800)  # 30 minutes

        except Exception as e:
            logging.error(f"Error in trading loop: {str(e)}")
            sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    # Default to simulation mode for testing
    run_automated_trading(simulation_mode=True)
```

Key Components:
1. Market Hours Check: Uses pytz to handle US Eastern timezone for accurate market hours
2. Portfolio Initialization: Includes retry mechanism for reliable startup
3. Trading Loop: Monitors signals and manages positions during market hours
4. Error Handling: Comprehensive logging and recovery from failures
5. Simulation Mode: Allows testing without market hour restrictions
