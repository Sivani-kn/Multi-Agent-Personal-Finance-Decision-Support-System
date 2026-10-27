
from datetime import datetime

import pandas as pd
import streamlit as st


def show_analysis(dashboard_page, ticker, risk_profile, timeframe, analysis):
    """Render the Agent Analysis page using shared application data."""

    # Retrieve calculated values passed by app.py.
    current_price = analysis["current_price"]
    sma_20 = analysis["sma_20"]
    rsi = analysis["rsi"]
    stop_loss = analysis["stop_loss"]

    trend_agent = analysis["trend_agent"]
    trend_reason = analysis["trend_reason"]
    momentum_agent = analysis["momentum_agent"]
    momentum_reason = analysis["momentum_reason"]
    risk_agent = analysis["risk_agent"]
    risk_reason = analysis["risk_reason"]
    signal = analysis["signal"]
    using_synthetic_data = analysis["using_synthetic_data"]

    # Initialize decision history once per Streamlit session.
    if "aurexa_decision_history" not in st.session_state:
        st.session_state.aurexa_decision_history = []

    # Back navigation.
    st.page_link(
        dashboard_page,
        label="← Back to Trading Dashboard",
        icon=":material/dashboard:",
    )

    st.title("🤖 AUREXA AI — Agent Analysis")

    st.caption(
        f"Ticker: {ticker} | "
        f"Risk profile: {risk_profile} | "
        f"Lookback: {timeframe}"
    )

    st.divider()

    if using_synthetic_data:
        st.warning(
            "Live stock data could not be retrieved. Synthetic fallback "
            "prices are being shown. Do not use this run for investment "
            "decisions."
        )

    # --------------------------------------------------------
    # TECHNICAL OVERVIEW
    # --------------------------------------------------------
    st.subheader("Technical Overview")

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Latest Close", f"${current_price:,.2f}")
    m2.metric("SMA 20", f"${sma_20:,.2f}")
    m3.metric("RSI (14)", f"{rsi:.1f}")
    m4.metric("Stop-Loss Guide", f"${stop_loss:,.2f}")

    # --------------------------------------------------------
    # AGENT ASSESSMENTS
    # --------------------------------------------------------
    st.subheader("Agent Assessments")

    agent_table = pd.DataFrame([
        {
            "Agent": "Trend Agent",
            "Assessment": trend_agent,
            "Reason": trend_reason,
        },
        {
            "Agent": "Momentum Agent",
            "Assessment": momentum_agent,
            "Reason": momentum_reason,
        },
        {
            "Agent": "Risk Agent",
            "Assessment": risk_agent,
            "Reason": risk_reason,
        },
    ])

    st.dataframe(
        agent_table,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # COMBINED RECOMMENDATION
    # --------------------------------------------------------
    st.subheader("Combined Recommendation")

    signal_display = {
        "BUY": st.success,
        "SELL": st.error,
        "HOLD": st.warning,
    }

    signal_display[signal](
        f"**Combined recommendation: {signal}**"
    )

    st.caption(
        "These are explainable, rule-based decision-support modules, "
        "not independent trained AI models. Recommendations do not "
        "guarantee future performance and are not personalized "
        "financial advice."
    )

    # --------------------------------------------------------
    # HUMAN-IN-THE-LOOP REVIEW
    # --------------------------------------------------------
    st.divider()
    st.subheader("🧑‍⚖️ Human-in-the-Loop Review")

    st.write(
        f"Proposed action for **{ticker}**: **{signal}**"
    )

    human_action = st.selectbox(
        "Your decision",
        [
            "Approve recommendation",
            "Reject recommendation",
            "Modify recommendation",
        ],
        key="aurexa_human_action",
    )

    modified_action = signal

    if human_action == "Modify recommendation":
        modified_action = st.selectbox(
            "Choose the action to record",
            ["BUY", "SELL", "HOLD"],
            index=["BUY", "SELL", "HOLD"].index(signal),
            key="aurexa_modified_action",
        )

    reviewer_note = st.text_area(
        "Review note (optional)",
        placeholder=(
            "Why are you approving, rejecting, "
            "or modifying this recommendation?"
        ),
        key="aurexa_reviewer_note",
    )

    if st.button("Record Human Decision", type="primary"):

        if human_action == "Approve recommendation":
            recorded_decision = f"APPROVED: {signal}"

        elif human_action == "Reject recommendation":
            recorded_decision = f"REJECTED: {signal}"

        else:
            recorded_decision = f"MODIFIED TO: {modified_action}"

        st.session_state.aurexa_decision_history.append({
            "Timestamp": datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            "Ticker": ticker,
            "Recommendation": signal,
            "Human decision": recorded_decision,
            "Reviewer note": reviewer_note.strip(),
            "Risk profile": risk_profile,
            "Latest close": round(current_price, 4),
            "Stop-loss guide": round(stop_loss, 4),
        })

        st.success(
            "Human decision recorded in this session. "
            "No trade was executed."
        )

    # --------------------------------------------------------
    # DECISION HISTORY
    # --------------------------------------------------------
    st.divider()
    st.subheader("📋 Decision History")

    history = pd.DataFrame(
        st.session_state.aurexa_decision_history
    )

    if history.empty:
        st.info("No human decisions recorded yet.")

    else:
        st.dataframe(
            history,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download Decision History as CSV",
            data=history.to_csv(index=False).encode("utf-8"),
            file_name="aurexa_decision_history.csv",
            mime="text/csv",
        )

    # --------------------------------------------------------
    # EXECUTION LOG SUMMARY
    # --------------------------------------------------------
    st.divider()
    st.subheader("🤖 AUREXA AI Execution Logs")

    st.success(
        f"**Agent Consensus:** Stock `{ticker}` evaluated "
        f"under **{risk_profile}** risk profile."
    )

    st.info(
        f"**Technical Metrics:** Price: `${current_price:.2f}` | "
        f"20-Day SMA: `${sma_20:.2f}` | "
        f"Guardrail Stop-Loss: `${stop_loss:.2f}`"
    )
