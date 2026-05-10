import logging
from logging.config import dictConfig
from config import settings

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": settings.LOG_FORMAT,
            "use_colors": True,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": settings.LOG_FORMAT,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "currency_converter": {
            "handlers": ["default"],
            "level": settings.LOG_LEVEL,
        },
        "uvicorn.error": {
            "level": settings.LOG_LEVEL,
            "handlers": ["default"],
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["access"],
            "level": settings.LOG_LEVEL,
            "propagate": False,
        },
    },
}

def configure_logging():
    dictConfig(LOGGING_CONFIG)