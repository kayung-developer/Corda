# backend/app/api/v1/endpoints/payments.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel

from backend.app.models.user import User
from backend.app.models.subscription import SubscribeRequest, PlanName, PLANS_DETAILS
from backend.app.services.payment_service import payment_service
from backend.app.api.deps import get_current_active_user
from typing import Dict, Optional

router = APIRouter()

class PaymentInitiateResponse(BaseModel):
    message: str
    client_secret: Optional[str] = None # For Stripe PaymentIntents
    order_id: Optional[str] = None # For PayPal orders
    payment_url: Optional[str] = None # For redirect-based crypto payments


@router.post("/subscribe/{payment_gateway}", response_model=Dict[str, str])
async def subscribe_to_plan(
    payment_gateway: str, # e.g., "stripe", "paypal", "crypto"
    subscribe_request: SubscribeRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Initiate and process a subscription payment.
    `payment_method_token` depends on the gateway:
    - Stripe: PaymentMethod ID (pm_xxx) or legacy Token ID (tok_xxx)
    - PayPal: PayPal Order ID (after client-side approval)
    - Crypto: Transaction ID or reference after user makes payment
    """
    plan_id = subscribe_request.plan_id
    if plan_id not in PLANS_DETAILS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan ID")

    payment_successful = False
    if payment_gateway.lower() == "stripe":
        payment_successful = await payment_service.process_stripe_payment(
            user=current_user,
            plan_id=plan_id,
            payment_method_token=subscribe_request.payment_method_token,
            is_yearly=subscribe_request.is_yearly
        )
    elif payment_gateway.lower() == "paypal":
        payment_successful = await payment_service.process_paypal_payment(
            user=current_user,
            plan_id=plan_id,
            order_id=subscribe_request.payment_method_token, # This would be PayPal Order ID
            is_yearly=subscribe_request.is_yearly
        )
    elif payment_gateway.lower() == "crypto":
        payment_successful = await payment_service.process_crypto_payment(
            user=current_user,
            plan_id=plan_id,
            transaction_id=subscribe_request.payment_method_token, # This would be crypto TX ID
            is_yearly=subscribe_request.is_yearly
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported payment gateway")

    if payment_successful:
        updated = await payment_service.update_user_subscription(
            user_id=current_user.id,
            plan_id=plan_id,
            is_yearly=subscribe_request.is_yearly
        )
        if updated:
            return {"message": f"Successfully subscribed to {plan_id.value} plan via {payment_gateway}."}
        else: # Should not happen if user exists
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user subscription record.")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Payment processing failed with {payment_gateway}.")

# Additional endpoints could be:
# - POST /payments/stripe/create-payment-intent (to setup payment on client)
# - POST /payments/paypal/create-order (to setup PayPal order on client)
# - GET  /payments/crypto/get-address (to show user where to send crypto)
# - Webhooks for each payment provider (e.g., /webhooks/stripe, /webhooks/paypal)
#   These are crucial for robust payment processing, handling asynchronous events.