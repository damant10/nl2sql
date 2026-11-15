import streamlit as st
from dataconnection import getResults, authenticate_user
from nlp2sql import NLPtoSQl, is_relevant_query, is_safe_select_query
from email_service import send_invalid_query_alert
from logger_config import setup_logger

logger = setup_logger("streamlit_app")

st.title("SQL Query Executor")

# --- Session State Initialization ---
#If the user has not been authenticated yet, consider them logged out."authenticated" is the name of a variable stored in the session.
#variable authenticated Checks whether the user is logged in
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
#No user is currently logged in, so we don't have any user information yet.
#variable current_user Stores the currently logged-in user's information
if "current_user" not in st.session_state:
    st.session_state.current_user = None

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
    else:
        is_valid = authenticate_user(clean_username, password_input)
        if is_valid:
            st.session_state.authenticated = True
            st.session_state.current_user = clean_username
            st.success(f"Welcome, {st.session_state.current_user}! Access granted.")
        else:
            st.session_state.authenticated = False
            st.error("Invalid username or password. Please retry.")

st.divider()

# --- Query Section (Activated only when authenticated) ---
if st.session_state.authenticated:
    user_input = st.text_area("Enter your query in English language here")

    if st.button("Execute Query"):
        clean_input = user_input.strip()
        if not clean_input:
            st.warning("Please enter a question.")
        else:
            logger.info(f"New user submission by {st.session_state.current_user}: '{clean_input}'")

            # Input Guardrail Check
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
                        sql_query,reason = NLPtoSQl(clean_input)
                        st.write("Generated SQL Query:")
                        st.code(sql_query, language='sql')
                        st.write(f"Logic of output is: {reason}")

                        # Output Guardrail Check
                        if not is_safe_select_query(sql_query):
                            st.error("Can't perform the required query: Disallowed statement or dangerous operation detected.")
                        else:
                            df = getResults(sql_query)
                            st.write("Query Results:")
                            st.dataframe(df)

                    except Exception as e:
                        logger.exception(f"Unhandled UI error: {e}")
                        st.error(f"Execution Error: {e}")
else:
    st.info("🔒 Enter your credentials and verify above to unlock the Natural Language Query tool.")