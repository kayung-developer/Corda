# backend/app/api/v1/endpoints/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any

from backend.app.core import security
from backend.app.core.config import settings
from backend.app.models.user import User, UserCreate, Token, db_users, user_id_counter, \
    UserInDB  # Using in-memory store
from backend.app.api.deps import get_current_active_user

router = APIRouter()


@router.post("/register", response_model=User)
def register_user(user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    global user_id_counter
    # Check if user already exists
    for _, existing_user in db_users.items():
        if existing_user.email == user_in.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

    hashed_password = security.get_password_hash(user_in.password)
    new_user_id = user_id_counter
    user_id_counter += 1

    user_db_data = user_in.model_dump()
    user_db_data.pop("password")  # Remove plain password

    user_in_db = UserInDB(
        id=new_user_id,
        hashed_password=hashed_password,
        **user_db_data
    )
    db_users[new_user_id] = user_in_db

    # Return User model (not UserInDB which includes hashed_password)
    return User.model_validate(user_in_db)


@router.post("/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = None
    for _, u in db_users.items():
        if u.email == form_data.username:  # OAuth2PasswordRequestForm uses 'username' for email
            user = u
            break

    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "user_id": user.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_active_user)) -> Any:
    """
    Get current user.
    """
    return current_user