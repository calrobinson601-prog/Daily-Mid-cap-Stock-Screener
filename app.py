import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
from ta.trend import MACD, ADXIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

# 🔍 Define the analysis function
def analyze_stock(ticker, start_date, end_date):
    ticker = ticker.strip().upper()
    if not ticker:
        st.warning("Empty ticker skipped.")
        return None

    try:
        df = yf.download(ticker, start=start_date, end=end_date)
    except Exception as e:
        st.error(f"Failed to download data for {ticker}: {e}")
        return None

    if df.empty or len(df) < 200:
        st.warning(f"No sufficient data for {ticker}.")
        return None

    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df.dropna(subset=["Close"], inplace=True)
    df.dropna(inplace=True)
    if len(df) < 50:
        st.warning(f"Not enough clean data for {ticker}.")
        return None

    try:
        df["RSI"] = RSIIndicator(close=df["Close"]).rsi()
    except Exception as e:
        st.warning(f"RSI failed for {ticker}: {e}")
        df["RSI"] = np.nan

    try:
        macd = MACD(close=df["Close"])
        df["MACD_diff"] = macd.macd_diff()
    except Exception as e:
        st.warning(f"MACD failed for {ticker}: {e}")
        df["MACD_diff"] = np.nan

    try:
        bb = BollingerBands(close=df["Close"])
        df["Upper_BB"] = bb.bollinger_hband()
    except Exception as e:
        st.warning(f"Bollinger Bands failed for {ticker}: {e}")
        df["Upper_BB"] = np.nan

    try:
        df["ADX"] = ADXIndicator(df["High"], df["Low"], df["Close"]).adx()
    except Exception as e:
        st.warning(f"ADX failed for {ticker}: {e}")
        df["ADX"] = np.nan

    df["MA_50"] = df["Close"].rolling(window=50).mean()
    df["MA_200"] = df["Close"].rolling(window=200).mean()
    df["Volume_Change"] = df["Volume"].pct_change()

    latest = df.iloc[-1]
    score = 0
    signals = []

    if pd.notnull(latest["RSI"]) and (latest["RSI"] < 30 or latest["RSI"] > 70):
        score += 1
        signals.append("RSI Trigger")

    if pd.notnull(latest["MACD_diff"]) and latest["MACD_diff"] > 0 and df["MACD_diff"].iloc[-2] < 0:
        score += 1
        signals.append("MACD Bullish Crossover")

    if pd.notnull(latest["Upper_BB"]) and latest["Close"] > latest["Upper_BB"]:
        score += 1
        signals.append("Bollinger Band Breakout")

    if pd.notnull(latest["Volume_Change"]) and latest["Volume_Change"] > 0.5:
        score += 1
        signals.append("Volume Surge")

    if pd.notnull(latest["MA_50"]) and pd.notnull(latest["MA_200"]) and latest["MA_50"] > latest["MA_200"]:
        score += 1
        signals.append("Golden Cross")

    if pd.notnull(latest["ADX"]) and latest["ADX"] > 25:
        score += 1
        signals.append("ADX > 25")

    if latest["Close"] > df["Close"].rolling(window=20).max().iloc[-1]:
        score += 1
        signals.append("Price Breakout")

    if pd.notnull(latest["Volume_Change"]) and latest["Volume_Change"] > 0.3:
        score += 1
        signals.append("Volume Spike")

    # 🔍 Simulated Finviz data (replace with real scrape if available)
    finviz = {
        "Insider Buying": True,
        "Short Interest Decline": False,
        "Institutional Ownership": True,
        "Earnings Surprise": True,
        "Sector Outperformance": False
    }

    if finviz.get("Insider Buying"):
        score += 1
        signals.append("Insider Buying")

    if finviz.get("Short Interest Decline"):
        score += 1
        signals.append("Short Interest Decline")

    if finviz.get("Institutional Ownership"):
        score += 1
        signals.append("High Institutional Ownership")

    if finviz.get("Earnings Surprise"):
        score += 1
        signals.append("Earnings Surprise")

    if finviz.get("Sector Outperformance"):
        score += 1
        signals.append("Sector Outperformance")

    if st.checkbox("Show raw data"):
        st.dataframe(df.tail(30))

    return {
        "Ticker": ticker,
        "Score": score,
        "Signals": signals,
        "Close": latest["Close"],
        "RSI": round(latest["RSI"], 2) if pd.notnull(latest["RSI"]) else None,
        "ADX": round(latest["ADX"], 2) if pd.notnull(latest["ADX"]) else None,
        "Volume": int(latest["Volume"])
    }

# 🧭 Streamlit App Interface
st.title("📈 Stock Signal Analyzer")
st.write("Enter a stock ticker to evaluate technical and sentiment signals.")

start_date = "2023-01-01"
end_date = datetime.today().strftime("%Y-%m-%d")

ticker = st.text_input("Ticker Symbol", value="AAPL")

if st.button("Analyze"):
    result = analyze_stock(ticker, start_date, end_date)

    if result:
        st.subheader(f"Results for {result['Ticker']}")
        st.metric("Score", result["Score"])
        st.write("### Signals")
        for signal in result["Signals"]:
            st.markdown(f"- {signal}")
        st.write(f"**Close Price:** ${result['Close']:.2f}")
        st.write(f"**RSI:** {result['RSI']}")
        st.write(f"**ADX:** {result['ADX']}")
        st.write(f"**Volume:** {result['Volume']:,}")
    else:
        st.info("No actionable data found for this ticker.")
