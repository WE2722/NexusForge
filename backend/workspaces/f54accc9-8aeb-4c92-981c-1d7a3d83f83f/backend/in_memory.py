# In-memory storage implementation
from typing import Dict, List
from ..models import User, ChatRoom, Message

users: Dict[str, User] = {}
rooms: Dict[str, ChatRoom] = {}
messages: Dict[str, List[Message]] = {}
user_presence: Dict[str, bool] = {}

def init_storage():
    """Initialize with sample data"""
    # Add sample users
    users["user1"] = User(id="user1", username="Alice")
    users["user2"] = User(id="user2", username="Bob")
    users["user3"] = User(id="user3", username="Charlie")

    # Add sample room
    rooms["room1"] = ChatRoom(
        id="room1",
        name="General Chat",
        participants=["user1", "user2", "user3"]
    )

    # Add sample messages
    messages["room1"] = [
        Message(
            id="msg1",
            room_id="room1",
            sender_id="user1",
            content="Hello everyone!"
        )
    ]