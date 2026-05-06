"""
NexusForge Main Application — FastAPI entrypoint.
"""
from __future__ import annotations

import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.services.project_memory import ProjectMemory

logger = structlog.get_logger(__name__)

project_memory = ProjectMemory()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("application_startup")
    await project_memory.initialize()
    yield
    # Shutdown
    logger.info("application_shutdown")


app = FastAPI(
    title="NexusForge API",
    description="Multi-Agent Orchestration System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to NexusForge API"}
