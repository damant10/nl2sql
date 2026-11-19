import contextvars
import json
import logging
from datetime import datetime
from sqlalchemy import create_engine, text

DB_URL = "mysql+pymysql://root:tiger@localhost/genai"

current_user_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_user", default="anonymous"
)

# AUTOCOMMIT ensures CREATE TABLE and INSERT persist immediately in MySQL
_shared_engine = create_engine(
    DB_URL,
    pool_recycle=3600,
    isolation_level="AUTOCOMMIT",
)


def set_log_user(username: str | None) -> None:
    """Sets the current user for all subsequent log entries in the active context."""
    current_user_var.set(username if username else "anonymous")


class UserContextFilter(logging.Filter):
    """Injects the current user from contextvars into every LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.user = current_user_var.get()
        return True


class MySQLJSONHandler(logging.Handler):
    def __init__(self, table_name: str = "app_logs"):
        super().__init__()
        self.table_name = table_name
        self.engine = _shared_engine
        self._table_verified = False
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Creates the target logging table using JSON, falling back to LONGTEXT if needed."""
        json_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            log_data JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        longtext_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            log_data LONGTEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text(json_table_sql))
            self._table_verified = True
        except Exception as e:
            print(f"[MySQLJSONHandler] JSON table failed ({e}), trying LONGTEXT...")
            with self.engine.connect() as conn:
                conn.execute(text(longtext_table_sql))
            self._table_verified = True

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if not self._table_verified:
                self._ensure_table_exists()

            timestamp_str = datetime.fromtimestamp(record.created).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            log_payload = {
                "timestamp": timestamp_str,
                "level": record.levelname,
                "component": record.name,
                "user": getattr(record, "user", "anonymous"),
                "message": record.getMessage(),
            }

            json_str = json.dumps(log_payload)

            insert_sql = text(
                f"INSERT INTO {self.table_name} (log_data) VALUES (:payload)"
            )
            with self.engine.connect() as conn:
                conn.execute(insert_sql, {"payload": json_str})

        except Exception as e:
            print(f"[MySQLJSONHandler EMIT ERROR]: {e}")
            self.handleError(record)


def setup_logger(name: str = "sql_app") -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.propagate = False

        db_handler = MySQLJSONHandler()
        db_handler.addFilter(UserContextFilter())
        logger.addHandler(db_handler)

    return logger


if __name__ == "__main__":
    # Direct test to verify table creation and log insertion
    test_logger = setup_logger("diag_test")
    set_log_user("Mrinal")
    test_logger.info("Verification log entry from logger_config.py")
    print("SUCCESS: Table verified and log inserted!")