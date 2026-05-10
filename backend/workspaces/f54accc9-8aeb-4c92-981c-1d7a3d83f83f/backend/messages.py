# Fixed: Added missing HTTPException import
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from ..schemas import SendMessageRequest
from ..services.chat_service import ChatService
from ..services.user_service import UserService
from typing import List
from datetime import datetime