from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional, List
import logging

from open_webui.models.subscriptions import (
    SubscriptionPlans,
    UserSubscriptions,
    CreatePlanForm,
    UpdatePlanForm,
    CreateSubscriptionForm,
    UpdateSubscriptionForm,
    SubscriptionPlanModel,
    UserSubscriptionModel,
)
from open_webui.models.users import Users
from open_webui.models.groups import Groups, GroupForm
from open_webui.models.models import Models
from open_webui.utils.auth import get_verified_user, get_admin_user

log = logging.getLogger(__name__)

router = APIRouter()

############################
# Subscription Plans
############################


@router.get("/plans", response_model=List[SubscriptionPlanModel])
async def get_all_plans():
    """Get all active subscription plans (public endpoint)"""
    try:
        plans = SubscriptionPlans.get_all_active_plans()
        return plans
    except Exception as e:
        log.error(f"Error getting plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription plans",
        )


@router.get("/plans/all", response_model=List[SubscriptionPlanModel])
async def get_all_plans_admin(user=Depends(get_admin_user)):
    """Get all subscription plans including inactive (admin only)"""
    try:
        plans = SubscriptionPlans.get_all_plans()
        return plans
    except Exception as e:
        log.error(f"Error getting plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription plans",
        )


@router.get("/plans/{plan_id}", response_model=SubscriptionPlanModel)
async def get_plan_by_id(plan_id: str):
    """Get a specific subscription plan by ID"""
    try:
        plan = SubscriptionPlans.get_plan_by_id(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription plan not found",
            )
        return plan
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription plan",
        )


@router.post("/plans", response_model=SubscriptionPlanModel)
async def create_plan(form_data: CreatePlanForm, user=Depends(get_admin_user)):
    """Create a new subscription plan (admin only)"""
    try:
        # Step 1: Create a group with the same name as the plan
        group_form = GroupForm(
            name=form_data.plan_name,
            description=f"Group for {form_data.plan_name} plan subscribers"
        )
        group = Groups.insert_new_group(user.id, group_form)
        
        if not group:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create group for plan",
            )
        
        # Step 2: Create the plan with the group ID
        plan_data_dict = form_data.model_dump()
        plan_data_dict['group'] = group.id
        
        # Step 3: Create the plan
        plan_form_with_group = CreatePlanForm(**plan_data_dict)
        plan = SubscriptionPlans.create_plan(plan_form_with_group)
        
        # Step 4: If models are selected, add the group to each model's access_control
        if form_data.models and len(form_data.models) > 0:
            from open_webui.models.models import ModelForm
            import copy
            
            for model_id in form_data.models:
                model = Models.get_model_by_id(model_id)
                if not model:
                    # Create the model in the database if it doesn't exist
                    try:
                        model_form = ModelForm(
                            id=model_id,
                            base_model_id=None,
                            name=model_id,
                            meta={
                                "profile_image_url": "/static/favicon.png",
                                "description": f"Model {model_id}",
                                "capabilities": {}
                            },
                            params={},
                            access_control={"read": {"group_ids": [], "user_ids": []}},
                            is_active=True
                        )
                        model = Models.insert_new_model(model_form, user.id)
                        if not model:
                            continue
                    except Exception:
                        continue
                
                # Deep copy existing access_control or initialize it
                access_control = copy.deepcopy(model.access_control) if model.access_control else {}
                
                # Initialize read permissions if not exists
                if "read" not in access_control:
                    access_control["read"] = {"group_ids": [], "user_ids": []}
                
                # Ensure group_ids is a list
                if "group_ids" not in access_control["read"]:
                    access_control["read"]["group_ids"] = []
                elif not isinstance(access_control["read"]["group_ids"], list):
                    access_control["read"]["group_ids"] = []
                
                # Add group_id to read permissions if not already there
                if group.id not in access_control["read"]["group_ids"]:
                    access_control["read"]["group_ids"].append(group.id)
                
                # Update the model with new access_control
                model_form = ModelForm(
                    id=model.id,
                    base_model_id=model.base_model_id,
                    name=model.name,
                    meta=model.meta,
                    params=model.params,
                    access_control=access_control,
                    is_active=model.is_active
                )
                
                Models.update_model_by_id(model.id, model_form)
        
        return plan
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error creating plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subscription plan: {str(e)}",
        )


@router.patch("/plans/{plan_id}", response_model=SubscriptionPlanModel)
async def update_plan(
    plan_id: str, form_data: UpdatePlanForm, user=Depends(get_admin_user)
):
    """Update a subscription plan (admin only)"""
    try:
        # Get the existing plan
        existing_plan = SubscriptionPlans.get_plan_by_id(plan_id)
        if not existing_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription plan not found",
            )
        
        # Handle model changes if models field is being updated
        if form_data.models is not None:
            import copy
            from open_webui.models.models import ModelForm
            
            # Check if group exists, if not create it
            group_id = existing_plan.group
            if group_id:
                # Verify the group still exists
                group = Groups.get_group_by_id(group_id)
                if not group:
                    # Group was deleted, create a new one
                    group_form = GroupForm(
                        name=existing_plan.plan_name,
                        description=f"Group for {existing_plan.plan_name} plan subscribers"
                    )
                    group = Groups.insert_new_group(user.id, group_form)
                    if group:
                        group_id = group.id
                        # Store new group ID in form_data so it gets saved with the main update
                        form_data.group = group_id
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to recreate group for plan",
                        )
            else:
                # No group assigned, create one
                group_form = GroupForm(
                    name=existing_plan.plan_name,
                    description=f"Group for {existing_plan.plan_name} plan subscribers"
                )
                group = Groups.insert_new_group(user.id, group_form)
                if group:
                    group_id = group.id
                    # Store new group ID in form_data so it gets saved with the main update
                    form_data.group = group_id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create group for plan",
                    )
            old_models = set(existing_plan.models or [])
            new_models = set(form_data.models)
            
            # Models to remove access from
            models_to_remove = old_models - new_models
            
            # Remove group from models that are no longer selected
            for model_id in models_to_remove:
                model = Models.get_model_by_id(model_id)
                if model and model.access_control:
                    access_control = copy.deepcopy(model.access_control)
                    if "read" in access_control and "group_ids" in access_control["read"]:
                        if group_id in access_control["read"]["group_ids"]:
                            access_control["read"]["group_ids"].remove(group_id)
                            
                            model_form = ModelForm(
                                id=model.id,
                                base_model_id=model.base_model_id,
                                name=model.name,
                                meta=model.meta,
                                params=model.params,
                                access_control=access_control,
                                is_active=model.is_active
                            )
                            Models.update_model_by_id(model.id, model_form)
            
            # Check ALL selected models and ensure group is added
            for model_id in new_models:
                model = Models.get_model_by_id(model_id)
                if not model:
                    # Create the model in the database if it doesn't exist
                    try:
                        model_form = ModelForm(
                            id=model_id,
                            base_model_id=None,
                            name=model_id,
                            meta={
                                "profile_image_url": "/static/favicon.png",
                                "description": f"Model {model_id}",
                                "capabilities": {}
                            },
                            params={},
                            access_control={"read": {"group_ids": [], "user_ids": []}},
                            is_active=True
                        )
                        model = Models.insert_new_model(model_form, user.id)
                        if not model:
                            continue
                    except Exception:
                        continue
                
                # Deep copy existing access_control or initialize it
                access_control = copy.deepcopy(model.access_control) if model.access_control else {}
                
                if "read" not in access_control:
                    access_control["read"] = {"group_ids": [], "user_ids": []}
                
                if "group_ids" not in access_control["read"]:
                    access_control["read"]["group_ids"] = []
                elif not isinstance(access_control["read"]["group_ids"], list):
                    access_control["read"]["group_ids"] = []
                
                if group_id not in access_control["read"]["group_ids"]:
                    access_control["read"]["group_ids"].append(group_id)
                
                model_form = ModelForm(
                    id=model.id,
                    base_model_id=model.base_model_id,
                    name=model.name,
                    meta=model.meta,
                    params=model.params,
                    access_control=access_control,
                    is_active=model.is_active
                )
                Models.update_model_by_id(model.id, model_form)
        
        # Update the plan
        plan = SubscriptionPlans.update_plan(plan_id, form_data)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription plan not found",
            )
        return plan
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error updating plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subscription plan",
        )


@router.delete("/plans/{plan_id}")
async def delete_plan(plan_id: str, user=Depends(get_admin_user)):
    """Delete a subscription plan (admin only)"""
    try:
        # Get the plan to retrieve group and models info
        plan = SubscriptionPlans.get_plan_by_id(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription plan not found",
            )
        
        # Remove group from all associated models before deleting
        if plan.group and plan.models:
            for model_id in plan.models:
                model = Models.get_model_by_id(model_id)
                if model and model.access_control:
                    access_control = model.access_control
                    if "read" in access_control and "group_ids" in access_control["read"]:
                        if plan.group in access_control["read"]["group_ids"]:
                            access_control["read"]["group_ids"].remove(plan.group)
                            
                            from open_webui.models.models import ModelForm
                            model_form = ModelForm(
                                id=model.id,
                                base_model_id=model.base_model_id,
                                name=model.name,
                                meta=model.meta,
                                params=model.params,
                                access_control=access_control,
                                is_active=model.is_active
                            )
                            Models.update_model_by_id(model.id, model_form)
        
        # Delete the associated group if it exists
        if plan.group:
            Groups.delete_group_by_id(plan.group)
        
        # Delete the plan
        success = SubscriptionPlans.delete_plan(plan_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription plan not found",
            )
        return {"success": True, "message": "Plan deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error deleting plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete subscription plan",
        )


############################
# User Subscriptions
############################


@router.get("/user/subscription", response_model=Optional[UserSubscriptionModel])
async def get_user_subscription(user=Depends(get_verified_user)):
    """Get the current user's subscription"""
    try:
        subscription = UserSubscriptions.get_user_subscription(user.id)
        return subscription
    except Exception as e:
        log.error(f"Error getting user subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription",
        )


@router.post("/user/subscription", response_model=UserSubscriptionModel)
async def create_user_subscription(
    form_data: CreateSubscriptionForm, user=Depends(get_verified_user)
):
    """Create a subscription for the current user"""
    try:
        # Verify the plan exists
        plan = SubscriptionPlans.get_plan_by_id(form_data.plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription plan not found",
            )

        # Create the subscription
        subscription = UserSubscriptions.create_subscription(user.id, form_data)

        # Add user to the plan's users array
        SubscriptionPlans.add_user_to_plan(plan.id, user.id)

        # Add user to the plan's group if the group exists
        if plan.group:
            group = Groups.get_group_by_id(plan.group)
            if group:
                Groups.add_users_to_group(plan.group, [user.id])
            else:
                log.warning(f"Plan {plan.id} has group {plan.group} but group does not exist")

        # Update user's subscription info
        Users.update_user_by_id(
            user.id,
            {
                "subscription_id": subscription.id,
                "subscription_status": subscription.status,
            },
        )

        return subscription
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error creating subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription",
        )


@router.post("/verify-payment")
async def verify_payment(
    payment_id: str,
    subscription_id: str,
    payment_method: str = "stripe",
):
    """
    Verify payment and activate subscription.
    This is a placeholder - integrate with actual payment gateway (Stripe, PayPal, etc.)
    """
    try:
        # TODO: Implement actual payment verification with payment gateway
        # For now, this is a mock implementation
        
        # Example Stripe verification:
        # import stripe
        # stripe.api_key = "your_stripe_secret_key"
        # payment_intent = stripe.PaymentIntent.retrieve(payment_id)
        # if payment_intent.status == "succeeded":
        #     # Activate subscription
        
        subscription = UserSubscriptions.get_subscription_by_id(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )

        # Get plan to determine duration
        plan = SubscriptionPlans.get_plan_by_id(subscription.plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription plan not found",
            )

        # Calculate duration based on interval
        duration_days = 30 if plan.interval == "month" else 365 if plan.interval == "year" else 36500

        # Update subscription with payment info and activate
        update_form = UpdateSubscriptionForm(
            status="active",
            payment_id=payment_id,
        )
        UserSubscriptions.update_subscription(subscription_id, update_form)
        activated_subscription = UserSubscriptions.activate_subscription(
            subscription_id, duration_days
        )

        # Add user to the plan's users array if not already added
        SubscriptionPlans.add_user_to_plan(plan.id, subscription.user_id)

        # Add user to the plan's group if the group exists
        if plan.group:
            group = Groups.get_group_by_id(plan.group)
            if group:
                Groups.add_users_to_group(plan.group, [subscription.user_id])
            else:
                log.warning(f"Plan {plan.id} has group {plan.group} but group does not exist")

        # Update user's subscription status
        Users.update_user_by_id(
            subscription.user_id,
            {"subscription_status": "active"},
        )

        return {
            "success": True,
            "message": "Payment verified and subscription activated",
            "subscription": activated_subscription,
        }
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error verifying payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify payment",
        )


@router.patch("/subscription/{subscription_id}", response_model=UserSubscriptionModel)
async def update_subscription(
    subscription_id: str,
    form_data: UpdateSubscriptionForm,
    user=Depends(get_admin_user),
):
    """Update a subscription (admin only)"""
    try:
        # Get the subscription before update
        existing_subscription = UserSubscriptions.get_subscription_by_id(subscription_id)
        if not existing_subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )

        # Update the subscription
        subscription = UserSubscriptions.update_subscription(subscription_id, form_data)

        # Update user's subscription status if changed
        if form_data.status:
            Users.update_user_by_id(
                subscription.user_id,
                {"subscription_status": form_data.status},
            )

            # If subscription is cancelled or expired, remove user from plan and group
            if form_data.status in ["cancelled", "expired"]:
                plan = SubscriptionPlans.get_plan_by_id(subscription.plan_id)
                if plan:
                    # Remove user from plan's users array
                    SubscriptionPlans.remove_user_from_plan(plan.id, subscription.user_id)
                    
                    # Remove user from plan's group
                    if plan.group:
                        group = Groups.get_group_by_id(plan.group)
                        if group:
                            Groups.remove_users_from_group(plan.group, [subscription.user_id])

            # If subscription is activated, add user to plan and group
            elif form_data.status == "active" and existing_subscription.status != "active":
                plan = SubscriptionPlans.get_plan_by_id(subscription.plan_id)
                if plan:
                    # Add user to plan's users array
                    SubscriptionPlans.add_user_to_plan(plan.id, subscription.user_id)
                    
                    # Add user to plan's group
                    if plan.group:
                        group = Groups.get_group_by_id(plan.group)
                        if group:
                            Groups.add_users_to_group(plan.group, [subscription.user_id])

        return subscription
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error updating subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subscription",
        )
