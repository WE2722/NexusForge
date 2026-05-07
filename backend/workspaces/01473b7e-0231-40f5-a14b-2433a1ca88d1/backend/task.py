# app/models/task.py
from datetime import datetime
from enum import Enum
from typing import Optional

class TaskStatus(str, Enum):
    pending = "pending"
    completed = "completed"

class Task:
    def __init__(
        self,
        id: int,
        title: str,
        description: Optional[str] = None,
        status: TaskStatus = TaskStatus.pending,
        created_at: datetime = datetime.now(),
        updated_at: datetime = datetime.now(),
    ):
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()
        return self