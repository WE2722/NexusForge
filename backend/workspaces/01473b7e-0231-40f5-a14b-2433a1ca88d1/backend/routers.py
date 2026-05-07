# app/api/v1/routers.py
from fastapi import APIRouter
from api.v1.endpoints import tasks, health

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(tasks.router)
v1_router.include_router(health.router)