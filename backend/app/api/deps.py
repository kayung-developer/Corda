# backend/app/api/deps.py
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import ValidationError

from backend.app.core import security
from backend.app.core.config import settings
from backend.app.models.user import User, TokenData, db_users  # Using in-memory store

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


def get_current_user(token: str = Depends(reusable_oauth2)) -> User:
    try:
        payload = security.decode_access_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials (token payload missing)",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_data = TokenData(**payload)

        if token_data.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials (user_id missing in token)",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials (JWTError)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValidationError:  # Pydantic validation error for TokenData
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials (TokenData malformed)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db_users.get(token_data.user_id)  # Fetch user from "DB"
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Convert UserInDB to User (Pydantic model for response, if needed or just use UserInDB directly)
    return User.model_validate(user)  # Pydantic V2


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Dependency for superuser/admin - can be expanded
# def get_current_active_superuser(current_user: User = Depends(get_current_user)) -> User:
#     if current_user.role != "admin": # Assuming User model has a role
#         raise HTTPException(
#             status_code=403, detail="The user doesn't have enough privileges"
#         )
#     return current_user