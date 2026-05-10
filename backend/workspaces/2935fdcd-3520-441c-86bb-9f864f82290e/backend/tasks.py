# Task-related API endpoints
from fastapi import APIRouter, HTTPException, status
from typing import List
from ..models import Task, TaskCreate, TaskUpdate
from ..storage import TaskStorage

router = APIRouter(prefix="/tasks", tags=["tasks"])
storage = TaskStorage()

@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskCreate):
    """Create a new task"""
    return storage.create_task(task_data)

@router.get("/", response_model=List[Task])
async def get_all_tasks():
    """Get all tasks"""
    return storage.get_all_tasks()

@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: int):
    """Get a task by ID"""
    task = storage.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=Task)
async def update_task(task_id: int, task_data: TaskUpdate):
    """Update a task"""
    task = storage.update_task(task_id, task_data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int):
    """Delete a task"""
    if not storage.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")

@router.get("/filter/{status}", response_model=List[Task])
async def filter_tasks_by_status(status: str):
    """Filter tasks by status (pending/completed)"""
    return storage.filter_tasks_by_status(status)