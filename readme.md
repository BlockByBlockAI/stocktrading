# Algorithmic Trading Platform

An advanced algorithmic trading platform that combines technical analysis, options strategies, and automated paper trading.

## Project Structure

### Core Trading Engine
- `auto_trade.py`: Automated trading engine that runs Mon-Fri during market hours
- `modules/trading_strategy.py`: Core trading signal generation and strategy execution
- `modules/portfolio_manager.py`: Portfolio and risk management for multiple positions
- `modules/options_strategies.py`: Complex options strategy selection and execution

### Analysis Components
- `modules/stock_data.py`: Market data fetching and processing
- `modules/technical_analysis.py`: Technical indicators and chart patterns
- `modules/news_analysis.py`: News sentiment and analyst ratings analysis
- `modules/options_analysis.py`: Options chain analysis and flow tracking

### User Interface
- `main.py`: Streamlit dashboard for monitoring and analysis
- `modules/paper_trading.py`: Manual paper trading interface
- `.streamlit/config.toml`: Streamlit configuration

### Data Storage
- `data/paper_trades.json`: Trade history and performance data
- `logs/trading.log`: System logs and debugging information

## Features

1. Multi-Signal Trading Strategy
   - RSI and trend-based indicators
   - Options flow analysis
   - Analyst ratings integration
   - Support/resistance levels

2. Portfolio Management
   - Position sizing and risk control
   - Multi-stock portfolio tracking
   - Automated stop-loss and take-profit
   - Performance analytics

3. Options Trading
   - Complex strategies (spreads, iron condors)
   - Options flow analysis
   - Greeks monitoring
   - Premium decay tracking

4. Real-Time Monitoring
   - Live market data integration
   - Portfolio performance dashboard
   - Trade execution logging
   - Risk metrics tracking

## Running the Platform

1. Start the Streamlit dashboard:
```bash
streamlit run main.py
```

2. Run automated trading:
```bash
python auto_trade.py
```

The system runs in simulation mode by default for testing and optimization.

## Configuration

- Initial capital: $100,000
- Risk per trade: 2% of portfolio
- Default stop-loss: 5%
- Default take-profit: 15%
- Trading universe: Top 50 S&P 500 stocks

## Dependencies
- streamlit: Web interface
- pandas: Data analysis
- yfinance: Market data
- pandas-ta: Technical analysis
- plotly: Interactive charts
- twilio: Notifications (optional)

## Project Status
- ✅ Core trading engine operational
- ✅ Portfolio management system active
- ✅ Paper trading interface complete
- ✅ Real-time monitoring dashboard
- 🔄 Machine learning optimization (planned)

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the Streamlit dashboard:
```bash
streamlit run main.py
```

3. Run automated trading:
```bash
python auto_trade.py
```

## Usage

1. Monitor Portfolio:
   - View current positions and performance
   - Track trade history and statistics
   - Monitor automated trading signals

2. Manual Trading:
   - Execute paper trades
   - Test different strategies
   - Track individual trade performance

3. Analysis:
   - View technical indicators
   - Monitor options flow
   - Track analyst ratings and news

## Configuration

The system uses the following configuration files:
- `.streamlit/config.toml`: Streamlit configuration
- `pyproject.toml`: Python dependencies
- `.replit`: Replit-specific configuration

## Optimization

The system collects trading data and signals for machine learning optimization:
- Trade entry/exit points
- Signal effectiveness
- Strategy performance metrics
- Risk/reward ratios

Data is stored in:
- `data/paper_trades.json`: Trade history
- `logs/trading.log`: System logs and performance data
