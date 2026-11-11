import bcrypt
import pandas as pd
from sqlalchemy import create_engine, text
from logger_config import setup_logger

logger = setup_logger("database")

DB_URL = 'mysql+pymysql://root:tiger@localhost/genai'
engine = create_engine(DB_URL)

def getResults(query: str) -> pd.DataFrame:
    """
    Executes a SELECT SQL query and returns the results as a Pandas DataFrame.
    """
    logger.info(f"Executing SQL query: {query}")
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(query, conn)
            logger.info(f"Execution successful. Returned {len(df)} row(s).")
            return df
    except Exception as e:
        logger.error(f"Database query execution failed: {e}")
        raise

def authenticate_user(user_name: str, plain_password: str) -> bool:
    """
    Verifies the user against the `users` table:
    1. Fetches the hashed password for the given username.
    2. Compares the plain-text password with the stored bcrypt hash.
    """
    query = text("SELECT password_hash FROM users WHERE user_name = :user_name LIMIT 1")
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"user_name": user_name}).fetchone()
            if not result:
                logger.warning(f"Auth failed: Username '{user_name}' not found.")
                return False

            stored_hash = result[0].encode("utf-8")  # Ensure the stored hash is in bytes
            input_bytes = plain_password.encode("utf-8")
            print(f"Stored hash: {stored_hash}, Input password bytes: {input_bytes}")  # Debugging line

            if bcrypt.checkpw(input_bytes, stored_hash):
                logger.info(f"User '{user_name}' authenticated successfully.")
                return True
            else:
                logger.warning(f"Auth failed: Invalid password for '{user_name}'.")
                return False
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        return False

if __name__ == "__main__":
    query = "SELECT * FROM customer"
    try:
        t = getResults(query)
        logger.info(f"Standalone run completed successfully with {len(t)} records.")
    except Exception as err:
        logger.error(f"Standalone test failed: {err}")