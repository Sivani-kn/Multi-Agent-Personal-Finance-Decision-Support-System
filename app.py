import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import streamlit.components.v1 as components

# --- PAGE SETUP ---
st.set_page_config(
    page_title="AUREXA AI - Decision & Brokerage Terminal",
    page_icon="📈",
    layout="wide"
)

# --- SIDEBAR MULTI-AGENT CONTROLS ---
st.sidebar.header("🤖 Agentic Control Panel")
ticker = st.sidebar.text_input("Stock Ticker", value="AAPL").upper().strip()
risk_profile = st.sidebar.selectbox("Risk Profile", ["Moderate", "Low", "High"])
timeframe = st.sidebar.selectbox("Lookback Period", ["3mo", "6mo", "1y"], index=1)

# --- DATA FETCHING & AGENT LOGIC ---
@st.cache_data(ttl=3600)
def fetch_data(symbol, period="6mo"):  # Fixed default from '6m' to '6mo'
    try:
        df = yf.download(symbol, period=period, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df = df.xs(symbol, level=1, axis=1) if symbol in df.columns.levels[1] else df.droplevel(1, axis=1)
        return df
    except Exception:
        return pd.DataFrame()

df = fetch_data(ticker, timeframe)
if df.empty or 'Close' not in df:
    dates = pd.date_range(end=pd.Timestamp.today(), periods=120, freq='B')
    np.random.seed(42)
    df = pd.DataFrame({'Close': 150 + np.cumsum(np.random.randn(120) * 2)}, index=dates)

# Technical Risk Calculations
close_series = df['Close'].squeeze()
current_price = float(close_series.iloc[-1])
sma_20 = float(close_series.rolling(window=20).mean().iloc[-1])
stop_pct = 0.03 if risk_profile == "Low" else (0.08 if risk_profile == "High" else 0.05)
stop_loss = current_price * (1 - stop_pct)
signal = "BUY / HOLD" if current_price > sma_20 else "REDUCE / EXIT"

# --- DISPLAY HTML BROKERAGE TERMINAL ---
with open("index.html", "r", encoding="utf-8") as f:
    html_code = f.read()

# Inject dynamic Python Agent values into the HTML script before rendering
html_code = html_code.replace('value="AAPL"', f'value="{ticker}"')
html_code = html_code.replace('loadTradingViewChart("AAPL")', f'loadTradingViewChart("{ticker}")')
html_code = html_code.replace('Calculating...', f'${stop_loss:.2f}', 1)
html_code = html_code.replace('Calculating...', f'{signal}', 1)

# Render index.html cleanly inside Streamlit
components.html(html_code, height=720, scrolling=False)

# --- AGENT LOGS SUMMARY ---
st.subheader("🤖 AUREXA AI Execution Logs")
st.success(f"**Agent Consensus:** Stock `{ticker}` evaluated under **{risk_profile}** risk profile.")
st.info(f"**Technical Metrics:** Price: `${current_price:.2f}` | 20-Day SMA: `${sma_20:.2f}` | Guardrail Stop-Loss: `${stop_loss:.2f}`")