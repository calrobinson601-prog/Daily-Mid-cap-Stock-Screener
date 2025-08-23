import yfinance as yf
import pandas as pd
import streamlit as st
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
import requests

# --- Settings ---
MID_CAP_TICKERS = ['CPRI', 'FND', 'BLDR', 'SMCI', 'ENPH']  # Add more tickers
NEWS_API_KEY = 'YOUR_API_KEY'  # Replace with your Finnhub or Alpha Vantage key

TICKER_SECTORS = {
    'CPRI': 'Consumer Cyclical',
    'FND': 'Consumer Cyclical',
    'BLDR': 'Industrials',
    'SMCI': 'Technology',
    'ENPH': 'Technology',
    # Add more mappings as needed
}

# --- Streamlit UI ---
st.title("Mid-Cap Breakout Screener (Low Volatility)")
selected_sectors = st.multiselect("Select sectors to scan:", list(set(TICKER_SECTORS.values())), default=['Technology', 'Industrials'])

# --- Helper Functions ---
def fetch_data(ticker):
    df = yf.download(ticker, period="6mo", interval="1d", group_by='column')
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(1)
    if 'Close' in df.columns:
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        df.dropna(subset=['Close'], inplace=True)
    else:
        df['Close'] = pd.Series([None] * len(df), index=df.index)
    return df

def calculate_indicators(df):
    df['20MA'] = SMAIndicator(close=df['Close'], window=20).sma_indicator()
    df['50MA'] = SMAIndicator(close=df['Close'], window=50).sma_indicator()
    df['RSI'] = RSIIndicator(close=df['Close']).rsi()
    macd = MACD(close=df['Close'])
    df['MACD'] = macd.macd_diff()
    df['VolumeAvg'] = df['Volume'].rolling(window=20).mean()
    return df

def get_market_cap(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get('marketCap', 0)
    except:
        return 0

def calculate_atr(df):
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(14).mean()
    return atr / df['Close']

def evaluate_breakout(df, ticker):
    latest = df.iloc[-1]
    breakout_score = 0
    total_criteria = 7

    market_cap = get_market_cap(ticker)
    atr_pct = calculate_atr(df).iloc[-1]
    volume = latest.get('Volume', 0)

    if 2e9 <= market_cap <= 15e9:
        breakout_score += 1
    if volume > 250_000:
        breakout_score += 1
    if atr_pct < 0.04:
        breakout_score += 1
    if latest.get('20MA', 0) > latest.get('50MA', 0):
        breakout_score += 1
    if 55 <= latest.get('RSI', 0) <= 70:
        breakout_score += 1
    if latest.get('MACD', 0) > 0:
        breakout_score += 1
    if latest['Close'] > df['Close'].rolling(20).max().iloc[-2]:
        breakout_score += 1

    stealth = False
    bb_width = df['Close'].rolling(20).std().iloc[-1] * 4
    if bb_width < df['Close'].rolling(20).std().mean() * 0.6:
        stealth = True
    if df['High'].iloc[-1] < df['High'].iloc[-2] and df['Low'].iloc[-1] > df['Low'].iloc[-2]:
        stealth = True

    score_pct = breakout_score / total_criteria
    if score_pct == 1:
        return "Confirmed Breakout"
    elif score_pct >= 0.9:
        return "Near Breakout"
    elif stealth:
        return "Stealth Setup"
    else:
        return None

def forecast_breakout(df, ticker):
    if len(df) < 3:
        return None

    latest = df.iloc[-1]
    prior = df.iloc[-2]
    earlier = df.iloc[-3]

    resistance = df['Close'].rolling(20).max().iloc[-2]
    price_near_resistance = 0.98 * resistance <= latest['Close'] <= resistance

    macd_bullish = latest.get('MACD', 0) > 0 and prior.get('MACD', 0) > 0 and earlier.get('MACD', 0) <= 0
    rsi_rising = latest.get('RSI', 0) > prior.get('RSI', 0) > earlier.get('RSI', 0) and latest.get('RSI', 0) > 50
    volume_surge = latest['Volume'] > df['Volume'].rolling(20).mean().iloc[-1]

    bb_width = df['Close'].rolling(20).std().iloc[-1] * 4
    squeeze = bb_width < df['Close'].rolling(20).std().mean() * 0.6

    if price_near_resistance and macd_bullish and rsi_rising and volume_surge and squeeze:
        return "Forecasted Breakout (2–3 Day Horizon)"
    return None

def get_news_sentiment(ticker):
    url = f"https://finnhub.io/api/v1/news-sentiment?symbol={ticker}&token={NEWS_API_KEY}"
    try:
        response = requests.get(url).json()
        return response.get('sentiment', {}).get('bullishPercent', 0)
    except:
        return 0

# --- Main Loop ---
top_stocks = []

for ticker in MID_CAP_TICKERS:
    sector = TICKER_SECTORS.get(ticker, 'Unknown')
    if sector not in selected_sectors:
        continue

    df = fetch_data(ticker)
    if df.empty or df['Close'].isnull().all():
        continue

    df = calculate_indicators(df)
    result = evaluate_breakout(df, ticker)
    forecast = forecast_breakout(df, ticker)

    if result:
        sentiment = get_news_sentiment(ticker)
        if sentiment > 0.5:
            top_stocks.append((ticker, result, sector, sentiment))
    elif forecast:
        sentiment = get_news_sentiment(ticker)
        if sentiment > 0.5:
            top_stocks.append((ticker, forecast, sector, sentiment))

# --- Display Results ---
if top_stocks:
    st.subheader("Breakout & Forecasted Candidates")
    for stock in sorted(top_stocks, key=lambda x: x[3], reverse=True):
        st.write(f"📈 {stock[0]} — {stock[1]} — Sector: {stock[2]} — Sentiment Score: {stock[3]:.2f}")
else:
    st.write("No breakout or forecasted candidates found today.")
