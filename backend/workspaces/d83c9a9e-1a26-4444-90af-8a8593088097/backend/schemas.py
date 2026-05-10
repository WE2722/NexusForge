from pydantic import BaseModel
from typing import Set, Optional

# User schemas
class UserCreate(BaseModel):
    username: str

class UserResponse(BaseModel):
    id: str
    username: str
    is_online: bool
    last_active: str

# Room schemas
class RoomCreate(BaseModel):
    name: str
    creator_id: str

class RoomResponse(BaseModel):
    id: str
    name: str
    users: Set[str]

class JoinRoom(BaseModel):
    user_id: str

# Message schemas
class MessageCreate(BaseModel):
    room_id: str
    user_id: str
    content: str

class MessageResponse(BaseModel):
    id: str
    room_id: str
    user_id: str
    content: str
    timestamp: str