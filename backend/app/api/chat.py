"""
Chat API Router — REST and WebSocket endpoints for the AI chat assistant.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

import structlog

from app.models.schemas import ChatRequest, ChatResponse, ChatMessage

logger = structlog.get_logger(__name__)

chat_router = APIRouter()

# Lazy-initialized ChatOrchestrator (set during app startup from main.py)
_chat_orchestrator = None


def get_chat_orchestrator():
    """Get or create the ChatOrchestrator singleton."""
    global _chat_orchestrator
    if _chat_orchestrator is None:
        # Import here to avoid circular imports at module level
        from app.api.routes import orchestrator
        from app.services.chat_orchestrator import ChatOrchestrator
        _chat_orchestrator = ChatOrchestrator(orchestrator)
    return _chat_orchestrator


# ── REST Endpoints ─────────────────────────────────────────────────

@chat_router.post("/projects/{project_id}/chat", response_model=ChatResponse)
async def send_chat_message(project_id: str, request: ChatRequest):
    """
    Send a chat message to modify a project.
    The AI assistant will understand the intent, run appropriate agents,
    and return a summary of changes made.
    """
    chat_orch = get_chat_orchestrator()

    try:
        response = await chat_orch.process_message(request.message, project_id)
        return response
    except Exception as exc:
        logger.error("chat_endpoint_error", project_id=project_id, error=str(exc))
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(exc)}")


@chat_router.get("/projects/{project_id}/chat/history")
async def get_chat_history(project_id: str):
    """
    Get conversation history for a project.
    Returns up to the last 20 messages.
    """
    chat_orch = get_chat_orchestrator()
    messages = chat_orch.get_history(project_id)

    return {
        "messages": [m.model_dump(mode="json") for m in messages],
        "count": len(messages),
    }


@chat_router.delete("/projects/{project_id}/chat/history")
async def clear_chat_history(project_id: str):
    """Clear conversation history for a project."""
    chat_orch = get_chat_orchestrator()
    cleared = chat_orch.clear_history(project_id)
    return {"cleared": cleared}


# ── WebSocket Endpoint ─────────────────────────────────────────────

@chat_router.websocket("/ws/projects/{project_id}/chat")
async def chat_websocket(websocket: WebSocket, project_id: str):
    """
    WebSocket for real-time chat streaming.
    Sends progress updates as the assistant processes the request.
    """
    await websocket.accept()
    chat_orch = get_chat_orchestrator()

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            payload = json.loads(data)
            user_message = payload.get("message", "")

            if not user_message:
                await websocket.send_json({"type": "error", "content": "Empty message"})
                continue

            # Send "thinking" status
            await websocket.send_json({
                "type": "status",
                "content": "Thinking...",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            # Send "classifying" status
            await websocket.send_json({
                "type": "status",
                "content": "Analyzing your request...",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            # Process the message
            try:
                response = await chat_orch.process_message(user_message, project_id)

                # Send agent activity updates
                for agent_name in response.agents_involved:
                    await websocket.send_json({
                        "type": "agent_activity",
                        "content": f"{agent_name.capitalize()} Agent modifying code...",
                        "agent": agent_name,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

                # Send final response
                await websocket.send_json({
                    "type": "response",
                    "content": response.response,
                    "intent": response.intent,
                    "changes": [c.model_dump() for c in response.changes],
                    "agents_involved": response.agents_involved,
                    "status": response.status,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            except Exception as exc:
                logger.error("ws_process_error", error=str(exc))
                await websocket.send_json({
                    "type": "error",
                    "content": f"Failed to process message: {str(exc)}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

    except WebSocketDisconnect:
        logger.info("ws_disconnected", project_id=project_id)
    except Exception as exc:
        logger.error("ws_error", project_id=project_id, error=str(exc))
