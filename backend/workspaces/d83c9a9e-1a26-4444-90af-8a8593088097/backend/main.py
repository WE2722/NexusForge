# Fixed: Added proper API prefix and corrected endpoint paths
import asyncio
import uuid
from typing import Dict, List, Set, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from pydantic import BaseModel

# Configuration
class Settings(BaseSettings):
    app_name: str = "Real-Time Chat API"
    websocket_timeout: int = 60
    api_prefix: str = "/api/v1"

    class Config:
        env_file = ".env"

settings = Settings()

# Data models
class User(BaseModel):
    id: str
    username: str
    is_online: bool = True
    last_active: str = ""

class Room(BaseModel):
    id: str
    name: str
    users: Set[str] = set()

class Message(BaseModel):
    id: str
    room_id: str
    user_id: str
    content: str
    timestamp: str

# In-memory storage
users_db: Dict[str, User] = {}
rooms_db: Dict[str, Room] = {}
messages_db: List[Message] = []
user_connections: Dict[str, WebSocket] = {}

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        users_db[user_id].is_online = True
        users_db[user_id].last_active = str(asyncio.get_event_loop().time())

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                users_db[user_id].is_online = False

    async def broadcast(self, room_id: str, message: dict):
        if room_id in rooms_db:
            for user_id in rooms_db[room_id].users:
                if user_id in self.active_connections:
                    for connection in self.active_connections[user_id]:
                        await connection.send_json(message)

manager = ConnectionManager()

# FastAPI app
app = FastAPI(title=settings.app_name)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API endpoints
@app.get(f"{settings.api_prefix}/health")
async def health_check():
    return {"status": "healthy"}

@app.post(f"{settings.api_prefix}/users")
async def create_user(username: str):
    user_id = str(uuid.uuid4())
    user = User(id=user_id, username=username)
    users_db[user_id] = user
    return user

@app.get(f"{settings.api_prefix}/users/{{user_id}}")
async def get_user(user_id: str):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.post(f"{settings.api_prefix}/rooms")
async def create_room(name: str, creator_id: str):
    if creator_id not in users_db:
        raise HTTPException(status_code=404, detail="Creator not found")

    room_id = str(uuid.uuid4())
    room = Room(id=room_id, name=name)
    rooms_db[room_id] = room
    room.users.add(creator_id)

    # Add creator to room
    users_db[creator_id].last_active = str(asyncio.get_event_loop().time())
    return room

@app.get(f"{settings.api_prefix}/rooms")
async def list_rooms():
    return list(rooms_db.values())

@app.get(f"{settings.api_prefix}/rooms/{{room_id}}")
async def get_room(room_id: str):
    if room_id not in rooms_db:
        raise HTTPException(status_code=404, detail="Room not found")
    return rooms_db[room_id]

@app.post(f"{settings.api_prefix}/rooms/{{room_id}}/join")
async def join_room(room_id: str, user_id: str):
    if room_id not in rooms_db:
        raise HTTPException(status_code=404, detail="Room not found")
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    rooms_db[room_id].users.add(user_id)
    users_db[user_id].last_active = str(asyncio.get_event_loop().time())
    return {"message": f"User {user_id} joined room {room_id}"}

@app.post(f"{settings.api_prefix}/messages")
async def send_message(room_id: str, user_id: str, content: str):
    if room_id not in rooms_db:
        raise HTTPException(status_code=404, detail="Room not found")
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    if user_id not in rooms_db[room_id].users:
        raise HTTPException(status_code=403, detail="User not in room")

    message_id = str(uuid.uuid4())
    timestamp = str(asyncio.get_event_loop().time())
    message = Message(
        id=message_id,
        room_id=room_id,
        user_id=user_id,
        content=content,
        timestamp=timestamp
    )

    messages_db.append(message)
    await manager.broadcast(room_id, {
        "type": "message",
        "message": message.dict()
    })
    return message

@app.get(f"{settings.api_prefix}/rooms/{{room_id}}/messages")
async def get_room_messages(room_id: str):
    if room_id not in rooms_db:
        raise HTTPException(status_code=404, detail="Room not found")
    return [msg for msg in messages_db if msg.room_id == room_id]

@app.websocket(f"{settings.api_prefix}/ws/{{user_id}}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Update last active time
            if user_id in users_db:
                users_db[user_id].last_active = str(asyncio.get_event_loop().time())

            # Broadcast presence update to all rooms the user is in
            for room in rooms_db.values():
                if user_id in room.users:
                    await manager.broadcast(room.id, {
                        "type": "presence",
                        "user_id": user_id,
                        "is_online": True,
                        "last_active": users_db[user_id].last_active
                    })

    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
        # Notify all rooms the user was in
        for room in rooms_db.values():
            if user_id in room.users:
                await manager.broadcast(room.id, {
                    "type": "presence",
                    "user_id": user_id,
                    "is_online": False
                })