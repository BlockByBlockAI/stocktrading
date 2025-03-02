import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import yfinance as yf
import numpy as np

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_options_chain(symbol, num_expiries):
    """Fetch options chain data for a given symbol"""
    try:
        stock = yf.Ticker(symbol)
        # Get all available expiration dates
        expirations = stock.options

        if not expirations:
            return pd.DataFrame(), []

        # Get options data for each expiration
        all_options = []

        # Use selected number of expiration dates
        for exp in expirations[:num_expiries]:
            calls = stock.option_chain(exp).calls
            puts = stock.option_chain(exp).puts

            # Add expiration date and type to the dataframes
            calls['optionType'] = 'CALL'
            puts['optionType'] = 'PUT'
            calls['expiration'] = exp
            puts['expiration'] = exp

            # Calculate total value of contracts
            calls['totalValue'] = calls['volume'] * calls['lastPrice'] * 100
            puts['totalValue'] = puts['volume'] * puts['lastPrice'] * 100

            all_options.extend([calls, puts])

        # Combine all options data
        options_df = pd.concat(all_options, ignore_index=True)
        return options_df, expirations
    except Exception as e:
        st.error(f"Error fetching options data for {symbol}: {str(e)}")
        return pd.DataFrame(), []

def calculate_options_statistics(options_df):
    """Calculate advanced options statistics"""
    if options_df.empty:
        return {}

    # Calculate money flow
    total_call_value = options_df[options_df['optionType'] == 'CALL']['totalValue'].sum()
    total_put_value = options_df[options_df['optionType'] == 'PUT']['totalValue'].sum()
    net_money_flow = total_call_value - total_put_value

    stats = {
        'total_call_volume': options_df[options_df['optionType'] == 'CALL']['volume'].sum(),
        'total_put_volume': options_df[options_df['optionType'] == 'PUT']['volume'].sum(),
        'put_call_ratio': options_df[options_df['optionType'] == 'PUT']['volume'].sum() / 
                         max(options_df[options_df['optionType'] == 'CALL']['volume'].sum(), 1),
        'total_call_value': total_call_value,
        'total_put_value': total_put_value,
        'net_money_flow': net_money_flow,
        'money_flow_ratio': net_money_flow / (total_call_value + total_put_value) if (total_call_value + total_put_value) > 0 else 0
    }
    return stats

def analyze_options_activity(options_df, vol_threshold, min_volume):
    """Analyze options for significant activity"""
    if options_df.empty:
        return pd.DataFrame()

    # Calculate volume/OI ratio to find unusual activity
    options_df['volume_oi_ratio'] = options_df['volume'] / options_df['openInterest']
    options_df['volume_oi_ratio'] = options_df['volume_oi_ratio'].fillna(0)

    # Calculate money flow using numpy.where for vectorized operation
    options_df['moneyFlow'] = options_df['totalValue'] * np.where(options_df['optionType'] == 'CALL', 1, -1)

    # Filter for significant activity
    significant = options_df[
        (options_df['volume_oi_ratio'] > vol_threshold) & 
        (options_df['volume'] > min_volume)
    ].copy()

    return significant

def create_options_heatmap(options_df, value_column='volume'):
    """Create a heatmap of options activity"""
    if options_df.empty:
        return None

    # Pivot data for heatmap
    heatmap_data = options_df.pivot_table(
        values=value_column,
        index='strike',
        columns=['expiration', 'optionType'],
        aggfunc='sum',
        fill_value=0
    )

    # Create heatmap
    fig = go.Figure()

    # Add heatmap for calls and puts
    for exp in options_df['expiration'].unique():
        fig.add_trace(go.Heatmap(
            z=[[x] for x in heatmap_data[(exp, 'CALL')].values],
            x=[exp],
            y=heatmap_data.index,
            name=f'Calls {exp}',
            colorscale='Greens',
            showscale=True
        ))
        fig.add_trace(go.Heatmap(
            z=[[x] for x in heatmap_data[(exp, 'PUT')].values],
            x=[exp],
            y=heatmap_data.index,
            name=f'Puts {exp}',
            colorscale='Reds',
            showscale=True
        ))

    fig.update_layout(
        title='Options Activity Heatmap',
        yaxis_title='Strike Price',
        template='plotly_white'
    )

    return fig

def display_options_analysis(symbol):
    """Display options analysis for a given symbol"""
    st.subheader("Advanced Options Flow Analysis")

    # Move widget controls outside of cached function
    st.sidebar.subheader("Options Analysis Settings")
    num_expiries = st.sidebar.slider(
        "Number of expiration dates to show",
        min_value=1,
        max_value=12,  # Increased max value for more dates
        value=6  # Default to 6 months
    )

    vol_threshold = st.sidebar.slider(
        "Volume/OI Ratio Threshold",
        min_value=0.1,
        max_value=1.0,
        value=0.2,
        step=0.1
    )

    min_volume = st.sidebar.number_input(
        "Minimum Volume",
        min_value=10,
        value=100,
        step=10
    )

    # Get options data using the selected number of expiries
    options_df, expiration_dates = get_options_chain(symbol, num_expiries)

    if options_df.empty:
        st.info("No options data available for this stock.")
        return

    # Calculate and display options statistics
    stats = calculate_options_statistics(options_df)

    # Display money flow analysis
    st.subheader("Options Money Flow")
    st.write("""
    Money flow indicates the direction and strength of options activity:
    - Positive flow (green) suggests bullish sentiment (more call buying)
    - Negative flow (red) suggests bearish sentiment (more put buying)
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Net Money Flow", 
                 f"${stats['net_money_flow']:,.0f}",
                 delta="Bullish" if stats['net_money_flow'] > 0 else "Bearish")
    with col2:
        st.metric("Call Flow", f"${stats['total_call_value']:,.0f}")
    with col3:
        st.metric("Put Flow", f"${stats['total_put_value']:,.0f}")

    # Display volume metrics
    st.subheader("Options Volume")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Put/Call Ratio", f"{stats['put_call_ratio']:.2f}")
    with col2:
        st.metric("Total Call Volume", f"{stats['total_call_volume']:,.0f}")
    with col3:
        st.metric("Total Put Volume", f"{stats['total_put_volume']:,.0f}")

    # Display options flow
    st.subheader("Options Flow Visualization")
    flow_type = st.radio("View", ["Volume", "Money Flow"])

    # Create and display heatmap
    heatmap_fig = create_options_heatmap(
        options_df, 
        'totalValue' if flow_type == "Money Flow" else 'volume'
    )
    if heatmap_fig:
        st.plotly_chart(heatmap_fig, use_container_width=True)

    # Filter for significant activity using the selected thresholds
    significant_activity = analyze_options_activity(options_df, vol_threshold, min_volume)

    if significant_activity.empty:
        st.info("No significant options activity detected with current filters.")
        return

    # Display unusual options activity
    st.subheader("Unusual Options Activity")

    # Create scatter plot of unusual activity
    fig = go.Figure()

    # Plot calls and puts separately
    for option_type in ['CALL', 'PUT']:
        data = significant_activity[significant_activity['optionType'] == option_type]

        if not data.empty:
            fig.add_trace(go.Scatter(
                x=data['strike'],
                y=data['volume'],
                mode='markers',
                name=f'{option_type}s',
                marker=dict(
                    size=data['volume_oi_ratio'] * 50,  # Size based on volume/OI ratio
                    color='green' if option_type == 'CALL' else 'red'
                ),
                text=[
                    f"Strike: ${strike:.2f}<br>"
                    f"Exp: {exp}<br>"
                    f"Volume: {vol:,.0f}<br>"
                    f"OI: {oi:,.0f}<br>"
                    f"V/OI: {ratio:.2f}<br>"
                    f"Value: ${value:,.2f}"
                    for strike, exp, vol, oi, ratio, value in zip(
                        data['strike'], 
                        data['expiration'],
                        data['volume'],
                        data['openInterest'],
                        data['volume_oi_ratio'],
                        data['totalValue']
                    )
                ],
                hoverinfo='text'
            ))

    fig.update_layout(
        title=f'Significant Options Activity - {symbol}',
        xaxis_title='Strike Price',
        yaxis_title='Volume',
        template='plotly_white',
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)

    # Display tabular data
    st.subheader("Notable Options Activity")
    display_df = significant_activity[[
        'expiration', 'optionType', 'strike', 'lastPrice',
        'volume', 'openInterest', 'volume_oi_ratio', 'totalValue'
    ]].sort_values('volume_oi_ratio', ascending=False)

    st.dataframe(display_df)
