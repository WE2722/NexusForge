# Pydantic models for request/response validation and serialization
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class TaskStatus(str, Enum):
    """Enumeration for task statuses"""
    PENDING = "pending"
    COMPLETED = "completed"

class TaskBase(BaseModel):
    """Base task model with common fields"""
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class TaskCreate(TaskBase):
    """Model for creating a new task"""
    pass

class TaskUpdate(BaseModel):
    """Model for updating a task"""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[TaskStatus] = None

class Task(TaskBase):
    """Complete task model with ID and status"""
    id: int
    status: TaskStatus = TaskStatus.PENDING

    class Config:
        from_attributes = True  # Enable ORM mode for Pydantic V2