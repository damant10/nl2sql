import json
import bcrypt
import pandas as pd
from sqlalchemy import create_engine, text
from logger_config import setup_logger

logger = setup_logger("database")

DB_URL = "mysql+pymysql://root:tiger@localhost/genai"
engine = create_engine(DB_URL)


def getResults(query: str) -> pd.DataFrame:
    """
    Executes a SELECT SQL query and returns the results as a Pandas DataFrame.
    """
    logger.info(f"Executing SQL query: {query}")
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text(query), conn)
            logger.info(f"Execution successful. Returned {len(df)} row(s).")
            return df
    except Exception as e:
        logger.error(f"Database query execution failed: {e}")
        raise


def authenticate_user(user_name: str, plain_password: str) -> tuple[bool, str | None]:
    """
    Verifies the user against the `users` table and returns (is_authenticated, user_type).
    """
    query = text(
        "SELECT password_hash, user_type FROM users WHERE user_name = :user_name LIMIT 1"
    )
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"user_name": user_name}).fetchone()
            print(f"result is:{result}")
            if not result:
                logger.warning(f"Auth failed: Username '{user_name}' not found.")
                return False, None

            stored_hash = result[0].encode("utf-8")
            user_type = result[1]
            input_bytes = plain_password.encode("utf-8")

            if bcrypt.checkpw(input_bytes, stored_hash):
                logger.info(f"User '{user_name}' (type: {user_type}) authenticated successfully.")
                return True, user_type
            else:
                logger.warning(f"Auth failed: Invalid password for '{user_name}'.")
                return False, None
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        return False, None


def get_app_logs() -> pd.DataFrame:
    """
    Fetches all records from `app_logs` and expands the JSON `log_data` column into structured columns.
    """
    query = text("SELECT id, log_data, created_at FROM app_logs ORDER BY id DESC")
    try:
        with engine.connect() as conn:
            raw_df = pd.read_sql_query(query, conn)

        if raw_df.empty:
            return raw_df

        # Parse JSON strings (handles both JSON column dicts and LONGTEXT strings)
        parsed_logs = raw_df["log_data"].apply(
            lambda x: json.loads(x) if isinstance(x, str) else (x or {})
        )
        json_df = pd.json_normalize(parsed_logs)

        # Combine table metadata with unpacked JSON fields
        result_df = pd.concat([raw_df[["id", "created_at"]], json_df], axis=1)
        return result_df
    except Exception as e:
        logger.error(f"Failed to fetch app_logs: {e}")
        raise