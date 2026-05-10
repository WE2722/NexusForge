from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security, HTTPException, status
from typing import Optional

security = HTTPBearer()

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> str:
    """
    Security dependency to validate API access.
    In production, you would validate against a real auth system.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # In a real app, you would validate the token here
    # For demo purposes, we'll just check if it's provided
    if not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials