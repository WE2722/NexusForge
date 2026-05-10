from fastapi import Depends
from core.security import get_current_user

async def get_current_active_user(token: str = Depends(get_current_user)) -> str:
    """
    Dependency to get the current active user.
    In a real application, this would return a user object.
    """
    return token