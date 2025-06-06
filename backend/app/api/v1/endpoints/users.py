# backend/app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException
from backend.app.models.user import User, UserUpdate, db_users  # Using in-memory store
from backend.app.api.deps import get_current_active_user
from backend.app.core.security import get_password_hash

router = APIRouter()


@router.get("/{user_id}", response_model=User)
def read_user_by_id(user_id: int, current_user: User = Depends(get_current_active_user)):
    """
    Get a specific user by id. For admins or the user themselves.
    """
    if current_user.id != user_id and current_user.role != "admin":  # Add role check if admin exists
        raise HTTPException(status_code=403, detail="Not enough permissions")

    user = db_users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User.model_validate(user)


@router.put("/me", response_model=User)
def update_user_me(user_in: UserUpdate, current_user: User = Depends(get_current_active_user)):
    """
    Update own user.
    """
    user_data = user_in.model_dump(exclude_unset=True)

    db_user = db_users.get(current_user.id)
    if not db_user:  # Should not happen if token is valid
        raise HTTPException(status_code=404, detail="User not found")

    if "password" in user_data and user_data["password"]:
        hashed_password = get_password_hash(user_data["password"])
        db_user.hashed_password = hashed_password
        del user_data["password"]

    for field, value in user_data.items():
        if hasattr(db_user, field):
            setattr(db_user, field, value)

    db_users[current_user.id] = db_user  # Update in-memory store
    return User.model_validate(db_user)