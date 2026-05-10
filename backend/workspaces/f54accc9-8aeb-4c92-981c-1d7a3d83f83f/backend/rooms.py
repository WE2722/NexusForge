# Room-related API endpoints
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..schemas import CreateRoomRequest, RoomWithParticipants
from ..services.chat_service import ChatService
from ..services.user_service import UserService
from typing import List

router = APIRouter(prefix="/api/rooms", tags=["rooms"])

@router.post("/", response_model=RoomWithParticipants)
async def create_room(request: CreateRoomRequest):
    room = ChatService.create_room(
        name=request.name,
        participant_ids=request.participant_ids
    )
    participants = [UserService.get_user(uid) for uid in request.participant_ids]
    return {"room": room, "participants": participants}

@router.get("/", response_model=List[RoomWithParticipants])
async def get_user_rooms(user_id: str):
    rooms = ChatService.get_user_rooms(user_id)
    return [{
        "room": room,
        "participants": [UserService.get_user(uid) for uid in room.participants]
    } for room in rooms]