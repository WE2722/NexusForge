from typing import Dict, List, Set, Optional
from models import User, Room, Message
from schemas import UserCreate, RoomCreate, MessageCreate
import uuid
import asyncio

class UserService:
    @staticmethod
    def create_user(username: str) -> User:
        user_id = str(uuid.uuid4())
        user = User(id=user_id, username=username)
        return user

    @staticmethod
    def get_user(user_id: str, users_db: Dict[str, User]) -> Optional[User]:
        return users_db.get(user_id)

class RoomService:
    @staticmethod
    def create_room(name: str, creator_id: str, users_db: Dict[str, User], rooms_db: Dict[str, Room]) -> Room:
        room_id = str(uuid.uuid4())
        room = Room(id=room_id, name=name)
        rooms_db[room_id] = room
        room.users.add(creator_id)
        return room

    @staticmethod
    def get_room(room_id: str, rooms_db: Dict[str, Room]) -> Optional[Room]:
        return rooms_db.get(room_id)

    @staticmethod
    def join_room(room_id: str, user_id: str, rooms_db: Dict[str, Room], users_db: Dict[str, User]) -> bool:
        if room_id not in rooms_db or user_id not in users_db:
            return False
        rooms_db[room_id].users.add(user_id)
        return True

class MessageService:
    @staticmethod
    def send_message(room_id: str, user_id: str, content: str,
                   rooms_db: Dict[str, Room], users_db: Dict[str, User],
                   messages_db: List[Message]) -> Optional[Message]:
        if (room_id not in rooms_db or user_id not in users_db or
            user_id not in rooms_db[room_id].users):
            return None

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
        return message

    @staticmethod
    def get_room_messages(room_id: str, messages_db: List[Message]) -> List[Message]:
        return [msg for msg in messages_db if msg.room_id == room_id]