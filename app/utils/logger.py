import logging
from app.config import LOG_LEVEL, LOG_PATH
from logging.handlers import RotatingFileHandler
from pathlib import Path


def create_logger(name: str) -> logging.Logger:
    log_file_path = Path(LOG_PATH)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # Create a file handler
    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=1024 * 1024 * 10, backupCount=10
    )
    file_handler.setLevel(getattr(logging, LOG_LEVEL))

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL))

    # Create a formatter and attach it to the handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
