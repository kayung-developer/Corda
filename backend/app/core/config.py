# backend/app/core/config.py
import os
from dotenv import load_dotenv
from typing import List

from pydantic.v1 import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key_for_dev_only")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database (placeholder - use a real DB URL in production)
    # SQLALCHEMY_DATABASE_URL: str = "sqlite:///./test.db"
    # For in-memory demonstration:
    DATABASE_URL: str = "sqlite+aiosqlite:///./temp_db.sqlite3"


    PROJECT_NAME: str = "Ultimate Code Assistant"
    PROJECT_VERSION: str = "0.1.0"

    # Stripe (Example - replace with real keys)
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_your_stripe_publishable_key")
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "sk_test_your_stripe_secret_key")

    # PayPal (Example - replace with real credentials)
    PAYPAL_CLIENT_ID: str = os.getenv("PAYPAL_CLIENT_ID", "your_paypal_client_id")
    PAYPAL_CLIENT_SECRET: str = os.getenv("PAYPAL_CLIENT_SECRET", "your_paypal_client_secret")
    PAYPAL_MODE: str = os.getenv("PAYPAL_MODE", "sandbox") # "live" or "sandbox"

    # Crypto Payment Gateway (Example - conceptual)
    CRYPTO_API_KEY: str = os.getenv("CRYPTO_API_KEY", "your_crypto_gw_api_key")

    # Allowed origins for CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost", "http://localhost:8000"] # Add frontend URL if different

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()