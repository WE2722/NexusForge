# User presence and authentication service
from ..models import User
from ..storage.in_memory import users, user_presence
from typing import Dict

class UserService:
    @staticmethod
    def get_user(user_id: str) -> User | None:
        return users.get(user_id)

    @staticmethod
    def update_presence(user_id: str, is_online: bool) -> User:
        user = users[user_id]
        user.is_online = is_online
        user.last_active = datetime.utcnow()
        user_presence[user_id] = is_online
        return user

    @staticmethod
    def get_online_users() -> Dict[str, User]:
        return {uid: u for uid, u in users.items() if u.is_online}