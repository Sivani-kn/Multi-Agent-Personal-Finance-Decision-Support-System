
import re
from datetime import datetime
from analysis_agent import show_analysis

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import streamlit.components.v1 as components


# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="AUREXA AI - Decision & Brokerage Terminal",
    page_icon="📈",
    layout="wide",
)


# ============================================================
# SIDEBAR CONTROLS
# ============================================================
st.sidebar.header("🤖 Agentic Control Panel")

ticker = st.sidebar.text_input(
    "Stock Ticker",
    value="AAPL",
).upper().strip()

risk_profile = st.sidebar.selectbox(
    "Risk Profile",
    ["Moderate", "Low", "High"],
)

timeframe = st.sidebar.selectbox(
    "Lookback Period",
    ["3mo", "6mo", "1y"],
    index=1,
)

if not ticker or not re.fullmatch(r"[A-Z0-9.^=_-]{1,20}", ticker):
    st.error("Enter a valid stock ticker, such as AAPL or MSFT.")
    st.stop()


# ============================================================
# STOCK DATA FETCHING
# ============================================================
@st.cache_data(ttl=3600)
def fetch_data(symbol, period="6mo"):
    try:
        data = yf.download(
            symbol,
            period=period,
            progress=False,
            auto_adjust=False,
        )

        if isinstance(data.columns, pd.MultiIndex):
            if symbol in data.columns.get_level_values(-1):
                data = data.xs(symbol, axis=1, level=-1)
            elif symbol in data.columns.get_level_values(0):
                data = data.xs(symbol, axis=1, level=0)
            else:
                data.columns = data.columns.get_level_values(0)

        return data

    except Exception:
        return pd.DataFrame()


def calculate_analysis(symbol, period, selected_risk):
    """Fetch stock data and calculate explainable agent assessments."""

    df = fetch_data(symbol, period)
    using_synthetic_data = False

    # Clearly identify fallback data if live data is unavailable.
    if df.empty or "Close" not in df.columns:
        dates = pd.date_range(
            end=pd.Timestamp.today(),
            periods=120,
            freq="B",
        )

        np.random.seed(42)

        df = pd.DataFrame(
            {
                "Close": 150 + np.cumsum(
                    np.random.randn(120) * 2
                )
            },
            index=dates,
        )

        using_synthetic_data = True

    close_series = pd.to_numeric(
        df["Close"].squeeze(),
        errors="coerce",
    ).dropna()

    if len(close_series) < 2:
        return None

    # --------------------------------------------------------
    # TECHNICAL INDICATORS
    # --------------------------------------------------------
    current_price = float(close_series.iloc[-1])

    sma_20_series = close_series.rolling(window=20).mean()
    sma_50_series = close_series.rolling(window=50).mean()

    sma_20 = (
        float(sma_20_series.iloc[-1])
        if pd.notna(sma_20_series.iloc[-1])
        else current_price
    )

    sma_50 = (
        float(sma_50_series.iloc[-1])
        if pd.notna(sma_50_series.iloc[-1])
        else sma_20
    )

    delta = close_series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean().replace(0, np.nan)

    rs = avg_gain / avg_loss
    rsi_series = 100 - (100 / (1 + rs))

    rsi = (
        float(rsi_series.iloc[-1])
        if pd.notna(rsi_series.iloc[-1])
        else 50.0
    )

    returns = close_series.pct_change().dropna()

    volatility_pct = (
        float(returns.tail(20).std() * np.sqrt(252) * 100)
        if len(returns) >= 2
        else 0.0
    )

    stop_pct = (
        0.03 if selected_risk == "Low"
        else 0.08 if selected_risk == "High"
        else 0.05
    )

    stop_loss = current_price * (1 - stop_pct)

    # --------------------------------------------------------
    # TREND AGENT
    # --------------------------------------------------------
    if current_price > sma_20 and sma_20 >= sma_50:
        trend_agent = "BUY"
        trend_reason = (
            "Price is above SMA 20 and SMA 20 is at or above SMA 50."
        )

    elif current_price < sma_20 and sma_20 <= sma_50:
        trend_agent = "SELL"
        trend_reason = (
            "Price is below SMA 20 and SMA 20 is at or below SMA 50."
        )

    else:
        trend_agent = "HOLD"
        trend_reason = (
            "Moving averages show a mixed or transitional trend."
        )

    # --------------------------------------------------------
    # MOMENTUM AGENT
    # --------------------------------------------------------
    if rsi < 30:
        momentum_agent = "BUY"
        momentum_reason = (
            f"RSI is {rsi:.1f}, in a potentially oversold range."
        )

    elif rsi > 70:
        momentum_agent = "SELL"
        momentum_reason = (
            f"RSI is {rsi:.1f}, in a potentially overbought range."
        )

    else:
        recent_change = (
            (
                float(close_series.iloc[-1])
                / float(close_series.iloc[-6]) - 1
            ) * 100
            if len(close_series) >= 6
            else 0.0
        )

        if recent_change > 1:
            momentum_agent = "BUY"
            momentum_reason = (
                "Five-session price momentum is positive "
                f"({recent_change:.2f}%)."
            )

        elif recent_change < -1:
            momentum_agent = "SELL"
            momentum_reason = (
                "Five-session price momentum is negative "
                f"({recent_change:.2f}%)."
            )

        else:
            momentum_agent = "HOLD"
            momentum_reason = (
                f"RSI is neutral ({rsi:.1f}) and "
                "recent momentum is limited."
            )

    # --------------------------------------------------------
    # RISK AGENT
    # --------------------------------------------------------
    if volatility_pct >= 60:
        risk_agent = "HOLD"
        risk_reason = (
            "Annualized 20-session volatility is elevated "
            f"({volatility_pct:.1f}%). The risk agent recommends caution."
        )

    else:
        risk_agent = "HOLD"
        risk_reason = (
            f"Annualized 20-session volatility is {volatility_pct:.1f}%. "
            f"Apply the {selected_risk.lower()} risk guardrail."
        )

    # --------------------------------------------------------
    # AGENT CONSENSUS
    # --------------------------------------------------------
    scores = {
        "BUY": 1,
        "HOLD": 0,
        "SELL": -1,
    }

    consensus_score = (
        scores[trend_agent]
        + scores[momentum_agent]
        + scores[risk_agent]
    )

    if volatility_pct >= 60:
        signal = "HOLD"
    elif consensus_score >= 2:
        signal = "BUY"
    elif consensus_score <= -2:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "df": df,
        "close_series": close_series,
        "using_synthetic_data": using_synthetic_data,
        "current_price": current_price,
        "sma_20": sma_20,
        "sma_50": sma_50,
        "rsi": rsi,
        "volatility_pct": volatility_pct,
        "stop_loss": stop_loss,
        "trend_agent": trend_agent,
        "trend_reason": trend_reason,
        "momentum_agent": momentum_agent,
        "momentum_reason": momentum_reason,
        "risk_agent": risk_agent,
        "risk_reason": risk_reason,
        "signal": signal,
    }


analysis = calculate_analysis(ticker, timeframe, risk_profile)

if analysis is None:
    st.error(
        "Not enough valid price data to calculate a recommendation."
    )
    st.stop()


# Make the calculated values available to both page functions.
current_price = analysis["current_price"]
sma_20 = analysis["sma_20"]
sma_50 = analysis["sma_50"]
rsi = analysis["rsi"]
volatility_pct = analysis["volatility_pct"]
stop_loss = analysis["stop_loss"]

trend_agent = analysis["trend_agent"]
trend_reason = analysis["trend_reason"]
momentum_agent = analysis["momentum_agent"]
momentum_reason = analysis["momentum_reason"]
risk_agent = analysis["risk_agent"]
risk_reason = analysis["risk_reason"]
signal = analysis["signal"]
using_synthetic_data = analysis["using_synthetic_data"]


# ============================================================
# SHARED SESSION STATE
# ============================================================
if "aurexa_decision_history" not in st.session_state:
    st.session_state.aurexa_decision_history = []


# ============================================================
# PAGE 1: ORIGINAL TRADING DASHBOARD
# ============================================================
def show_dashboard():

    st.title("AUREXA AI")
    st.caption("Agentic Finance & Brokerage Dashboard")

    # Native Streamlit navigation: no iframe JavaScript required.
    st.page_link(
        analysis_page,
        label="🤖 Agent's Analysis",
        icon=":material/analytics:",
    )

    if using_synthetic_data:
        st.warning(
            "Live stock data could not be retrieved. Synthetic fallback "
            "prices are being shown. Do not use this run for investment "
            "decisions."
        )

    try:
        with open("index.html", "r", encoding="utf-8") as html_file:
            html_code = html_file.read()

    except FileNotFoundError:
        st.error(
            "Could not find index.html. Keep it in the same folder "
            "as aurexa_app_updated.py."
        )
        st.stop()

    # Update ticker references in the in-memory HTML only.
    html_code = html_code.replace(
        'value="AAPL"',
        f'value="{ticker}"',
    )

    html_code = html_code.replace(
        'loadTradingViewChart("AAPL")',
        f'loadTradingViewChart("{ticker}")',
    )

    # Update the original dashboard's first two agent placeholders.
    html_code = html_code.replace(
        "Calculating...",
        f"${stop_loss:.2f}",
        1,
    )

    html_code = html_code.replace(
        "Calculating...",
        signal,
        1,
    )

    # Stabilize the existing chart container height.
    html_code = html_code.replace(
        "h-[calc(100vh-61px)]",
        "h-[780px] min-h-[780px]",
    )

    # Preserve the existing HTML dashboard.
    components.html(
        html_code,
        height=850,
        scrolling=True,
    )

# ============================================================
# NATIVE STREAMLIT MULTIPAGE NAVIGATION
# ============================================================

dashboard_page = st.Page(
    show_dashboard,
    title="Trading Dashboard",
    icon=":material/dashboard:",
    default=True,
)

analysis_page = st.Page(
    lambda: show_analysis(
        dashboard_page,
        ticker,
        risk_profile,
        timeframe,
        analysis,
    ),
    title="Agent's Analysis",
    icon=":material/analytics:",
)

navigation = st.navigation([
    dashboard_page,
    analysis_page,
])

navigation.run()



