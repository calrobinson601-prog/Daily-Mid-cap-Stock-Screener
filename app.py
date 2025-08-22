def analyze_stock(ticker):
    df = yf.download(ticker.strip(), start=start_date, end=end_date)
    if df.empty or len(df) < 200:
        return None

    # ✅ Clean and validate data
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df.dropna(subset=["Close"], inplace=True)
    df.dropna(inplace=True)
    if len(df) < 50:
        return None

    # ✅ Initialize indicators safely
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
