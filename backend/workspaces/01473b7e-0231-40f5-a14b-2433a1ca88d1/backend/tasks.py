# app/api/v1/endpoints/tasks.py
from fastapi import APIRouter, Depends, status, HTTPException
from typing import List

from models.schemas import (
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from services.task_service import task_service
from utils.exceptions import NotFoundException
from custom_logger import logger

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    response_description="The created task",
)
async def create_task(
    task: TaskCreate,
):
    """Create a new task in the todo list."""
    try:
        logger.info(f"Creating new task: {task.title}")
        created_task = await task_service.create_task(
            title=task.title,
            description=task.description,
        )
        return created_task
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task",
        )

@router.get(
    "/",
    response_model=List[TaskResponse],
    summary="Get all tasks",
    response_description="List of all tasks",
)
async def get_all_tasks():
    """Get all tasks from the todo list."""
    try:
        logger.info("Fetching all tasks")
        tasks = await task_service.get_all_tasks()
        return tasks
    except Exception as e:
        logger.error(f"Error fetching tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tasks",
        )

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a specific task",
    response_description="The requested task",
)
async def get_task(task_id: int):
    """Get a specific task by ID."""
    try:
        logger.info(f"Fetching task with ID: {task_id}")
        task = await task_service.get_task(task_id)
        return task
    except NotFoundException:
        logger.warning(f"Task with ID {task_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error fetching task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch task",
        )

@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
    response_description="The updated task",
)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
):
    """Update an existing task."""
    try:
        logger.info(f"Updating task with ID: {task_id}")
        task_data = task_update.model_dump(exclude_unset=True)
        updated_task = await task_service.update_task(
            task_id,
            **task_data,
        )
        return updated_task
    except NotFoundException:
        logger.warning(f"Task with ID {task_id} not found for update")
        raise
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task",
        )

@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    response_description="No content",
)
async def delete_task(task_id: int):
    """Delete a task by ID."""
    try:
        logger.info(f"Deleting task with ID: {task_id}")
        await task_service.delete_task(task_id)
        return None
    except NotFoundException:
        logger.warning(f"Task with ID {task_id} not found for deletion")
        raise
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task",
        )

@router.patch(
    "/{task_id}/toggle",
    response_model=TaskResponse,
    summary="Toggle task completion status",
    response_description="The updated task",
)
async def toggle_task_status(task_id: int):
    """Toggle a task's completion status."""
    try:
        logger.info(f"Toggling status for task with ID: {task_id}")
        toggled_task = await task_service.toggle_task_status(task_id)
        return toggled_task
    except NotFoundException:
        logger.warning(f"Task with ID {task_id} not found for status toggle")
        raise
    except Exception as e:
        logger.error(f"Error toggling task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle task status",
        )