# app/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from custom_logger import logger
from api.v1.routers import v1_router

app = FastAPI(
    title="Todo List API",
    description="A simple Todo List API built with FastAPI",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(v1_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Host: {settings.app_host}")
    logger.info(f"Port: {settings.app_port}")

@app.get("/")
async def root():
    return {
        "message": "Todo List API",
        "version": "1.0.0",
        "docs": "/api/docs",
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
        log_config=None,
    )