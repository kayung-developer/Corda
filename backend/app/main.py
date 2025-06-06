# backend/app/main.py
import sys
import os

import uvicorn

# --- Start of Aggressive Debugging ---
print(f"--- DEBUG: main.py execution started ---")
print(f"Initial __file__: {os.path.abspath(__file__)}")
print(f"Initial os.getcwd(): {os.getcwd()}") # Current working directory when uvicorn starts this script
print(f"Initial sys.path (first 5 entries): {sys.path[:5]}")

# Determine the project root directory ("Corda")
# __file__ is Corda/backend/app/main.py
# We need to go up two levels from 'app' to get to 'Corda'
path_to_app_dir = os.path.dirname(os.path.abspath(__file__)) # Corda/backend/app
path_to_backend_dir = os.path.dirname(path_to_app_dir)     # Corda/backend
PROJECT_ROOT = os.path.dirname(path_to_backend_dir)        # Corda

print(f"--- DEBUG: Calculated PROJECT_ROOT: {PROJECT_ROOT} ---")

# Ensure PROJECT_ROOT is at the beginning of sys.path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    print(f"--- DEBUG: PROJECT_ROOT ({PROJECT_ROOT}) was INSERTED into sys.path ---")
else:
    # If it's already there, ensure it's at the front for priority
    sys.path.remove(PROJECT_ROOT)
    sys.path.insert(0, PROJECT_ROOT)
    print(f"--- DEBUG: PROJECT_ROOT ({PROJECT_ROOT}) was MOVED to the front of sys.path ---")

print(f"--- DEBUG: Modified sys.path (first 5 entries): {sys.path[:5]} ---")
print(f"--- DEBUG: Full modified sys.path: {sys.path} ---")
print(f"--- DEBUG: Attempting to import project modules using 'from backend.app...' ---")
# --- End of Aggressive Debugging ---

# Now try the imports with the modified sys.path
try:
    from backend.app.core.config import settings
    print("--- DEBUG: Successfully imported 'backend.app.core.config.settings' ---")
    from backend.app.api.v1.api import api_router
    print("--- DEBUG: Successfully imported 'backend.app.api.v1.api.api_router' ---")
    from backend.app.models.user import UserInDB, UserRole, SubscriptionPlan, db_users, user_id_counter, User
    print("--- DEBUG: Successfully imported 'backend.app.models.user' modules ---")
    from backend.app.core.security import get_password_hash
    print("--- DEBUG: Successfully imported 'backend.app.core.security.get_password_hash' ---")
except ImportError as e:
    print(f"--- DEBUG: !!! IMPORT ERROR OCCURRED !!! ---")
    print(f"--- DEBUG: Error message: {e} ---")
    print(f"--- DEBUG: sys.path at time of error: {sys.path} ---")
    print(f"--- DEBUG: os.getcwd() at time of error: {os.getcwd()} ---")

    # Check if 'backend' directory exists where expected by PROJECT_ROOT
    expected_backend_path = os.path.join(PROJECT_ROOT, "backend")
    print(f"--- DEBUG: Checking for 'backend' directory at: {expected_backend_path} ---")
    print(f"--- DEBUG: Does '{expected_backend_path}' exist? {os.path.isdir(expected_backend_path)} ---")
    if os.path.isdir(expected_backend_path):
        print(f"--- DEBUG: Contents of '{expected_backend_path}': {os.listdir(expected_backend_path)} ---")
        # Check for __init__.py in backend
        backend_init_py = os.path.join(expected_backend_path, "__init__.py")
        print(f"--- DEBUG: Does '{backend_init_py}' exist? {os.path.isfile(backend_init_py)} ---")

        expected_app_path = os.path.join(expected_backend_path, "app")
        print(f"--- DEBUG: Checking for 'backend/app' directory at: {expected_app_path} ---")
        print(f"--- DEBUG: Does '{expected_app_path}' exist? {os.path.isdir(expected_app_path)} ---")
        if os.path.isdir(expected_app_path):
            print(f"--- DEBUG: Contents of '{expected_app_path}': {os.listdir(expected_app_path)} ---")
            app_init_py = os.path.join(expected_app_path, "__init__.py")
            print(f"--- DEBUG: Does '{app_init_py}' exist? {os.path.isfile(app_init_py)} ---")
    else:
        print(f"--- DEBUG: CRITICAL - 'backend' directory NOT FOUND at expected PROJECT_ROOT subpath. ---")

    raise # Re-raise the import error to stop execution if it occurs

# If imports were successful, continue with FastAPI app setup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone

print("--- DEBUG: All project imports successful. Proceeding with FastAPI app setup. ---")


if not db_users: # Add a default user if store is empty
    hashed_password = get_password_hash("string")
    db_users[user_id_counter] = UserInDB(
        id=user_id_counter,
        email="user@example.com",
        full_name="Test User",
        hashed_password=hashed_password,
        is_active=True,
        role=UserRole.USER,
        subscription_plan=SubscriptionPlan.PRO,
        subscription_expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    user_id_counter += 1
    db_users[user_id_counter] = UserInDB(
        id=user_id_counter,
        email="basic@example.com",
        full_name="Basic User",
        hashed_password=get_password_hash("basicpass"),
        is_active=True,
        role=UserRole.USER,
        subscription_plan=SubscriptionPlan.BASIC,
        subscription_expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    user_id_counter += 1


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version=settings.PROJECT_VERSION,
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

print("--- DEBUG: FastAPI app configured. Uvicorn should be serving now. ---")
#uvicorn backend.app.main:app --reload princelillwitty@gmail.com