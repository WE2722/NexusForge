import custom_logger
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import structlog

# Initialize structured logging
structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

app = FastAPI(
    title="Todo List API",
    description="A simple Todo List backend with FastAPI",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS configuration (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
todos = {}

# Pydantic models
class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, example="Buy groceries")
    description: Optional[str] = Field(None, max_length=300, example="Milk, eggs, bread")

class TodoCreate(TodoBase):
    pass

class TodoResponse(TodoBase):
    id: str
    completed: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Dependency to get a todo by ID
async def get_todo(todo_id: str) -> TodoResponse:
    if todo_id not in todos:
        logger.warning("Todo not found", todo_id=todo_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )
    return todos[todo_id]

# Root endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Create a new todo
@app.post(
    "/api/todos",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"}
    }
)
async def create_todo(todo: TodoCreate):
    """Create a new todo item"""
    try:
        todo_id = str(uuid.uuid4())
        now = datetime.utcnow()

        new_todo = TodoResponse(
            id=todo_id,
            title=todo.title,
            description=todo.description,
            completed=False,
            created_at=now,
            updated_at=now
        )

        todos[todo_id] = new_todo
        logger.info("Todo created", todo_id=todo_id)
        return new_todo
    except Exception as e:
        logger.error("Failed to create todo", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create todo"
        )

# Get all todos
@app.get(
    "/api/todos",
    response_model=List[TodoResponse],
    responses={
        500: {"description": "Internal Server Error"}
    }
)
async def get_all_todos():
    """Get all todo items"""
    try:
        return list(todos.values())
    except Exception as e:
        logger.error("Failed to fetch todos", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch todos"
        )

# Get a specific todo
@app.get(
    "/api/todos/{todo_id}",
    response_model=TodoResponse,
    responses={
        404: {"description": "Todo not found"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_todo_item(todo: TodoResponse = Depends(get_todo)):
    """Get a specific todo item"""
    return todo

# Update a todo (mark as completed)
@app.patch(
    "/api/todos/{todo_id}/complete",
    response_model=TodoResponse,
    responses={
        404: {"description": "Todo not found"},
        500: {"description": "Internal Server Error"}
    }
)
async def complete_todo(todo: TodoResponse = Depends(get_todo)):
    """Mark a todo as completed"""
    try:
        todo.completed = True
        todo.updated_at = datetime.utcnow()
        todos[todo.id] = todo
        logger.info("Todo marked as completed", todo_id=todo.id)
        return todo
    except Exception as e:
        logger.error("Failed to update todo", todo_id=todo.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update todo"
        )

# Delete a todo
@app.delete(
    "/api/todos/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Todo not found"},
        500: {"description": "Internal Server Error"}
    }
)
async def delete_todo(todo_id: str):
    """Delete a todo item"""
    try:
        if todo_id not in todos:
            logger.warning("Attempted to delete non-existent todo", todo_id=todo_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Todo with id {todo_id} not found"
            )

        del todos[todo_id]
        logger.info("Todo deleted", todo_id=todo_id)
        return None
    except Exception as e:
        logger.error("Failed to delete todo", todo_id=todo_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete todo"
        )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.warning("HTTP Exception", status_code=exc.status_code, detail=exc.detail)
    return {"status_code": exc.status_code, "message": exc.detail}

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error("Unhandled Exception", error=str(exc))
    return {"status_code": 500, "message": "Internal Server Error"}