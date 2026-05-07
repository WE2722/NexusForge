# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal

class Settings(BaseSettings):
    app_env: Literal["development", "staging", "production"] = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    log_level: str = Field(default="INFO")

    class Config:
        env_file = ".env"

settings = Settings()