from pydantic import BaseModel
from typing import Set

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