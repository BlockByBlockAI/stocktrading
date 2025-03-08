import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from modules.stock_data import get_historical_data

def calculate_macd(data, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence/Divergence) and its signal line."""
    fast_ema = data.ewm(span=fast, adjust=False).mean()
    slow_ema = data.ewm(span=slow, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    macd_hist = macd_line - signal_line
    return macd_line, signal_line, macd_hist

def calculate_bollinger_bands(data, window=20, num_std=2):
    """Calculate Bollinger Bands (upper and lower bands) for the given window."""
    rolling_mean = data.rolling(window).mean()
    rolling_std = data.rolling(window).std()
    upper_band = rolling_mean + num_std * rolling_std
    lower_band = rolling_mean - num_std * rolling_std
    return rolling_mean, upper_band, lower_band

def calculate_atr(df, period=14):
    """Calculate Average True Range for volatility measurement."""
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift(1)).abs()
    low_close = (df['Low'] - df['Close'].shift(1)).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr

def calculate_sma(data, window):
    """Calculate Simple Moving Average"""
    return data.rolling(window=window).mean()

def calculate_rsi(data, periods=14):
    """Calculate Relative Strength Index"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_support_resistance(df, window=20):
    """Calculate support and resistance levels"""
    highs = df['High'].rolling(window=window).max()
    lows = df['Low'].rolling(window=window).min()
    return lows, highs

def display_technical_analysis(symbol):
    # Get historical data
    df = get_historical_data(symbol)

    # Calculate technical indicators
    df['SMA_20'] = calculate_sma(df['Close'], 20)
    df['SMA_50'] = calculate_sma(df['Close'], 50)
    df['RSI'] = calculate_rsi(df['Close'])

    # Support and resistance
    support, resistance = calculate_support_resistance(df)

    # Create interactive chart
    fig = go.Figure()

    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='OHLC'
    ))

    # Add moving averages
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['SMA_20'],
        name='SMA 20',
        line=dict(color='blue')
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['SMA_50'],
        name='SMA 50',
        line=dict(color='orange')
    ))

    # Update layout
    fig.update_layout(
        title=f'{symbol} Technical Analysis',
        yaxis_title='Price',
        xaxis_title='Date',
        template='plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Display RSI alerts instead of chart
    current_rsi = df['RSI'].iloc[-1]
    mean_rsi = df['RSI'].mean()

    # Create a container for RSI alerts
    rsi_container = st.container()

    with rsi_container:
        st.write("### RSI Analysis")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Current RSI", f"{current_rsi:.2f}")
        with col2:
            st.metric("Mean RSI", f"{mean_rsi:.2f}")

        # Display RSI alerts
        if current_rsi > 70:
            st.warning(f"⚠️ RSI is OVERBOUGHT at {current_rsi:.2f} (Mean: {mean_rsi:.2f})")
        elif current_rsi < 30:
            st.warning(f"⚠️ RSI is OVERSOLD at {current_rsi:.2f} (Mean: {mean_rsi:.2f})")
        else:
            st.info(f"RSI is within normal range at {current_rsi:.2f} (Mean: {mean_rsi:.2f})")
