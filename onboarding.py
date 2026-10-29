import streamlit as st


RISK_OPTIONS = {
    "Low": "Prioritizes capital preservation and lower volatility.",
    "Moderate": "Accepts some fluctuations for potential growth.",
    "High": (
        "Accepts substantial fluctuations and the possibility of "
        "significant losses."
    ),
}

EXPERIENCE_OPTIONS = {
    "Beginner": "New to investing or still building foundational knowledge.",
    "Intermediate": "Has some investing experience and understands common concepts.",
    "Experienced": "Comfortable evaluating investments and managing a portfolio.",
}

SECTOR_OPTIONS = [
    "Information Technology",
    "Banking and Financial Services",
    "Healthcare and Pharmaceuticals",
    "Energy",
    "Consumer Goods",
    "Automobile",
    "Telecommunications",
    "No preference / open to exploring different sectors",
]


def _show_option_descriptions(options):
    for label, description in options.items():
        st.caption(f"**{label}:** {description}")


def _show_profile_summary(profile):
    sectors = ", ".join(profile["preferred_sectors"])
    st.success("Your investment profile has been saved.")
    st.info(
        f"Budget: ₹{profile['budget_amount']:,.2f} "
        f"({profile['budget_type']}) · "
        f"Risk: {profile['risk_tolerance']} · "
        f"Goal: {profile['investment_goal']} · "
        f"Experience: {profile['experience_level']} · "
        f"Horizon: {profile['time_horizon']} · "
        f"Sectors: {sectors}"
    )


def show_onboarding(dashboard_page):
    """Render the session-only customer investment profile form."""

    st.title("Personalize Your Investment Profile")
    st.caption(
        "Tell AUREXA about your investing preferences so your workspace "
        "can be ready for future personalization."
    )

    saved_profile = st.session_state.get("aurexa_investment_profile")
    if saved_profile:
        st.subheader("Saved profile")
        _show_profile_summary(saved_profile)
        if st.button("Edit investment profile"):
            st.session_state.aurexa_edit_profile = True
            st.rerun()

        if not st.session_state.get("aurexa_edit_profile", False):
            st.page_link(
                dashboard_page,
                label="Continue to Trading Dashboard",
                icon=":material/dashboard:",
            )
            return

        st.divider()
        st.subheader("Edit your preferences")

    with st.form("investment_profile_form"):
        st.subheader("Investment budget")
        st.caption(
            "Enter the amount you intend to invest, not your total savings."
        )
        budget_amount = st.number_input(
            "Amount to invest (₹)",
            min_value=0.0,
            value=(
                float(saved_profile["budget_amount"])
                if saved_profile
                else 0.0
            ),
            step=1000.0,
            format="%.2f",
        )
        budget_type = st.radio(
            "Budget type",
            ["One-time investment", "Monthly contribution"],
            index=(
                ["One-time investment", "Monthly contribution"].index(
                    saved_profile["budget_type"]
                )
                if saved_profile
                else 0
            ),
            horizontal=True,
        )

        st.subheader("Risk tolerance")
        risk_tolerance = st.radio(
            "Choose the description that best fits you",
            list(RISK_OPTIONS),
            index=(
                list(RISK_OPTIONS).index(saved_profile["risk_tolerance"])
                if saved_profile
                else None
            ),
        )
        _show_option_descriptions(RISK_OPTIONS)

        st.subheader("Investment goal")
        investment_goal = st.selectbox(
            "What are you investing for?",
            [
                "Long-term wealth creation",
                "Short-term financial goal",
                "Dividend or income-oriented investing",
                "Learning about the stock market",
            ],
            index=(
                [
                    "Long-term wealth creation",
                    "Short-term financial goal",
                    "Dividend or income-oriented investing",
                    "Learning about the stock market",
                ].index(saved_profile["investment_goal"])
                if saved_profile
                else None
            ),
            placeholder="Select an investment goal",
        )

        st.subheader("Investment experience")
        experience_level = st.radio(
            "How would you describe your experience?",
            list(EXPERIENCE_OPTIONS),
            index=(
                list(EXPERIENCE_OPTIONS).index(saved_profile["experience_level"])
                if saved_profile
                else None
            ),
        )
        _show_option_descriptions(EXPERIENCE_OPTIONS)

        st.subheader("Investment time horizon")
        time_horizon = st.selectbox(
            "When might you need this money?",
            ["Less than 1 year", "1–3 years", "3–5 years", "More than 5 years"],
            index=(
                [
                    "Less than 1 year",
                    "1–3 years",
                    "3–5 years",
                    "More than 5 years",
                ].index(saved_profile["time_horizon"])
                if saved_profile
                else None
            ),
            placeholder="Select a time horizon",
        )

        st.subheader("Preferred sectors")
        preferred_sectors = st.multiselect(
            "Select one or more sectors",
            SECTOR_OPTIONS,
            default=(
                saved_profile["preferred_sectors"] if saved_profile else []
            ),
            placeholder="Choose sectors or select no preference",
        )

        submitted = st.form_submit_button(
            "Save Profile & Continue to Dashboard",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    errors = []
    if budget_amount <= 0:
        errors.append("Enter a positive investment amount.")
    if risk_tolerance is None:
        errors.append("Choose a risk tolerance.")
    if investment_goal is None:
        errors.append("Choose an investment goal.")
    if experience_level is None:
        errors.append("Choose your investment experience.")
    if time_horizon is None:
        errors.append("Choose an investment time horizon.")
    if not preferred_sectors:
        errors.append("Choose at least one preferred sector or no preference.")

    if errors:
        for error in errors:
            st.error(error)
        return

    profile = {
        "budget_amount": float(budget_amount),
        "budget_type": budget_type,
        "risk_tolerance": risk_tolerance,
        "investment_goal": investment_goal,
        "experience_level": experience_level,
        "time_horizon": time_horizon,
        "preferred_sectors": preferred_sectors,
    }
    st.session_state.aurexa_investment_profile = profile
    st.session_state.aurexa_profile_saved_message = True
    st.session_state.aurexa_edit_profile = False
    st.switch_page(dashboard_page)
