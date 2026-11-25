import streamlit as st
from dataconnection import getResults, authenticate_user, get_app_logs
from nlp2sql import NLPtoSQl, is_relevant_query, is_safe_select_query
from email_service import send_invalid_query_alert
from logger_config import setup_logger, set_log_user

logger = setup_logger("streamlit_app")

st.title("SQL Query Executor")

# --- Session State Initialization ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "user_type" not in st.session_state:
    st.session_state.user_type = None

# Sync current_user into the logging context on every Streamlit rerun
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

# --- Role-Based View Routing ---
if st.session_state.authenticated:
    if st.session_state.user_type == "power_user":
        st.subheader("Application Logs (`app_logs`)")

        if st.button("Refresh Logs"):
            st.rerun()

        try:
            logs_df = get_app_logs()
            if logs_df.empty:
                st.info("No logs found in the `app_logs` table.")
            else:
                # Optional filters for quick log inspection
                filter_col1, filter_col2 = st.columns(2)
                with filter_col1:
                    if "level" in logs_df.columns:
                        levels = ["ALL"] + sorted(logs_df["level"].dropna().unique().tolist())
                        selected_level = st.selectbox("Filter by Log Level", levels)
                        if selected_level != "ALL":
                            logs_df = logs_df[logs_df["level"] == selected_level]
                with filter_col2:
                    if "user" in logs_df.columns:
                        users = ["ALL"] + sorted(logs_df["user"].dropna().unique().tolist())
                        selected_user = st.selectbox("Filter by User", users)
                        if selected_user != "ALL":
                            logs_df = logs_df[logs_df["user"] == selected_user]

                st.dataframe(logs_df, use_container_width=True, hide_index=True)
        except Exception as e:
            logger.exception(f"Error loading app_logs for power_user: {e}")
            st.error(f"Failed to load logs: {e}")

    else:
        # --- Default View: Natural Language to SQL Query Tool ---
        user_input = st.text_area("Enter your query in English language here")

        if st.button("Execute Query"):
            clean_input = user_input.strip()
            if not clean_input:
                st.warning("Please enter a question.")
            else:
                logger.info(f"New user submission: '{clean_input}'")

                # Input Guardrail Check
                with st.spinner("Checking query scope..."):
                    valid = is_relevant_query(clean_input)

                if not valid:
                    st.error("These questions are not in our scope.")
                    try:
                        user_name = st.session_state.current_user
                        send_invalid_query_alert(clean_input,user_name)
                    except Exception as e:
                        logger.error(f"Error triggering email alert: {e}")
                else:
                    with st.spinner("Generating SQL query..."):
                        try:
                            sql_query, reason = NLPtoSQl(clean_input)
                            st.write("Generated SQL Query:")
                            st.code(sql_query, language="sql")
                            st.write(f"Logic of output is: {reason}")

                            # Output Guardrail Check
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
    st.info("🔒 Enter your credentials and verify above to unlock the Natural Language Query tool.")
