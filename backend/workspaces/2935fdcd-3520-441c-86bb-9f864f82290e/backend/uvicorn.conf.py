# Uvicorn configuration
import uvicorn
from fastapi import FastAPI
from pydantic_settings import BaseSettings
from .main import app

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)