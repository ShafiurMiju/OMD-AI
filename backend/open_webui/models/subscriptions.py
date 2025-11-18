import time
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, String, Text, BigInteger, Float, Boolean, JSON
from open_webui.internal.db import Base, JSONField, get_db

####################
# Subscription Plan DB Schema
####################


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plan"

    id = Column(String, primary_key=True)
    plan_name = Column(String, nullable=False)  # planName
    subtitle = Column(Text, nullable=True)
    plan_type = Column(String, default="premium")  # planType: premium, free, enterprise
    duration_type = Column(String, default="months")  # durationType: days, weeks, months, years
    plan_duration = Column(BigInteger, default=1)  # planDuration: number value
    price = Column(Float, nullable=False)
    benefits = Column(JSONField, nullable=True)  # Array of benefit strings
    additional_info = Column(Text, nullable=True)  # additionalInfo
    group = Column(String, nullable=True)  # group ID
    models = Column(JSONField, nullable=True)  # Array of model IDs
    users = Column(JSONField, nullable=True)  # Array of user IDs subscribed to this plan
    is_active = Column(Boolean, default=True)
    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class UserSubscription(Base):
    __tablename__ = "user_subscription"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    plan_id = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, active, expired, cancelled
    payment_id = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)  # stripe, paypal, etc.
    start_date = Column(BigInteger, nullable=True)
    end_date = Column(BigInteger, nullable=True)
    auto_renew = Column(Boolean, default=True)
    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


####################
# Pydantic Models
####################


class SubscriptionPlanModel(BaseModel):
    id: str
    plan_name: str
    subtitle: Optional[str] = None
    plan_type: str = "premium"
    duration_type: str = "months"
    plan_duration: int = 1
    price: float
    benefits: Optional[List[str]] = None
    additional_info: Optional[str] = None
    group: Optional[str] = None
    models: Optional[List[str]] = None
    users: Optional[List[str]] = None
    is_active: bool = True
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


class UserSubscriptionModel(BaseModel):
    id: str
    user_id: str
    plan_id: str
    status: str = "pending"
    payment_id: Optional[str] = None
    payment_method: Optional[str] = None
    start_date: Optional[int] = None
    end_date: Optional[int] = None
    auto_renew: bool = True
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


####################
# Forms
####################


class CreatePlanForm(BaseModel):
    plan_name: str
    subtitle: Optional[str] = None
    plan_type: str = "premium"
    duration_type: str = "months"
    plan_duration: int = 1
    price: float
    benefits: Optional[List[str]] = None
    additional_info: Optional[str] = None
    group: Optional[str] = None
    models: Optional[List[str]] = None


class UpdatePlanForm(BaseModel):
    plan_name: Optional[str] = None
    subtitle: Optional[str] = None
    plan_type: Optional[str] = None
    duration_type: Optional[str] = None
    plan_duration: Optional[int] = None
    price: Optional[float] = None
    benefits: Optional[List[str]] = None
    additional_info: Optional[str] = None
    group: Optional[str] = None
    models: Optional[List[str]] = None
    users: Optional[List[str]] = None
    is_active: Optional[bool] = None


class CreateSubscriptionForm(BaseModel):
    plan_id: str
    payment_id: Optional[str] = None
    payment_method: Optional[str] = None


class UpdateSubscriptionForm(BaseModel):
    status: Optional[str] = None
    payment_id: Optional[str] = None
    end_date: Optional[int] = None
    auto_renew: Optional[bool] = None


####################
# SubscriptionPlans Table
####################


class SubscriptionPlansTable:
    def __init__(self, db):
        self.db = db

    def create_plan(self, form_data: CreatePlanForm) -> Optional[SubscriptionPlanModel]:
        with get_db() as db:
            import uuid

            plan_id = str(uuid.uuid4())
            timestamp = int(time.time())

            plan = SubscriptionPlan(
                id=plan_id,
                plan_name=form_data.plan_name,
                subtitle=form_data.subtitle,
                plan_type=form_data.plan_type,
                duration_type=form_data.duration_type,
                plan_duration=form_data.plan_duration,
                price=form_data.price,
                benefits=form_data.benefits,
                additional_info=form_data.additional_info,
                group=form_data.group,
                models=form_data.models,
                is_active=True,
                created_at=timestamp,
                updated_at=timestamp,
            )

            db.add(plan)
            db.commit()
            db.refresh(plan)

            return SubscriptionPlanModel.model_validate(plan)

    def get_plan_by_id(self, plan_id: str) -> Optional[SubscriptionPlanModel]:
        with get_db() as db:
            plan = db.query(SubscriptionPlan).filter_by(id=plan_id).first()
            return SubscriptionPlanModel.model_validate(plan) if plan else None

    def get_all_active_plans(self) -> List[SubscriptionPlanModel]:
        with get_db() as db:
            plans = db.query(SubscriptionPlan).filter_by(is_active=True).all()
            return [SubscriptionPlanModel.model_validate(plan) for plan in plans]

    def get_all_plans(self) -> List[SubscriptionPlanModel]:
        with get_db() as db:
            plans = db.query(SubscriptionPlan).all()
            return [SubscriptionPlanModel.model_validate(plan) for plan in plans]

    def update_plan(
        self, plan_id: str, form_data: UpdatePlanForm
    ) -> Optional[SubscriptionPlanModel]:
        with get_db() as db:
            plan = db.query(SubscriptionPlan).filter_by(id=plan_id).first()
            if not plan:
                return None

            update_data = form_data.model_dump(exclude_none=True)
            for key, value in update_data.items():
                setattr(plan, key, value)

            plan.updated_at = int(time.time())
            db.commit()
            db.refresh(plan)

            return SubscriptionPlanModel.model_validate(plan)

    def delete_plan(self, plan_id: str) -> bool:
        with get_db() as db:
            plan = db.query(SubscriptionPlan).filter_by(id=plan_id).first()
            if plan:
                db.delete(plan)
                db.commit()
                return True
            return False

    def add_user_to_plan(
        self, plan_id: str, user_id: str
    ) -> Optional[SubscriptionPlanModel]:
        """Add a user to the plan's users array"""
        with get_db() as db:
            plan = db.query(SubscriptionPlan).filter_by(id=plan_id).first()
            if not plan:
                return None

            # Initialize users array if it doesn't exist
            if not plan.users or not isinstance(plan.users, list):
                plan.users = []

            # Add user if not already in the list
            if user_id not in plan.users:
                plan.users = plan.users + [user_id]  # Create new list to trigger update
                plan.updated_at = int(time.time())
                db.commit()
                db.refresh(plan)

            return SubscriptionPlanModel.model_validate(plan)

    def remove_user_from_plan(
        self, plan_id: str, user_id: str
    ) -> Optional[SubscriptionPlanModel]:
        """Remove a user from the plan's users array"""
        with get_db() as db:
            plan = db.query(SubscriptionPlan).filter_by(id=plan_id).first()
            if not plan:
                return None

            # Remove user if exists in the list
            if plan.users and isinstance(plan.users, list) and user_id in plan.users:
                plan.users = [uid for uid in plan.users if uid != user_id]
                plan.updated_at = int(time.time())
                db.commit()
                db.refresh(plan)

            return SubscriptionPlanModel.model_validate(plan)


####################
# UserSubscriptions Table
####################


class UserSubscriptionsTable:
    def __init__(self, db):
        self.db = db

    def create_subscription(
        self, user_id: str, form_data: CreateSubscriptionForm
    ) -> Optional[UserSubscriptionModel]:
        with get_db() as db:
            import uuid

            subscription_id = str(uuid.uuid4())
            timestamp = int(time.time())

            subscription = UserSubscription(
                id=subscription_id,
                user_id=user_id,
                plan_id=form_data.plan_id,
                status="pending",
                payment_id=form_data.payment_id,
                payment_method=form_data.payment_method,
                created_at=timestamp,
                updated_at=timestamp,
            )

            db.add(subscription)
            db.commit()
            db.refresh(subscription)

            return UserSubscriptionModel.model_validate(subscription)

    def get_user_subscription(self, user_id: str) -> Optional[UserSubscriptionModel]:
        with get_db() as db:
            subscription = (
                db.query(UserSubscription)
                .filter_by(user_id=user_id)
                .order_by(UserSubscription.created_at.desc())
                .first()
            )
            return (
                UserSubscriptionModel.model_validate(subscription)
                if subscription
                else None
            )

    def get_subscription_by_id(
        self, subscription_id: str
    ) -> Optional[UserSubscriptionModel]:
        with get_db() as db:
            subscription = (
                db.query(UserSubscription).filter_by(id=subscription_id).first()
            )
            return (
                UserSubscriptionModel.model_validate(subscription)
                if subscription
                else None
            )

    def update_subscription(
        self, subscription_id: str, form_data: UpdateSubscriptionForm
    ) -> Optional[UserSubscriptionModel]:
        with get_db() as db:
            subscription = (
                db.query(UserSubscription).filter_by(id=subscription_id).first()
            )
            if not subscription:
                return None

            update_data = form_data.model_dump(exclude_none=True)
            for key, value in update_data.items():
                setattr(subscription, key, value)

            subscription.updated_at = int(time.time())
            db.commit()
            db.refresh(subscription)

            return UserSubscriptionModel.model_validate(subscription)

    def activate_subscription(
        self, subscription_id: str, duration_days: int = 30
    ) -> Optional[UserSubscriptionModel]:
        with get_db() as db:
            subscription = (
                db.query(UserSubscription).filter_by(id=subscription_id).first()
            )
            if not subscription:
                return None

            timestamp = int(time.time())
            subscription.status = "active"
            subscription.start_date = timestamp
            subscription.end_date = timestamp + (duration_days * 24 * 60 * 60)
            subscription.updated_at = timestamp

            db.commit()
            db.refresh(subscription)

            return UserSubscriptionModel.model_validate(subscription)


# Initialize tables
SubscriptionPlans = SubscriptionPlansTable(get_db())
UserSubscriptions = UserSubscriptionsTable(get_db())
