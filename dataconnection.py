import bcrypt
import pandas as pd
from sqlalchemy import create_engine, text
from logger_config import setup_logger

logger = setup_logger("database")

DB_URL = "mysql+pymysql://root:tiger@localhost/genai"
engine = create_engine(DB_URL)


def init_system_settings() -> None:
    """Ensures the system_settings table and default kill_switch row exist."""
    create_sql = text("""
        CREATE TABLE IF NOT EXISTS system_settings (
            setting_key VARCHAR(50) PRIMARY KEY,
            is_enabled BOOLEAN NOT NULL DEFAULT FALSE,
            updated_by VARCHAR(100),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );
    """)
    seed_sql = text("""
        INSERT IGNORE INTO system_settings (setting_key, is_enabled, updated_by)
        VALUES ('kill_switch', FALSE, 'system');
    """)
    with engine.begin() as conn:
        conn.execute(create_sql)
        conn.execute(seed_sql)


def is_kill_switch_active() -> bool:
    """Returns True if the kill switch is currently ON."""
    query = text("SELECT is_enabled FROM system_settings WHERE setting_key = 'kill_switch' LIMIT 1")
    try:
        with engine.connect() as conn:
            result = conn.execute(query).fetchone()
            return bool(result[0]) if result else False
    except Exception as e:
        logger.error(f"Failed to read kill_switch state: {e}")
        return False


def set_kill_switch(enabled: bool, updated_by: str) -> None:
    """Updates the kill switch state in MySQL."""
    query = text("""
        UPDATE system_settings
        SET is_enabled = :enabled, updated_by = :updated_by
        WHERE setting_key = 'kill_switch'
    """)
    with engine.begin() as conn:
        conn.execute(query, {"enabled": enabled, "updated_by": updated_by})
    logger.warning(f"Kill switch set to {enabled} by '{updated_by}'.")


def get_app_logs(limit: int = 200) -> pd.DataFrame:
    """Fetches structured logs from `app_logs` for the power_user dashboard."""
    query = text("""
        SELECT
            id,
            JSON_UNQUOTE(JSON_EXTRACT(log_data, '$.timestamp')) AS timestamp,
            JSON_UNQUOTE(JSON_EXTRACT(log_data, '$.level')) AS level,
            JSON_UNQUOTE(JSON_EXTRACT(log_data, '$.component')) AS component,
            JSON_UNQUOTE(JSON_EXTRACT(log_data, '$.user')) AS user,
            JSON_UNQUOTE(JSON_EXTRACT(log_data, '$.message')) AS message,
            created_at
        FROM app_logs
        ORDER BY id DESC
        LIMIT :limit
    """)
    with engine.connect() as conn:
        return pd.read_sql_query(query, conn, params={"limit": limit})


def getResults(query: str) -> pd.DataFrame:
    """Executes a SELECT SQL query and returns the results as a Pandas DataFrame."""
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
    Verifies the user against the `users` table.
    Returns (True, user_type) on success, or (False, None) on failure.
    """
    query = text("SELECT password_hash, user_type FROM users WHERE user_name = :user_name LIMIT 1")
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"user_name": user_name}).fetchone()
            if not result:
                logger.warning(f"Auth failed: Username '{user_name}' not found.")
                return False, None

            stored_hash = result[0].encode("utf-8")
            user_type = result[1]
            input_bytes = plain_password.encode("utf-8")

            if bcrypt.checkpw(input_bytes, stored_hash):
                logger.info(f"User '{user_name}' ({user_type}) authenticated successfully.")
                
                return True, user_type
            else:
                logger.warning(f"Auth failed: Invalid password for '{user_name}'.")
                return False, None
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        return False, None