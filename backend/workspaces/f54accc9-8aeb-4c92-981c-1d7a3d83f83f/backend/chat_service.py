# Core chat service
from ..models import ChatRoom, Message
from ..storage.in_memory import rooms, messages
from typing import List
from uuid import uuid4
from datetime import datetime

class ChatService:
    @staticmethod
    def create_room(name: str, participant_ids: List[str]) -> ChatRoom:
        room_id = str(uuid4())
        room = ChatRoom(
            id=room_id,
            name=name,
            participants=participant_ids
        )
        rooms[room_id] = room
        messages[room_id] = []
        return room

    @staticmethod
    def send_message(room_id: str, sender_id: str, content: str) -> Message:
        message_id = str(uuid4())
        message = Message(
            id=message_id,
            room_id=room_id,
            sender_id=sender_id,
            content=content
        )
        messages[room_id].append(message)
        return message

    @staticmethod
    def get_room_messages(room_id: str) -> List[Message]:
        return messages.get(room_id, [])

    @staticmethod
    def get_user_rooms(user_id: str) -> List[ChatRoom]:
        return [room for room in rooms.values() if user_id in room.participants]