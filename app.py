import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

st.title("📈 Tactical Mid-Cap Screener: Top 5 Breakout Picks with Timing Intelligence")

# --- Define mid-cap tickers (customizable)
tickers = ["AEO", "BLDR", "FND", "HUBG", "SMCI", "TPX", "TOL", "WEN", "WOLF", "ZUMZ"]

# --- Breakout metric function
def calculate_metrics(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        info = stock.info

        if hist.empty or "Close" not in hist or "Volume" not in hist:
            return None

        close = hist["Close"]
        volume = hist["Volume"]

        # 1. Momentum (6-month return)
        momentum = (close[-1] - close[0]) / close[0]
        score1 = 1 if momentum > 0.15 else 0

        # 2. Volume Surge (last day vs. 20-day avg)
        vol_ratio = volume[-1] / volume[-20:].mean()
        score2 = 1 if vol_ratio > 1.5 else 0

        # 3. RSI (Relative Strength Index)
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        score3 = 1 if 30 < rsi.iloc[-1] < 70 else 0

        # 4. MACD Crossover
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        score4 = 1 if macd.iloc[-1] > signal.iloc[-1] else 0

        # 5. Earnings Growth
        earnings_growth = info.get("earningsQuarterlyGrowth", 0)
        score5 = 1 if earnings_growth and earnings_growth > 0.1 else 0

        # 6. Institutional Ownership
        inst_own = info.get("heldPercentInstitutions", 0)
        score6 = 1 if inst_own and inst_own > 0.5 else 0

        # 7. Short Interest Ratio
        short_ratio = info.get("shortRatio", 0)
        score7 = 1 if short_ratio and short_ratio < 5 else 0

        # Composite breakout score
        total_score = score1 + score2 + score3 + score4 + score5 + score6 + score7

        # Predictive gain potential: based on momentum + volume + MACD
        gain_potential = 0
        if momentum > 0.05: gain_potential += 1
        if vol_ratio > 1.5: gain_potential += 1
        if macd.iloc[-1] > signal.iloc[-1]: gain_potential += 1

        # --- Best Day to Buy Analysis
        hist["Return"] = hist["Close"].pct_change()
        hist["Weekday"] = hist.index.day_name()
        weekday_perf = hist.groupby("Weekday")["Return"].mean().sort_values(ascending=False)

        best_day = weekday_perf.idxmax()
        best_day_return = weekday_perf.max()

        # --- Next Upcoming Best Day
        weekday_map = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4
        }

        today = pd.Timestamp.today().tz_localize("America/Chicago")
        today_weekday = today.weekday()
        best_day_num = weekday_map.get(best_day, None)

        if best_day_num is not None:
            days_ahead = (best_day_num - today_weekday + 7) % 7
            next_best_day = today + pd.Timedelta(days=days_ahead)
            next_best_day_str = next_best_day.strftime("%A, %b %d")
        else:
            next_best_day_str = "N/A"

        return {
            "Ticker": ticker,
            "Breakout Score": total_score,
            "Gain Potential Score": gain_potential,
            "Momentum": round(momentum, 2),
            "Volume Surge": round(vol_ratio, 2),
            "RSI": round(rsi.iloc[-1], 2),
            "MACD > Signal": bool(score4),
            "Earnings Growth": round(earnings_growth, 2) if earnings_growth else "N/A",
            "Institutional Ownership": round(inst_own, 2) if inst_own else "N/A",
            "Short Ratio": round(short_ratio, 2) if short_ratio else "N/A",
            "Best Day to Buy": best_day,
            "Avg Return on Best Day (%)": round(best_day_return * 100, 2),
            "Next Best Buy Date": next_best_day_str
        }

    except Exception as e:
        st.warning(f"{ticker} skipped due to error: {e}")
        return None

# --- Run screener
results = []
for ticker in tickers:
    metrics = calculate_metrics(ticker)
    if metrics and "Gain Potential Score" in metrics:
        results.append(metrics)

# --- Display top 5
if results:
    df = pd.DataFrame(results)
    top5 = df.sort_values(by="Gain Potential Score", ascending=False).head(5)
    st.subheader("🔝 Top 5 Mid-Cap Stocks Likely to Gain 5% Today")
    st.dataframe(top5)
else:
    st.error("No valid data returned. Please check tickers or try again later.")
