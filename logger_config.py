import json
import logging
from sqlalchemy import create_engine, text

# Database connection URL (matches your project's connection in dataconnection.py)
DB_URL = "mysql+pymysql://root:tiger@localhost/genai"


class MySQLJSONHandler(logging.Handler):
    """
    Custom logging handler that formats log records into a specific JSON structure:
    {
      "timestamp": asctime,
      "level": levelname,
      "component": "name",
      "message": message
    }
    and saves them to a MySQL table.
    """

    def __init__(self, db_url: str = DB_URL, table_name: str = "app_logs"):
        super().__init__()
        self.table_name = table_name
        self.date_format = "%Y-%m-%d %H:%M:%S"
        self.engine = create_engine(db_url, pool_recycle=3600)
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Creates the target logging table if it does not already exist."""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            log_data JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text(create_table_sql))
                conn.commit()
        except Exception as e:
            # Fallback print to stdout if table creation fails
            print(f"[ERROR] Could not initialize MySQL logging table: {e}")

    def emit(self, record: logging.LogRecord) -> None:
        try:
            # Format time as 'YYYY-MM-DD HH:MM:SS'
            record.asctime = self.formatTime(record, self.date_format)

            # Build the exact JSON schema requested
            log_payload = {
                "timestamp": record.asctime,
                "level": record.levelname,
                "component": record.name,
                "message": record.getMessage(),
            }

            json_str = json.dumps(log_payload)

            # Insert JSON string into the MySQL table
            insert_sql = text(
                f"INSERT INTO {self.table_name} (log_data) VALUES (:payload)"
            )
            with self.engine.connect() as conn:
                conn.execute(insert_sql, {"payload": json_str})
                conn.commit()

        except Exception:
            # Delegate to standard logging error handler to prevent crashing host app
            self.handleError(record)


def setup_logger(name: str = "sql_app") -> logging.Logger:
    """Configures and returns a logger connected to the MySQL JSON handler."""
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if the logger has already been initialized
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Attach custom MySQL JSON handler
        db_handler = MySQLJSONHandler()
        logger.addHandler(db_handler)

    return logger