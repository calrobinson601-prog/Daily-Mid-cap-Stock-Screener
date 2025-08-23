import yfinance as yf
import pandas as pd
import streamlit as st
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
import requests

# --- Settings ---
MID_CAP_TICKERS = ['CPRI', 'FND', 'BLDR', 'SMCI', 'ENPH']  # Replace with full list
NEWS_API_KEY = 'YOUR_API_KEY'  # Finnhub or Alpha Vantage

# --- Helper Functions ---
def fetch_data(ticker):
    df = yf.download(ticker, period="6mo", interval="1d")
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    df.dropna(subset=['Close'], inplace=True)
    return df

def calculate_indicators(df):
    try:
        df['20MA'] = SMAIndicator(close=df['Close'], window=20).sma_indicator()
    except:
        df['20MA'] = pd.Series([None] * len(df), index=df.index)

    try:
        df['50MA'] = SMAIndicator(close=df['Close'], window=50).sma_indicator()
    except:
        df['50MA'] = pd.Series([None] * len(df), index=df.index)

    try:
        df['RSI'] = RSIIndicator(close=df['Close']).rsi()
    except:
        df['RSI'] = pd.Series([None] * len(df), index=df.index)

    try:
        macd = MACD(close=df['Close'])
        df['MACD'] = macd.macd_diff()
    except:
        df['MACD'] = pd.Series([None] * len(df), index=df.index)

    df['VolumeAvg'] = df['Volume'].rolling(window=20).mean()
    return df

def check_breakout_criteria(df):
    latest = df.iloc[-1]
    criteria = {
        "MA Alignment": latest.get('20MA', 0) > latest.get('50MA', 0),
        "RSI Range": 55 <= latest.get('RSI', 0) <= 70,
        "MACD Crossover": latest.get('MACD', 0) > 0,
        "Volume Surge": latest['Volume'] > latest.get('VolumeAvg', 0),
        "Price Above Resistance": latest['Close'] > df['Close'].rolling(20).max().iloc[-2]
    }
    return all(criteria.values())

def get_news_sentiment(ticker):
    url = f"https://finnhub.io/api/v1/news-sentiment?symbol={ticker}&token={NEWS_API_KEY}"
    try:
        response = requests.get(url).json()
        return response.get('sentiment', {}).get('bullishPercent', 0)
    except:
        return 0

# --- Streamlit UI ---
st.title("Mid-Cap Breakout Screener (Low Volatility)")
top_stocks = []

for ticker in MID_CAP_TICKERS:
    df = fetch_data(ticker)
    df = calculate_indicators(df)
    if check_breakout_criteria(df):
        sentiment = get_news_sentiment(ticker)
        if sentiment > 0.5:  # Filter for positive drift
            top_stocks.append((ticker, sentiment))

if top_stocks:
    st.subheader("Top 5 Breakout Candidates")
    for stock in sorted(top_stocks, key=lambda x: x[1], reverse=True)[:5]:
        st.write(f"📈 {stock[0]} — Sentiment Score: {stock[1]:.2f}")
else:
    st.write("No breakout candidates found today.")
