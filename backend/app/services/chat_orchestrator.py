"""
ChatOrchestrator — AI assistant that modifies generated projects via natural-language chat.

Flow:
  1. User sends a message (e.g. "Add dark mode toggle")
  2. Classify intent → ADD_FEATURE
  3. Identify affected files (frontend components, maybe backend theme endpoint)
  4. Identify required agents (FrontendAgent, maybe BackendAgent)
  5. Create targeted tasks → only those agents run
  6. Apply changes safely (backup → lock → apply → unlock)
  7. Return summary + diff to user
"""
from __future__ import annotations

import asyncio
import copy
import json
import os
import time
from datetime import datetime, timezone

import structlog

from app.core.llm_router import LLMRouter
from app.models.schemas import (
    AgentType,
    ChatIntent,
    ChatMessage,
    ChatResponse,
    FileChange,
    Project,
    Task,
    TaskPriority,
    TaskStatus,
)
from app.services.conflict_resolver import ConflictResolver

logger = structlog.get_logger(__name__)

HISTORY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "chat_history"))
MAX_HISTORY = 20

INTENT_SYSTEM_PROMPT = """You are an intent classifier for a code generation assistant.
Given a user message about modifying a software project, classify the intent.

Return ONLY a JSON object with these fields:
{
  "intent": "add_feature" | "fix_bug" | "change_design" | "refactor" | "change_stack" | "question",
  "summary": "brief description of what needs to change",
  "affected_areas": ["frontend", "backend", "database"],
  "confidence": 0.0 to 1.0
}

Rules:
- "add_feature": user wants new functionality (auth, dark mode, new page, API endpoint)
- "fix_bug": user reports something broken or not working
- "change_design": user wants visual/UI changes (colors, layout, animations)
- "refactor": user wants code restructuring without feature changes
- "change_stack": user wants to swap technologies (MongoDB→PostgreSQL, REST→GraphQL)
- "question": user is asking about the project, not requesting changes"""

MODIFICATION_SYSTEM_PROMPT = """You are a code modification assistant for NexusForge.
You receive the current project files and a user request.

Your job is to generate ONLY the modified/new files needed to fulfill the request.
Output each file as a labeled code block with the EXACT filename.

STRICT RULES:
- Only modify files that need changing — preserve everything else
- If creating a new file, give it a clear name and path
- Maintain consistent code style with the existing project
- Make sure all imports are correct
- If modifying backend, ensure API endpoints stay compatible
- If modifying frontend, ensure component props are correct

Example output:
```python main.py
# Modified: added dark mode endpoint
from fastapi import FastAPI
...
```

```tsx ThemeToggle.tsx
// New: dark mode toggle component
import React from 'react'
...
```"""


class ChatOrchestrator:
    """
    Processes user chat messages to modify generated projects.
    Uses LLM for intent classification and agent coordination.
    """

    def __init__(self, orchestrator) -> None:
        """
        Args:
            orchestrator: The main Orchestrator instance (for accessing agents, projects, router).
        """
        self._orchestrator = orchestrator
        self._router: LLMRouter = orchestrator.router
        self._conflict_resolver = ConflictResolver(default_timeout=15.0)
        os.makedirs(HISTORY_DIR, exist_ok=True)

    # ── Public API ─────────────────────────────────────────────────

    async def process_message(self, user_message: str, project_id: str) -> ChatResponse:
        """
        Main entry point: process a user chat message for a project.
        Returns a ChatResponse with summary, changes, and agents involved.
        """
        project = await self._orchestrator.get_project(project_id)
        if not project:
            return ChatResponse(
                response="Project not found.",
                status="failed",
            )

        # Save user message to history
        user_msg = ChatMessage(role="user", content=user_message)
        self._append_history(project_id, user_msg)

        logger.info("chat_processing", project_id=project_id, message=user_message[:100])

        # Step 1: Classify intent
        intent, summary, affected_areas = await self._classify_intent(user_message, project)

        # Step 2: Handle question intent (no code changes)
        if intent == ChatIntent.QUESTION:
            answer = await self._answer_question(user_message, project)
            assistant_msg = ChatMessage(
                role="assistant",
                content=answer,
                intent=intent.value,
            )
            self._append_history(project_id, assistant_msg)
            return ChatResponse(response=answer, intent=intent.value, status="completed")

        # Step 3: Identify affected files and required agents
        project_files = self._collect_project_files(project)
        affected_files = self._identify_affected_files(intent, user_message, affected_areas, project_files)
        required_agents = self._identify_required_agents(affected_areas, affected_files)

        # Step 4: Create modification tasks and execute
        changes, agents_used = await self._execute_modifications(
            user_message, summary, intent, project, project_files, required_agents
        )

        # Step 5: Apply changes to project
        if changes:
            await self._apply_changes_safely(project, changes)
            self._orchestrator._save_projects()

        # Step 6: Format response
        file_changes = [
            FileChange(
                file=filename,
                action="modified" if filename in project_files else "created",
                diff=f"Updated by {', '.join(agents_used)} agents",
            )
            for filename in changes.keys()
        ]

        response_text = (
            f"✅ {summary}\n\n"
            f"**Changes made:**\n"
            + "\n".join(f"- `{fc.file}` ({fc.action})" for fc in file_changes)
            + f"\n\n**Agents involved:** {', '.join(agents_used)}"
        )

        assistant_msg = ChatMessage(
            role="assistant",
            content=response_text,
            intent=intent.value,
            changes=file_changes,
            agents_involved=agents_used,
            status="completed" if changes else "partial",
        )
        self._append_history(project_id, assistant_msg)

        return ChatResponse(
            response=response_text,
            intent=intent.value,
            changes=file_changes,
            agents_involved=agents_used,
            status="completed" if changes else "partial",
        )

    def get_history(self, project_id: str) -> list[ChatMessage]:
        """Return conversation history for a project."""
        history_path = os.path.join(HISTORY_DIR, f"{project_id}.json")
        if not os.path.exists(history_path):
            return []
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [ChatMessage.model_validate(m) for m in data]
        except Exception as exc:
            logger.error("chat_history_load_error", error=str(exc))
            return []

    def clear_history(self, project_id: str) -> bool:
        """Clear conversation history for a project."""
        history_path = os.path.join(HISTORY_DIR, f"{project_id}.json")
        if os.path.exists(history_path):
            os.remove(history_path)
            return True
        return False

    # ── Intent Classification ──────────────────────────────────────

    async def _classify_intent(
        self, message: str, project: Project
    ) -> tuple[ChatIntent, str, list[str]]:
        """Use LLM to classify the user's intent."""
        from app.models.schemas import LLMRequest, LLMProvider

        context_summary = (
            f"Project: {project.brief.title}\n"
            f"Tech stack: {', '.join(project.brief.tech_stack)}\n"
            f"Features: {', '.join(project.brief.features)}"
        )

        request = LLMRequest(
            provider=LLMProvider.GOOGLE,
            prompt=f"Project context:\n{context_summary}\n\nUser message: {message}",
            system_prompt=INTENT_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=512,
        )

        response = await self._router.generate(request)

        if not response.success:
            logger.warning("intent_classify_fallback", error=response.error)
            return ChatIntent.ADD_FEATURE, message, ["frontend", "backend"]

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            data = json.loads(content.strip())

            intent = ChatIntent(data.get("intent", "add_feature"))
            summary = data.get("summary", message)
            affected_areas = data.get("affected_areas", ["frontend", "backend"])

            return intent, summary, affected_areas
        except Exception as exc:
            logger.warning("intent_parse_fallback", error=str(exc))
            return ChatIntent.ADD_FEATURE, message, ["frontend", "backend"]

    # ── Question Handling ──────────────────────────────────────────

    async def _answer_question(self, question: str, project: Project) -> str:
        """Answer a question about the project without making changes."""
        from app.models.schemas import LLMRequest, LLMProvider

        project_files = self._collect_project_files(project)
        file_list = "\n".join(f"- {name}" for name in project_files.keys())

        request = LLMRequest(
            provider=LLMProvider.GOOGLE,
            prompt=(
                f"Project: {project.brief.title}\n"
                f"Description: {project.brief.description}\n"
                f"Tech stack: {', '.join(project.brief.tech_stack)}\n"
                f"Files:\n{file_list}\n\n"
                f"Question: {question}\n\n"
                f"Answer concisely and helpfully."
            ),
            system_prompt="You are a helpful project assistant. Answer questions about the project clearly.",
            temperature=0.5,
            max_tokens=2048,
        )

        response = await self._router.generate(request)
        return response.content if response.success else "I couldn't process that question. Please try again."

    # ── File & Agent Identification ────────────────────────────────

    def _collect_project_files(self, project: Project) -> dict[str, str]:
        """Collect all code blocks from completed tasks."""
        files: dict[str, str] = {}
        for task in project.tasks:
            if task.result and task.result.code_blocks:
                files.update(task.result.code_blocks)
        return files

    def _identify_affected_files(
        self,
        intent: ChatIntent,
        message: str,
        affected_areas: list[str],
        project_files: dict[str, str],
    ) -> list[str]:
        """Identify which existing files are likely affected."""
        affected = []
        msg_lower = message.lower()

        for filename in project_files:
            fname_lower = filename.lower()

            # Area-based matching
            if "frontend" in affected_areas and fname_lower.endswith((".tsx", ".ts", ".jsx", ".js", ".css")):
                affected.append(filename)
            elif "backend" in affected_areas and fname_lower.endswith((".py",)):
                affected.append(filename)
            elif "database" in affected_areas and any(kw in fname_lower for kw in ("model", "schema", "database", "db")):
                affected.append(filename)

        return affected

    def _identify_required_agents(
        self, affected_areas: list[str], affected_files: list[str]
    ) -> list[AgentType]:
        """Determine which agents need to run based on affected areas/files."""
        agents: set[AgentType] = set()

        area_map = {
            "frontend": AgentType.FRONTEND,
            "backend": AgentType.BACKEND,
            "database": AgentType.DATABASE,
        }
        for area in affected_areas:
            if area in area_map:
                agents.add(area_map[area])

        # Also infer from file extensions
        for f in affected_files:
            if f.endswith((".tsx", ".ts", ".jsx", ".js", ".css")):
                agents.add(AgentType.FRONTEND)
            elif f.endswith(".py"):
                agents.add(AgentType.BACKEND)

        return list(agents) if agents else [AgentType.FRONTEND, AgentType.BACKEND]

    # ── Modification Execution ─────────────────────────────────────

    async def _execute_modifications(
        self,
        user_message: str,
        summary: str,
        intent: ChatIntent,
        project: Project,
        project_files: dict[str, str],
        required_agents: list[AgentType],
    ) -> tuple[dict[str, str], list[str]]:
        """Execute targeted modifications using the required agents."""
        all_changes: dict[str, str] = {}
        agents_used: list[str] = []

        # Build context: existing files relevant to the change
        existing_code = ""
        for filename, code in project_files.items():
            existing_code += f"\n--- {filename} ---\n{code}\n"

        # Create tasks for each required agent
        for agent_type in required_agents:
            agent = self._orchestrator._agents.get(agent_type)
            if not agent:
                continue

            area_name = agent_type.value
            task = Task(
                title=f"Chat modification ({area_name}): {summary[:100]}",
                description=(
                    f"User request: {user_message}\n\n"
                    f"Intent: {intent.value}\n\n"
                    f"Modify the {area_name} code to fulfill this request.\n"
                    f"Only output files that need to change."
                ),
                agent_type=agent_type,
                priority=TaskPriority.HIGH,
                metadata={
                    "context": existing_code[:8000],  # Limit context size
                    "chat_modification": True,
                },
            )

            try:
                result = await agent.execute(task)
                if result.success and result.code_blocks:
                    all_changes.update(result.code_blocks)
                    agents_used.append(area_name)
                    logger.info("chat_agent_success", agent=area_name, files=list(result.code_blocks.keys()))
                elif result.success:
                    agents_used.append(area_name)
                    logger.info("chat_agent_no_changes", agent=area_name)
                else:
                    logger.warning("chat_agent_failed", agent=area_name, errors=result.errors)
            except Exception as exc:
                logger.error("chat_agent_error", agent=area_name, error=str(exc))

        return all_changes, agents_used

    # ── Safe Change Application ────────────────────────────────────

    async def _apply_changes_safely(
        self, project: Project, changes: dict[str, str]
    ) -> None:
        """Apply code changes to the project with file locking and backup."""
        # Backup current state
        backup = {}
        for task in project.tasks:
            if task.result and task.result.code_blocks:
                backup.update(copy.deepcopy(task.result.code_blocks))

        try:
            for filename, new_code in changes.items():
                async with self._conflict_resolver.lock_file(filename, owner="chat_orchestrator"):
                    # Find the task that owns this file and update it
                    applied = False
                    for task in project.tasks:
                        if task.result and task.result.code_blocks and filename in task.result.code_blocks:
                            task.result.code_blocks[filename] = new_code
                            applied = True
                            break

                    # If file doesn't exist yet, add to the most relevant task
                    if not applied:
                        target_task = self._find_target_task(project, filename)
                        if target_task and target_task.result:
                            target_task.result.code_blocks[filename] = new_code
                        else:
                            logger.warning("chat_no_target_task", filename=filename)

            project.updated_at = datetime.now(timezone.utc)
            logger.info("chat_changes_applied", files=list(changes.keys()))

        except Exception as exc:
            # Rollback on failure
            logger.error("chat_apply_failed", error=str(exc))
            for task in project.tasks:
                if task.result and task.result.code_blocks:
                    for filename in task.result.code_blocks:
                        if filename in backup:
                            task.result.code_blocks[filename] = backup[filename]
            raise

    def _find_target_task(self, project: Project, filename: str) -> Task | None:
        """Find the best task to attach a new file to based on file extension."""
        ext = os.path.splitext(filename)[1].lower()
        target_type = AgentType.FRONTEND if ext in (".tsx", ".ts", ".jsx", ".js", ".css") else AgentType.BACKEND

        for task in project.tasks:
            if task.agent_type == target_type and task.result:
                return task
        # Fallback: any task with result
        for task in project.tasks:
            if task.result:
                return task
        return None

    # ── History Persistence ────────────────────────────────────────

    def _append_history(self, project_id: str, message: ChatMessage) -> None:
        """Append a message to the conversation history."""
        history = self.get_history(project_id)
        history.append(message)

        # Trim to max
        if len(history) > MAX_HISTORY:
            history = history[-MAX_HISTORY:]

        history_path = os.path.join(HISTORY_DIR, f"{project_id}.json")
        try:
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump([m.model_dump(mode="json") for m in history], f)
        except Exception as exc:
            logger.error("chat_history_save_error", error=str(exc))
