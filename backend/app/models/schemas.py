"""
NexusForge Pydantic Models — full domain model for the orchestration system.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────
class ProjectStatus(str, Enum):
    PENDING = "pending"
    REFINING = "refining"
    PLANNING = "planning"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentType(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    ARCHITECTURE = "architecture"
    DEBUGGER = "debugger"
    REVIEW = "review"


class LLMProvider(str, Enum):
    GOOGLE = "google"
    GROQ = "groq"
    MISTRAL = "mistral"
    OPENROUTER = "openrouter"


class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


# ── Value Objects ──────────────────────────────────────────────────
class TokenUsage(BaseModel):
    """Tracks token consumption for a single LLM call."""
    provider: LLMProvider = LLMProvider.GOOGLE
    model: str = ""
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0.0, ge=0.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LLMRequest(BaseModel):
    """A request to an LLM provider."""
    provider: LLMProvider = LLMProvider.GOOGLE
    model: str = "gemini-2.0-flash"
    prompt: str = Field(..., min_length=1)
    system_prompt: str = ""
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    response_format: str = "text"


class LLMResponse(BaseModel):
    """Response from an LLM provider."""
    content: str = ""
    provider: LLMProvider = LLMProvider.GOOGLE
    model: str = ""
    usage: TokenUsage = Field(default_factory=TokenUsage)
    latency_ms: float = 0.0
    success: bool = True
    error: str = ""


class ProjectBrief(BaseModel):
    """Refined project brief extracted from a raw prompt."""
    title: str = Field(default="", max_length=200)
    description: str = ""
    intent: str = ""
    features: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    complexity: ComplexityLevel = ComplexityLevel.MODERATE
    estimated_tasks: int = Field(default=5, ge=1, le=100)
    raw_prompt: str = ""


# ── Agent Result ───────────────────────────────────────────────────
class AgentResult(BaseModel):
    """Output produced by a single agent execution."""
    agent_type: AgentType = AgentType.FRONTEND
    task_id: str = ""
    success: bool = True
    output: str = ""
    code_blocks: dict[str, str] = Field(default_factory=dict)
    files_created: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    reasoning: str = ""
    usage: TokenUsage = Field(default_factory=TokenUsage)
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Task ───────────────────────────────────────────────────────────
class Task(BaseModel):
    """A single unit of work within a project."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., min_length=1, max_length=300)
    description: str = ""
    agent_type: AgentType = AgentType.FRONTEND
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: list[str] = Field(default_factory=list)
    result: AgentResult | None = None
    attempts: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=3, ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    wave: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Project ────────────────────────────────────────────────────────
class Project(BaseModel):
    """Top-level entity representing a full project generation run."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw_prompt: str = Field(..., min_length=1)
    brief: ProjectBrief = Field(default_factory=ProjectBrief)
    status: ProjectStatus = ProjectStatus.PENDING
    tasks: list[Task] = Field(default_factory=list)
    total_tokens: TokenUsage = Field(default_factory=TokenUsage)
    files: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    user_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── API Request / Response Models ──────────────────────────────────
class CreateProjectRequest(BaseModel):
    """Request body for POST /projects."""
    prompt: str = Field(..., min_length=5, max_length=10000)


class ProjectSummary(BaseModel):
    """Lightweight project view for list endpoints."""
    id: str
    title: str = ""
    status: ProjectStatus = ProjectStatus.PENDING
    task_count: int = 0
    completed_tasks: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentInfo(BaseModel):
    """Public info about a registered agent."""
    name: str
    agent_type: AgentType
    role: str
    expertise: list[str] = Field(default_factory=list)
    preferred_providers: list[LLMProvider] = Field(default_factory=list)
    status: str = "ready"


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    uptime_seconds: float = 0.0
    services: dict[str, str] = Field(default_factory=dict)
