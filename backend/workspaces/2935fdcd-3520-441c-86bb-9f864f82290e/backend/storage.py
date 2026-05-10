# In-memory storage implementation for tasks
from typing import Dict, List, Optional
from .models import Task, TaskCreate, TaskUpdate

class TaskStorage:
    """In-memory storage for tasks with basic CRUD operations"""

    def __init__(self):
        self.tasks: Dict[int, Task] = {}
        self.next_id = 1

    def create_task(self, task_data: TaskCreate) -> Task:
        """Create a new task"""
        task = Task(
            id=self.next_id,
            title=task_data.title,
            description=task_data.description,
            status="pending"
        )
        self.tasks[self.next_id] = task
        self.next_id += 1
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID"""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks"""
        return list(self.tasks.values())

    def update_task(self, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        """Update a task"""
        task = self.tasks.get(task_id)
        if not task:
            return None

        if task_data.title is not None:
            task.title = task_data.title
        if task_data.description is not None:
            task.description = task_data.description
        if task_data.status is not None:
            task.status = task_data.status

        return task

    def delete_task(self, task_id: int) -> bool:
        """Delete a task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False

    def filter_tasks_by_status(self, status: str) -> List[Task]:
        """Filter tasks by status"""
        return [task for task in self.tasks.values() if task.status == status]