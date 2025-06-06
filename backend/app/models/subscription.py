# backend/app/models/subscription.py
from pydantic import BaseModel
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime

class PlanName(str, Enum):
    BASIC = "Basic"
    PREMIUM = "Premium"
    PRO = "Pro"

class SubscriptionPlanDetail(BaseModel):
    id: PlanName
    name: str
    price_monthly: float
    price_yearly: float
    features: List[str]
    # Example limits (could be more granular)
    code_completions_limit: int  # per day or month
    code_generation_limit: int
    project_understanding_level: int # 0: none, 1: basic, 2: advanced

# Define the available plans
PLANS_DETAILS: Dict[PlanName, SubscriptionPlanDetail] = {
    PlanName.BASIC: SubscriptionPlanDetail(
        id=PlanName.BASIC,
        name="Basic Plan",
        price_monthly=9.99,
        price_yearly=99.99,
        features=[
            "AI Code Autocompletion (Standard)",
            "Code Generation from Natural Language (Limited)",
            "Contextual Awareness",
            "Documentation Suggestions",
        ],
        code_completions_limit=1000,
        code_generation_limit=50,
        project_understanding_level=0
    ),
    PlanName.PREMIUM: SubscriptionPlanDetail(
        id=PlanName.PREMIUM,
        name="Premium Plan",
        price_monthly=19.99,
        price_yearly=199.99,
        features=[
            "All Basic features",
            "AI Code Autocompletion (Advanced)",
            "Code Generation from Natural Language (Extended)",
            "Multi-file Understanding",
            "Testing Support (Basic)",
            "Refactoring Suggestions",
            "Code Explanation",
        ],
        code_completions_limit=5000,
        code_generation_limit=200,
        project_understanding_level=1
    ),
    PlanName.PRO: SubscriptionPlanDetail(
        id=PlanName.PRO,
        name="Pro Plan",
        price_monthly=49.99,
        price_yearly=499.99,
        features=[
            "All Premium features",
            "Full Project Understanding",
            "Security Vulnerability Warnings",
            "AI-driven Code Review (Beta)",
            "Priority Support",
            "Access to Future Advancements (e.g., Voice-to-Code, Custom Models)",
        ],
        code_completions_limit=-1, # Unlimited
        code_generation_limit=-1, # Unlimited
        project_understanding_level=2
    ),
}

class UserSubscriptionStatus(BaseModel):
    user_id: int
    current_plan: PlanName
    expires_at: Optional[datetime] = None
    is_active: bool

class SubscribeRequest(BaseModel):
    plan_id: PlanName
    payment_method_token: str # e.g., Stripe token, PayPal order ID
    is_yearly: bool = False