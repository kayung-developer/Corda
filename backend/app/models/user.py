# backend/app/models/user.py
from typing import Optional, List # Corrected: Optional from typing
from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from datetime import datetime # Added for subscription_expires_at

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class SubscriptionPlan(str, Enum):
    NONE = "none"
    BASIC = "basic"
    PREMIUM = "premium"
    PRO = "pro"

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(UserBase):
    password: Optional[str] = Field(None, min_length=8)
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserInDBBase(UserBase):
    id: int
    role: UserRole = UserRole.USER
    subscription_plan: SubscriptionPlan = SubscriptionPlan.NONE
    subscription_expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Pydantic V2, replaces orm_mode = True

class User(UserInDBBase):
    pass

class UserInDB(UserInDBBase):
    hashed_password: str

# Placeholder for database storage (replace with SQLAlchemy models for a real DB)
# This is a simplified in-memory store for demonstration.
# In a real app, use SQLAlchemy with Alembic for migrations.
db_users: dict[int, UserInDB] = {}
user_id_counter = 1

# Token models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None # Store user_id in token