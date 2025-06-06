# backend/app/api/v1/endpoints/subscriptions.py
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict

from backend.app.models.subscription import SubscriptionPlanDetail, PLANS_DETAILS, UserSubscriptionStatus, PlanName
from backend.app.models.user import User, db_users
from backend.app.api.deps import get_current_active_user

router = APIRouter()


@router.get("/plans", response_model=List[SubscriptionPlanDetail])
async def list_subscription_plans():
    """
    Get available subscription plans.
    """
    return list(PLANS_DETAILS.values())


@router.get("/status", response_model=UserSubscriptionStatus)
async def get_user_subscription_status(current_user: User = Depends(get_current_active_user)):
    """
    Get the current user's subscription status.
    """
    # In a real app, this data comes from the user's record in the database
    is_active_subscription = False
    if current_user.subscription_expires_at:
        is_active_subscription = current_user.subscription_expires_at > datetime.now(timezone.utc)

    return UserSubscriptionStatus(
        user_id=current_user.id,
        current_plan=current_user.subscription_plan,
        expires_at=current_user.subscription_expires_at,
        is_active=is_active_subscription
    )


# Note: Actual subscription creation/cancellation would be tied to payment processing.
# This endpoint is illustrative. A POST to /payments/subscribe would handle the change.

@router.post("/cancel", response_model=Dict[str, str])
async def cancel_subscription(current_user: User = Depends(get_current_active_user)):
    """
    Cancel user's current subscription (conceptual).
    In a real system, this would:
    1. Mark the subscription to not renew with the payment provider (e.g., Stripe).
    2. Update the local user record's subscription_plan to 'none' or set an expiry.
    """
    # Placeholder logic for in-memory user store
    user_in_db = db_users.get(current_user.id)
    if user_in_db:
        if user_in_db.subscription_plan != PlanName.NONE:
            # For simplicity, set to None immediately. Real world: set to expire at end of current period.
            print(f"User {current_user.email} cancelling plan {user_in_db.subscription_plan.value}.")
            # user_in_db.subscription_plan = PlanName.NONE
            # user_in_db.subscription_expires_at = None # Or keep expiry for prorated access
            # This should communicate with payment provider (e.g., stripe.Subscription.cancel)
            return {
                "message": f"Subscription {user_in_db.subscription_plan.value} cancellation process initiated. Access remains until {user_in_db.subscription_expires_at}."}
        else:
            return {"message": "No active subscription to cancel."}

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")