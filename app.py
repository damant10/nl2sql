import streamlit as st
from dataconnection import (
    getResults,
    authenticate_user,
    init_system_settings,
    is_kill_switch_active,
    set_kill_switch,
    get_app_logs,
)
from nlp2sql import NLPtoSQl, is_relevant_query, is_safe_select_query
from email_service import send_invalid_query_alert
from logger_config import setup_logger, set_log_user

logger = setup_logger("streamlit_app")
init_system_settings()

st.title("SQL Query Executor")

# --- Session State Initialization ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "user_type" not in st.session_state:
    st.session_state.user_type = None

set_log_user(st.session_state.current_user)

# --- User Authentication Section ---
st.subheader("User Verification")
col1, col2 = st.columns(2)
with col1:
    user_name_input = st.text_input("Username")
with col2:
    password_input = st.text_input("Password (Unhashed)", type="password")

submit = st.button("Enter")

if submit:
    clean_username = user_name_input.strip()
    if not clean_username or not password_input:
        st.warning("Please provide both username and password.")
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.user_type = None
        set_log_user(None)
    else:
        set_log_user(clean_username)
        is_valid, user_type = authenticate_user(clean_username, password_input)
        if is_valid:
            st.session_state.authenticated = True
            st.session_state.current_user = clean_username
            st.session_state.user_type = user_type
            st.success(f"Welcome, {st.session_state.current_user}! Access granted.")
        else:
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.user_type = None
            set_log_user(None)
            st.error("Invalid username or password. Please retry.")

st.divider()

# --- Role-Based Views (Activated only when authenticated) ---
if st.session_state.authenticated:
    kill_switch_active = is_kill_switch_active()
    is_power_user = st.session_state.user_type == "power_user"

    if is_power_user:
        # =========================================================
        # POWER USER VIEW: Kill Switch + Application Logs Viewer ONLY
        # =========================================================
        st.subheader("🛡️ Power User Dashboard")

        btn_label = (
            "🟢 Disable Kill Switch (Enable User Submissions)"
            if kill_switch_active
            else "🔴 Activate Kill Switch (Disable User Submissions)"
        )
        if st.button(btn_label):
            set_kill_switch(not kill_switch_active, st.session_state.current_user)
            st.rerun()

        if kill_switch_active:
            st.warning("Kill switch is currently ACTIVE. User query submissions are disabled.")
        else:
            st.info("Kill switch is OFF. Users can submit queries normally.")

        st.divider()

        st.subheader("📋 Application Logs (`app_logs`)")
        log_col1, log_col2 = st.columns([3, 1])
        with log_col1:
            selected_levels = st.multiselect(
                "Filter by Log Level",
                options=["INFO", "WARNING", "ALERT", "ERROR"],
                default=["INFO", "WARNING", "ALERT", "ERROR"],
                key="power_user_log_levels_v2",
            )
        with log_col2:
            st.write("")
            st.write("")
            if st.button("🔄 Refresh Logs"):
                st.rerun()

        try:
            logs_df = get_app_logs(limit=200)
            if not logs_df.empty:
                logs_df["level"] = logs_df["level"].astype(str).str.strip().str.upper()
                if selected_levels:
                    logs_df = logs_df[logs_df["level"].isin(selected_levels)]
            st.dataframe(logs_df, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to load logs from `app_logs`: {e}")

    else:
        # =========================================================
        # STANDARD USER VIEW: Natural Language Query Executor ONLY
        # =========================================================
        if kill_switch_active:
            st.error("🚫 Query submissions are temporarily disabled by an administrator.")

        user_input = st.text_area("Enter your query in English language here")

        if st.button("Execute Query", disabled=kill_switch_active):
            # Re-check DB on click in case power_user toggled the switch while this page was idle
            if is_kill_switch_active():
                st.error("🚫 Query submissions were just disabled by an administrator.")
                st.stop()

            clean_input = user_input.strip()
            if not clean_input:
                st.warning("Please enter a question.")
            else:
                logger.info(f"New user submission: '{clean_input}'")

                with st.spinner("Checking query scope..."):
                    valid = is_relevant_query(clean_input)

                if not valid:
                    st.error("These questions are not in our scope.")
                    try:
                        send_invalid_query_alert(clean_input)
                    except Exception as e:
                        logger.error(f"Error triggering email alert: {e}")
                else:
                    with st.spinner("Generating SQL query..."):
                        try:
                            sql_query, reason = NLPtoSQl(clean_input)
                            st.write("Generated SQL Query:")
                            st.code(sql_query, language="sql")
                            st.write(f"Logic of output is: {reason}")

                            if not is_safe_select_query(sql_query):
                                st.error(
                                    "Can't perform the required query: Disallowed statement or dangerous operation detected."
                                )
                            else:
                                df = getResults(sql_query)
                                st.write("Query Results:")
                                st.dataframe(df)

                        except Exception as e:
                            logger.exception(f"Unhandled UI error: {e}")
                            st.error(f"Execution Error: {e}")
else:
    st.info("🔒 Enter your credentials and verify above to unlock the application.")