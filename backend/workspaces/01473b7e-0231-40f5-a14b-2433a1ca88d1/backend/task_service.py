# app/services/task_service.py
from typing import List, Dict, Optional
from datetime import datetime
from models.task import Task, TaskStatus
from utils.exceptions import NotFoundException

class TaskService:
    def __init__(self):
        self.tasks: Dict[int, Task] = {}
        self.next_id = 1

    async def create_task(self, title: str, description: Optional[str] = None) -> Task:
        """Create a new task."""
        task = Task(
            id=self.next_id,
            title=title,
            description=description,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.tasks[self.next_id] = task
        self.next_id += 1
        return task

    async def get_task(self, task_id: int) -> Task:
        """Get a task by ID."""
        if task_id not in self.tasks:
            raise NotFoundException(f"Task with ID {task_id} not found")
        return self.tasks[task_id]

    async def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return list(self.tasks.values())

    async def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[TaskStatus] = None,
    ) -> Task:
        """Update a task."""
        task = await self.get_task(task_id)
        update_data = {
            "title": title,
            "description": description,
            "status": status,
        }
        updated_task = task.update(**update_data)
        self.tasks[task_id] = updated_task
        return updated_task

    async def delete_task(self, task_id: int) -> None:
        """Delete a task."""
        if task_id not in self.tasks:
            raise NotFoundException(f"Task with ID {task_id} not found")
        del self.tasks[task_id]

    async def toggle_task_status(self, task_id: int) -> Task:
        """Toggle task completion status."""
        task = await self.get_task(task_id)
        new_status = (
            TaskStatus.completed
            if task.status == TaskStatus.pending
            else TaskStatus.pending
        )
        return await self.update_task(task_id, status=new_status)

# Initialize service
task_service = TaskService()