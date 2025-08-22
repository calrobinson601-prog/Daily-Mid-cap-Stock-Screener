# app.py

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from ta.trend import MACD, ADXIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

st.set_page_config(page_title="13-Metric Tactical Screener", layout="wide")

# 📥 Input tickers
st.title("📊 Tactical Stock Screener (13 Metrics)")
tickers = st.text_input("Enter comma-separated tickers", "AAPL, MSFT, NVDA").split(",")

# 📅 Parameters
start_date = st.date_input("Start Date", pd.to_datetime("2024-01-01"))
end_date = st.date_input("End Date", pd.to_datetime("today"))

# 🔍 Finviz scraping for sentiment/fundamental metrics
def scrape_finviz(ticker):
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")
        data = {td.text: td.find_next_sibling("td").text for td in soup.find_all("td", class_="snapshot-td2-cp")}
        return {
            "Insider Buying": "Buy" in data.get("Insider Trans", ""),
            "Short Interest Decline": "-" in data.get("Short Float", ""),
            "Institutional Ownership": float(data.get("Inst Own", "0%").strip('%')) > 50,
            "Earnings Surprise": "+" in data.get("EPS (ttm)", ""),
            "Sector Outperformance": float(data.get("Perf YTD", "0%").strip('%')) > 0
        }
    except:
        return {
            "Insider Buying": False,
            "Short Interest Decline": False,
            "Institutional Ownership": False,
            "Earnings Surprise": False,
            "Sector Outperformance": False
        }

# 📈 Technical analysis
def analyze_stock(ticker):
    df = yf.download(ticker.strip(), start=start_date, end=end_date)
    if df.empty or len(df) < 200:
        return None

    # Clean and validate data
    df = df[pd.to_numeric(df["Close"], errors="coerce").notnull()]
    df.dropna(inplace=True)
    if len(df) < 50:
        return None

    # Initialize indicators safely
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

    # ✅ Technical Metrics
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

    # ✅ Breakout Logic
    if latest["Close"] > df["Close"].rolling(window=20).max().iloc[-1]:
        score += 1
        signals.append("Price Breakout")

    if pd.notnull(latest["Volume_Change"]) and latest["Volume_Change"] > 0.3:
        score += 1
        signals.append("Volume Spike")

    # ✅ Sentiment/Fundamental (via Finviz)
    finviz = scrape_finviz(ticker.strip())
    if finviz["Insider Buying"]:
        score += 1
        signals.append("Insider Buying")

    if finviz["Short Interest Decline"]:
        score += 1
        signals.append("Short Interest Decline")

    if finviz["Institutional Ownership"]:
        score += 1
        signals.append("High Institutional Ownership")

    if finviz["Earnings Surprise"]:
        score += 1
        signals.append("Earnings Surprise")

    if finviz["Sector Outperformance"]:
        score += 1
        signals.append("Sector Outperformance")

    return {
        "Ticker": ticker.strip(),
        "Score": score,
        "Signals": signals,
        "Close": latest["Close"],
        "RSI": round(latest["RSI"], 2) if pd.notnull(latest["RSI"]) else None,
        "ADX": round(latest["ADX"], 2) if pd.notnull(latest["ADX"]) else None,
        "Volume": int(latest["Volume"])
    }

# 🧮 Run analysis
results = []
for ticker in tickers:
    result = analyze_stock(ticker)
    if result:
        results.append(result)

# 📊 Display results
if results:
    df_results = pd.DataFrame(results).sort_values(by="Score", ascending=False)
    st.dataframe(df_results[["Ticker", "Score", "Close", "RSI", "ADX", "Volume", "Signals"]])
else:
    st.warning("No valid data returned. Please check tickers or date range.")
