import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from modules.stock_data import get_historical_data

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
