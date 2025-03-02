# Algorithmic Trading Platform

An advanced algorithmic trading platform that combines technical analysis, options strategies, and automated paper trading.

## Features

- Multi-signal trading strategy (RSI, options flow, analyst ratings)
- Complex options strategies (spreads, iron condors, butterflies)
- Automated paper trading for top 50 S&P stocks
- Real-time market data and signal processing
- Risk management with position sizing and stop-loss
- Performance tracking and analytics dashboard

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

## Components

### Trading Engine
- `auto_trade.py`: Automated trading engine running Mon-Fri during market hours
- `modules/trading_strategy.py`: Signal generation and trade execution
- `modules/options_strategies.py`: Options strategy selection and execution
- `modules/portfolio_manager.py`: Portfolio and risk management

### Analysis
- `modules/stock_data.py`: Market data fetching and processing
- `modules/news_analysis.py`: News and analyst ratings analysis
- `modules/technical_analysis.py`: Technical indicators and chart patterns

### Interface
- `main.py`: Streamlit dashboard for monitoring and analysis
- `modules/paper_trading.py`: Manual paper trading interface

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
