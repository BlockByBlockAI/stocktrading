import streamlit as st
from datetime import datetime, timedelta
import yfinance as yf
import trafilatura
import urllib.parse
import pandas as pd
import json
from bs4 import BeautifulSoup

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_stock_news(symbol):
    """Fetch news from multiple sources"""
    try:
        # Get company name for better Google News search
        stock = yf.Ticker(symbol)
        company_name = stock.info.get('longName', symbol)

        # Get Yahoo Finance news
        yf_news = stock.news or []

        # Get Google News
        google_news = get_google_news(company_name)

        # Combine and sort news from both sources
        all_news = yf_news + google_news
        sorted_news = sorted(all_news, key=lambda x: x.get('providerPublishTime', 0), reverse=True)
        return sorted_news[:10]  # Return latest 10 news items
    except Exception as e:
        st.error(f"Error fetching news for {symbol}: {str(e)}")
        return []

def get_google_news(company_name):
    """Fetch news from Google News"""
    try:
        # Encode company name for URL
        encoded_name = urllib.parse.quote(company_name)
        url = f"https://news.google.com/search?q={encoded_name}%20stock&hl=en-US&gl=US&ceid=US%3Aen"

        # Download and extract content
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return []

        # Extract text content with XML format
        content = trafilatura.extract(downloaded, 
                                    include_links=True, 
                                    output_format='xml',
                                    with_metadata=True)

        if not content:
            return []

        # Parse XML content
        soup = BeautifulSoup(content, 'xml')
        articles = []
        current_timestamp = int(datetime.now().timestamp())

        # Find all paragraphs (news items)
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text:
                # Split text into parts (source, title, date, author)
                parts = text.split('More')
                if len(parts) >= 2:
                    source = parts[0].strip()
                    title = parts[1].strip()

                    # Create article structure similar to Yahoo Finance
                    article = {
                        'title': title,
                        'summary': text,
                        'link': url,
                        'providerPublishTime': current_timestamp,
                        'source': source
                    }
                    articles.append(article)

        return articles
    except Exception as e:
        st.error(f"Error fetching Google News: {str(e)}")
        return []

def format_earnings_date(dates):
    """Format earnings dates into a readable string"""
    if isinstance(dates, list):
        if len(dates) == 1:
            return dates[0].strftime('%Y-%m-%d')
        elif len(dates) == 2:
            return f"{dates[0].strftime('%Y-%m-%d')} to {dates[1].strftime('%Y-%m-%d')}"
    return str(dates)

def format_financial_value(value):
    """Format financial values with proper notation"""
    if value is None or value == 'N/A':
        return 'N/A'

    try:
        if isinstance(value, (int, float)):
            if value >= 1_000_000_000:  # Billions
                return f"${value/1_000_000_000:.2f}B"
            elif value >= 1_000_000:  # Millions
                return f"${value/1_000_000:.2f}M"
            else:
                return f"${value:,.2f}"
        return str(value)
    except:
        return 'N/A'

def get_earnings_calendar(symbol):
    """Fetch earnings calendar information"""
    try:
        stock = yf.Ticker(symbol)
        calendar = stock.calendar
        if calendar is None:
            return None

        # Format earnings data
        earnings_date = calendar.get('Earnings Date')
        revenue_estimate = calendar.get('Revenue Estimate')
        earnings_estimate = calendar.get('Earnings Estimate')

        # Get actual values from info if available
        info = stock.info
        if not revenue_estimate and 'revenueEstimate' in info:
            revenue_estimate = info['revenueEstimate']
        if not earnings_estimate and 'forwardEps' in info:
            earnings_estimate = info['forwardEps']

        earnings_info = {
            'Earnings Date': format_earnings_date(earnings_date) if earnings_date else 'N/A',
            'Revenue Estimate': format_financial_value(revenue_estimate),
            'Earnings Estimate': format_financial_value(earnings_estimate),
            'Last Updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return earnings_info
    except Exception as e:
        st.error(f"Error fetching earnings calendar for {symbol}: {str(e)}")
        return None

def get_analyst_ratings(symbol):
    """Fetch analyst ratings for the stock"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        ratings = {
            'Recommendation': info.get('recommendationKey', 'N/A').upper(),
            'Mean Rating': info.get('recommendationMean', 'N/A'),
            'Number of Analysts': info.get('numberOfAnalystOpinions', 'N/A'),
            'Target Price': f"${info.get('targetMeanPrice', 'N/A')}",
            'Target High': f"${info.get('targetHighPrice', 'N/A')}",
            'Target Low': f"${info.get('targetLowPrice', 'N/A')}"
        }
        return ratings
    except Exception as e:
        st.error(f"Error fetching analyst ratings for {symbol}: {str(e)}")
        return {}

def display_news(symbol):
    st.subheader("Latest News")
    news_items = get_stock_news(symbol)

    if not news_items:
        st.info("No recent news available for this stock.")
        return

    for news in news_items:
        # Handle different timestamp keys that might be present
        timestamp = news.get('providerPublishTime') or news.get('publishTime') or news.get('time', 0)
        publish_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')

        source = news.get('source', 'Yahoo Finance')
        st.write(f"**{news.get('title', 'No title available')}** - *{source}*")
        st.write(f"*{publish_date}*")
        st.write(news.get('summary', 'No summary available'))
        if 'link' in news:
            st.write(f"[Read more]({news['link']})")
        st.markdown("---")

def display_earnings_calendar(symbol):
    st.subheader("Upcoming Earnings")
    earnings_info = get_earnings_calendar(symbol)

    if earnings_info:
        col1, col2 = st.columns(2)

        # Display earnings date separately
        st.write(f"**Earnings Date:** {earnings_info['Earnings Date']}")

        # Display estimates in columns
        with col1:
            st.metric("Revenue Estimate", earnings_info['Revenue Estimate'])
        with col2:
            st.metric("EPS Estimate", earnings_info['Earnings Estimate'])

        # Show last updated time
        st.caption(f"Last updated: {earnings_info['Last Updated']}")
    else:
        st.info("No earnings calendar information available.")

def display_analyst_ratings(symbol):
    st.subheader("Analyst Ratings")
    ratings = get_analyst_ratings(symbol)

    if not ratings:
        st.info("No analyst ratings available for this stock.")
        return

    # Create columns for better layout
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Consensus", ratings.get('Recommendation', 'N/A'))
        st.metric("Mean Rating", ratings.get('Mean Rating', 'N/A'))
        st.metric("Number of Analysts", ratings.get('Number of Analysts', 'N/A'))

    with col2:
        st.metric("Target Price", ratings.get('Target Price', 'N/A'))
        st.metric("Target High", ratings.get('Target High', 'N/A'))
        st.metric("Target Low", ratings.get('Target Low', 'N/A'))
