# backend/app/services/payment_service.py
from backend.app.models.subscription import SubscribeRequest, PlanName, PLANS_DETAILS
from backend.app.models.user import User, db_users # For updating user subscription
from backend.app.core.config import settings
from datetime import datetime, timedelta, timezone


# import stripe # Uncomment and configure if using Stripe

class PaymentService:
    def __init__(self):
        # stripe.api_key = settings.STRIPE_SECRET_KEY # Uncomment for Stripe
        pass

    async def process_stripe_payment(self, user: User, plan_id: PlanName, payment_method_token: str, is_yearly: bool) -> bool:
        # --- THIS IS WHERE REAL STRIPE INTEGRATION WOULD HAPPEN ---
        # 1. Create a Stripe Customer if not exists (user.stripe_customer_id)
        # 2. Create a Stripe Subscription or PaymentIntent
        #    - Get price_id from PLANS_DETAILS (you'd map these to Stripe Price IDs)
        #    - plan_detail = PLANS_DETAILS[plan_id]
        #    - amount = plan_detail.price_yearly if is_yearly else plan_detail.price_monthly
        #    - currency = "usd"
        #    - try:
        #          payment_intent = stripe.PaymentIntent.create(
        #              amount=int(amount * 100), # Stripe expects cents
        #              currency=currency,
        #              customer=user.stripe_customer_id, # Or create customer
        #              payment_method=payment_method_token, # If it's a payment method ID
        #              off_session=True, # If charging saved card
        #              confirm=True,
        #          )
        #          if payment_intent.status == 'succeeded':
        #              return True
        #      except stripe.error.StripeError as e:
        #          print(f"Stripe error: {e}")
        #          return False
        # ------------------------------------------------------------------
        print(f"Simulating Stripe payment for user {user.email}, plan {plan_id.value}, token {payment_method_token}")
        if "tok_visa" in payment_method_token or "pm_" in payment_method_token : # Simulate success for valid-looking test tokens
            return True
        return False # Simulate failure for others

    async def process_paypal_payment(self, user: User, plan_id: PlanName, order_id: str, is_yearly: bool) -> bool:
        # --- THIS IS WHERE REAL PAYPAL INTEGRATION WOULD HAPPEN ---
        # 1. Verify PayPal order_id with PayPal API (capture payment)
        #    - Use PayPal SDK or direct HTTP calls to PayPal API
        #    - headers = {"Authorization": f"Bearer {get_paypal_access_token()}"}
        #    - response = requests.post(f"{paypal_api_base}/v2/checkout/orders/{order_id}/capture", headers=headers)
        #    - if response.status_code == 201 and response.json()['status'] == 'COMPLETED':
        #          return True
        # ------------------------------------------------------------------
        print(f"Simulating PayPal payment capture for user {user.email}, plan {plan_id.value}, order_id {order_id}")
        if order_id.startswith("PAYPAL_ORDER_"): # Simulate success
            return True
        return False

    async def process_crypto_payment(self, user: User, plan_id: PlanName, transaction_id: str, is_yearly: bool) -> bool:
        # --- THIS IS WHERE REAL CRYPTO PAYMENT GATEWAY INTEGRATION WOULD HAPPEN ---
        # 1. Verify transaction_id with the crypto payment gateway's API
        #    - Check if transaction is confirmed on the blockchain
        #    - Ensure the correct amount was paid to your wallet address
        # ------------------------------------------------------------------
        print(f"Simulating Crypto payment verification for user {user.email}, plan {plan_id.value}, tx_id {transaction_id}")
        if transaction_id.startswith("CRYPTO_TX_"): # Simulate success
            return True
        return False

    async def update_user_subscription(self, user_id: int, plan_id: PlanName, is_yearly: bool):
        # This would update the user's record in a real database
        user_in_db = db_users.get(user_id)
        if user_in_db:
            user_in_db.subscription_plan = plan_id
            expiry_duration = timedelta(days=365) if is_yearly else timedelta(days=30)
            user_in_db.subscription_expires_at = datetime.now(timezone.utc) + expiry_duration
            print(f"User {user_id} subscription updated to {plan_id.value}, expires {user_in_db.subscription_expires_at}")
            return True
        return False

payment_service = PaymentService()