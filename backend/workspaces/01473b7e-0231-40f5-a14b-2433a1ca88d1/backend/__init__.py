# app/api/v1/endpoints/__init__.py
from .tasks import router as tasks_router
from .health import router as health_router

__all__ = ["tasks_router", "health_router"]