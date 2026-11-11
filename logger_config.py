import logging

def setup_logger(name: str = "sql_app") -> logging.Logger:
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if the logger is already initialized
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # File handler directing output to logs.txt
        file_handler = logging.FileHandler("logs.txt", mode="a", encoding="utf-8")
        
        # Log entry layout: Date/Time | Severity | Module Name | Message
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] (%(name)s): %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger