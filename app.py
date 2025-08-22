# tactical_screener.py

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Mid-Cap Tactical Screener", layout="wide")
st.title("📊 Mid-Cap Tactical Screener")
st.caption("Live breakout scoring based on price action, RSI, volume, and 52-week range")

# Define mid-cap tickers to scan
tickers = ['BLDR', 'FND', 'TOL', 'WEN', 'ZUMZ']

@st.cache_data(ttl=3600)
def fetch_metrics(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1mo")
    info = stock.info

    price = info.get('currentPrice', None)
    high_52w = info.get('fiftyTwoWeekHigh', None)
    low_52w = info.get('fiftyTwoWeekLow', None)
    volume = info.get('volume', None)
    avg_volume = info.get('averageVolume', None)

    # RSI calculation
    rsi = None
    if not hist.empty:
        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs.iloc[-1])) if rs.iloc[-1] else None

    return {
        'Ticker': ticker,
        'Price': price,
        '52W High': high_52w,
        '52W Low': low_52w,
        'Volume': volume,
        'Avg Volume': avg_volume,
        'RSI': round(rsi, 2) if rsi else None
    }

# Fetch live data
live_data = [fetch_metrics(t) for t in tickers]
df = pd.DataFrame(live_data)

# Tactical scoring logic
def score_row(row):
    score = 0
    if row['Price'] and row['52W High']:
        breakout_ratio = row['Price'] / row['52W High']
        if breakout_ratio > 0.95:
            score += 2
        elif breakout_ratio > 0.90:
            score += 1

    if row['RSI']:
        if 50 < row['RSI'] < 70:
            score += 2
        elif 40 < row['RSI'] <= 50:
            score += 1

    if row['Volume'] and row['Avg Volume']:
        vol_ratio = row['Volume'] / row['Avg Volume']
        if vol_ratio > 1.2:
            score += 2
        elif vol_ratio > 1.0:
            score += 1

    return score

df['Score'] = df.apply(score_row, axis=1)
df = df.sort_values(by='Score', ascending=False)

# Display results
st.subheader("🏆 Top Tactical Setups")
st.dataframe(df.style.highlight_max(axis=0, subset=['Score']), use_container_width=True)

# Optional: Show raw metrics
with st.expander("📋 Raw Metrics"):
    st.write(df)
