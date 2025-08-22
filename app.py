import streamlit as st
import pandas as pd
from datetime import datetime

# Sample data — replace with your actual metrics or connect to your backend
data = {
    'Ticker': ['TOL', 'WEN', 'ABC', 'XYZ', 'DEF'],
    'Breakout Score': [7.2, 3.5, 5.1, 2.0, 8.0],
    'Volume Surge': [1.8, 0.9, 1.2, 0.5, 2.1],
    'Best Day to Buy': ['Tuesday', 'Friday', 'Monday', 'Thursday', 'Wednesday'],
    'Momentum': [0.26, -0.31, 0.05, -0.45, 0.33],
    'Gain Potential Score': [3, 1, 2, 0, 3],
    'Sector Strength': ['Strong', 'Weak', 'Neutral', 'Weak', 'Strong']
}

df = pd.DataFrame(data)

# Step 1: Classify signal strength
def classify_signal(row):
    if row['Gain Potential Score'] == 3 or row['Momentum'] > 0.2:
        return '✅ Positive Setup'
    elif row['Momentum'] < -0.2 or row['Gain Potential Score'] == 0:
        return '❌ Negative'
    else:
        return '⚠️ Neutral'

df['Signal'] = df.apply(classify_signal, axis=1)

# Step 2: Add emoji icon column
df['Signal Icon'] = df['Signal'].map({
    '✅ Positive Setup': '🟢',
    '⚠️ Neutral': '🟡',
    '❌ Negative': '🔴'
})

# Step 3: Generate AI tactical notes
def generate_note(row):
    if row['Signal'] == '✅ Positive Setup':
        return f"Strong setup — consider entry on {row['Best Day to Buy']} with breakout score {row['Breakout Score']:.1f}."
    elif row['Signal'] == '⚠️ Neutral':
        return f"Mixed signals — momentum is modest. Watch for volume confirmation."
    else:
        return f"Under pressure — avoid entry until momentum improves."

df['AI Note'] = df.apply(generate_note, axis=1)

# Step 4: Add Buy-Day Alert
today = datetime.today().strftime('%A')  # e.g., 'Friday'
df['Buy-Day Alert'] = df['Best Day to Buy'].apply(
    lambda x: '🔔 Today is the optimal entry day!' if x == today else ''
)

# Step 5: Define color styling for Signal column
def color_signal(val):
    if val == '✅ Positive Setup':
        return 'background-color: lightgreen; color: black'
    elif val == '⚠️ Neutral':
        return 'background-color: #fff3cd; color: black'
    elif val == '❌ Negative':
        return 'background-color: lightcoral; color: white'
    else:
        return ''

# Step 6: Sidebar filter for dynamic selection
st.sidebar.title("🔍 Filter Tactical Setups")
signal_filter = st.sidebar.selectbox(
    "Choose signal type:",
    options=["All", "✅ Positive Setup", "⚠️ Neutral", "❌ Negative"]
)

# Step 7: Filter DataFrame based on selection
if signal_filter == "All":
    filtered_df = df
else:
    filtered_df = df[df['Signal'] == signal_filter]

# Step 8: Display styled DataFrame
st.title("📊 Tactical Stock Screener")
st.subheader(f"Showing: {signal_filter} Signals")

styled_df = filtered_df.style.applymap(color_signal, subset=['Signal'])
st.dataframe(styled_df)

# Step 9: Highlight Buy-Day Alerts
if any(filtered_df['Buy-Day Alert']):
    st.subheader("🔔 Today's Entry Alerts")
    for _, row in filtered_df.iterrows():
        if row['Buy-Day Alert']:
            st.markdown(f"**{row['Ticker']}** → {row['Buy-Day Alert']}")


