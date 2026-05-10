import os
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Currency Converter API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Currency rates (fixed for EUR, USD, MAD)
    FIXED_RATES: dict = {
        "EUR": 1.0,
        "USD": 1.07,  # Example: 1 EUR = 1.07 USD
        "MAD": 10.5   # Example: 1 EUR = 10.5 MAD
    }

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()