# app/core/logging.py
import logging
from loguru import logger
from core.config import settings

def setup_logging():
    """Configure structured logging for the application."""
    logger.remove()
    logger.add(
        sink="logs/app.log",
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}",
        rotation="10 MB",
        compression="zip",
    )
    logging.getLogger("uvicorn").handlers.clear()
    logging.getLogger("uvicorn").addHandler(logging.StreamHandler())
    logging.getLogger("uvicorn").setLevel(settings.log_level)

    return logger

logger = setup_logging()