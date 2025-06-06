# backend/app/api/v1/endpoints/code_assistant.py
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.models.user import User, SubscriptionPlan
from backend.app.models.code_assistant import (
    CodeGenerationRequest, CodeGenerationResponse,
    CodeExplanationRequest, CodeExplanationResponse,
    CodeRefactorRequest, CodeRefactorResponse
)
from backend.app.services.code_assistant_service import code_assistant_service
from backend.app.api.deps import get_current_active_user
from backend.app.models.subscription import PLANS_DETAILS  # To check feature availability

router = APIRouter()


def check_feature_access(user: User, required_feature_level: int):
    """
    Helper to check if user's plan allows access to a feature.
    `required_feature_level` maps to `project_understanding_level` or similar in plan details.
    0: Basic access (e.g., Basic plan)
    1: Medium access (e.g., Premium plan)
    2: Full access (e.g., Pro plan)
    """
    user_plan_details = PLANS_DETAILS.get(SubscriptionPlan(user.subscription_plan))  # Ensure enum value is used
    if not user_plan_details:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid subscription plan.")

    # Using project_understanding_level as a proxy for feature tier for this example
    if user_plan_details.project_understanding_level < required_feature_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This feature requires a higher subscription tier. Your plan: {user.subscription_plan.value}"
        )


@router.post("/generate-code", response_model=CodeGenerationResponse)
async def generate_code_endpoint(
        request: CodeGenerationRequest,
        current_user: User = Depends(get_current_active_user)
):
    """
    Generate code based on a natural language prompt.
    """
    # Example: Basic code generation might be available to all, but advanced features within it might be tiered.
    # For simplicity, let's say Basic plan has some generation, Pro has more.
    if current_user.subscription_plan == SubscriptionPlan.NONE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Code generation requires an active subscription.")

    # Example: Tiered generation capability (e.g., model quality or context length)
    # This logic would be inside the service, but a high-level check can be here too.
    # check_feature_access(current_user, 0) # Level 0 for basic generation

    # More complex: Check rate limits from user's plan against a usage counter (not implemented here)
    # user_usage = await get_user_usage_today(current_user.id, "code_generation")
    # plan_limits = PLANS_DETAILS[current_user.subscription_plan].code_generation_limit
    # if plan_limits != -1 and user_usage >= plan_limits:
    #    raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Code generation limit reached for your plan.")

    return await code_assistant_service.generate_code(request, current_user)


@router.post("/explain-code", response_model=CodeExplanationResponse)
async def explain_code_endpoint(
        request: CodeExplanationRequest,
        current_user: User = Depends(get_current_active_user)
):
    """
    Explain a given block of code.
    """
    # Example: This feature might require at least Premium
    if current_user.subscription_plan not in [SubscriptionPlan.PREMIUM, SubscriptionPlan.PRO]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Code explanation requires a Premium or Pro plan.")
    # check_feature_access(current_user, 1) # Level 1 for explanation

    return await code_assistant_service.explain_code(request, current_user)


@router.post("/refactor-code", response_model=CodeRefactorResponse)
async def refactor_code_endpoint(
        request: CodeRefactorRequest,
        current_user: User = Depends(get_current_active_user)
):
    """
    Suggest refactorings for a given block of code.
    """
    # Example: This feature might require at least Premium
    if current_user.subscription_plan not in [SubscriptionPlan.PREMIUM, SubscriptionPlan.PRO]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Code refactoring requires a Premium or Pro plan.")
    # check_feature_access(current_user, 1) # Level 1 for refactoring

    return await code_assistant_service.refactor_code(request, current_user)

# Add more endpoints for other features:
# - Autocompletion (might need WebSockets for real-time or a different interaction model)
# - Test Generation
# - Vulnerability Detection
# - Multi-file analysis (more complex, might involve project uploads or git integrations)