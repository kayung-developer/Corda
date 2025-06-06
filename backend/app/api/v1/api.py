# backend/app/api/v1/api.py
from fastapi import APIRouter

# Corrected line in backend/app/api/v1/api.py
from backend.app.api.v1.endpoints import (
    auth,
    users,
    subscriptions,
    payments,
    code_assistant
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(code_assistant.router, prefix="/assist", tags=["Code Assistant"])