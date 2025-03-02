import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import logging
from time import sleep

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@st.cache_data(ttl=60)  # Cache for 1 minute only
def get_sp500_stocks(max_retries=3, delay_between_retries=5):
    """Fetch S&P 500 stocks list with retry mechanism and improved error handling"""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    retries = 0

    while retries < max_retries:
        try:
            tables = pd.read_html(url)
            if not tables:
                raise ValueError("No tables found on the page")

            df = tables[0]

            # Validate required columns exist
            required_columns = ['Symbol', 'Security']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"Missing required columns: {required_columns}")

            # Clean and validate data
            df = df[['Symbol', 'Security']].copy()
            df['Symbol'] = df['Symbol'].astype(str).str.strip()

            # Validate we have data
            if df.empty:
                raise ValueError("No data found in S&P 500 table")

            # Sort by symbol to ensure consistent ordering
            df = df.sort_values('Symbol').reset_index(drop=True)

            logging.info(f"Successfully retrieved {len(df)} S&P 500 stocks")
            return df

        except Exception as e:
            retries += 1
            if retries < max_retries:
                logging.warning(f"Attempt {retries} failed to get S&P 500 data: {str(e)}")
                sleep(delay_between_retries)  # Longer delay between retries
            else:
                logging.error(f"Failed to get S&P 500 data after {max_retries} attempts: {str(e)}")
                # Return empty DataFrame with correct columns for error handling
                return pd.DataFrame(columns=['Symbol', 'Security'])

@st.cache_data(ttl=60)  # Cache for 1 minute only
def get_stock_info(symbol):
    """Get basic stock information"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        relevant_info = {
            "Company Name": info.get('longName', 'N/A'),
            "Sector": info.get('sector', 'N/A'),
            "Industry": info.get('industry', 'N/A'),
            "Market Cap": f"${info.get('marketCap', 0):,}",
            "Forward P/E": info.get('forwardPE', 'N/A'),
            "52 Week High": f"${info.get('fiftyTwoWeekHigh', 0):.2f}",
            "52 Week Low": f"${info.get('fiftyTwoWeekLow', 0):.2f}",
            "Last Updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return relevant_info
    except Exception as e:
        logging.error(f"Error fetching info for {symbol}: {str(e)}")
        return {
            "Company Name": symbol,
            "Error": "Failed to fetch data",
            "Last Updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

@st.cache_data(ttl=60)  # Cache for 1 minute only
def get_historical_data(symbol, period='1y', interval='1d', max_retries=3, delay_between_retries=5):
    """Fetch historical stock data with improved retry mechanism and rate limiting handling"""
    retries = 0
    while retries < max_retries:
        try:
            stock = yf.Ticker(symbol)
            end_date = datetime.now()

            # Calculate start date based on period
            if period == '1d':
                start_date = end_date - timedelta(days=1)
            elif period == '5d':
                start_date = end_date - timedelta(days=5)
            elif period == '1mo':
                start_date = end_date - timedelta(days=30)
            elif period == '3mo':
                start_date = end_date - timedelta(days=90)
            elif period == '6mo':
                start_date = end_date - timedelta(days=180)
            elif period == '1y':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=365)  # Default to 1 year

            df = stock.history(
                start=start_date,
                end=end_date,
                interval=interval
            )

            if df.empty:
                raise ValueError(f"No data available for {symbol}")

            # Validate data quality
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"Missing required columns for {symbol}")

            # Check for minimum required data points
            if len(df) < 50:  # Need at least 50 data points for reliable signals
                raise ValueError(f"Insufficient historical data for {symbol} (got {len(df)} rows)")

            logging.info(f"Successfully retrieved historical data for {symbol}")
            return df

        except Exception as e:
            retries += 1
            if "Too Many Requests" in str(e):
                # Exponential backoff for rate limiting
                sleep_time = delay_between_retries * (2 ** (retries - 1))
                logging.warning(f"Rate limit hit for {symbol}, waiting {sleep_time} seconds...")
                sleep(sleep_time)
            elif retries < max_retries:
                logging.warning(f"Attempt {retries} failed to get data for {symbol}: {str(e)}")
                sleep(delay_between_retries)
            else:
                logging.error(f"Failed to get data for {symbol} after {max_retries} attempts: {str(e)}")
                return pd.DataFrame()
