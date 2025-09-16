from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from django.utils import timezone

from .models import SubscriptionLimit, UserSubscription, DailyUsage  # type: ignore


@dataclass
class LimitInfo:
    daily_ai_requests: int
    is_premium: bool


def get_user_subscription(user) -> Optional[UserSubscription]:
    try:
        return getattr(user, 'subscription', None)
    except Exception:
        return None


def get_limits_for_user(user) -> LimitInfo:
    sub = get_user_subscription(user)
    if sub and sub.is_active and sub.subscription_type == 'premium':
        limits = SubscriptionLimit.get_limits('premium')  # type: ignore
        return LimitInfo(daily_ai_requests=limits.daily_ai_requests, is_premium=True)  # type: ignore
    limits = SubscriptionLimit.get_limits('free')  # type: ignore
    return LimitInfo(daily_ai_requests=limits.daily_ai_requests, is_premium=False)  # type: ignore


def can_user_make_ai_request(user) -> bool:
    limits = get_limits_for_user(user)
    if limits.is_premium:
        return True
    today_usage = DailyUsage.get_today_usage(user)  # type: ignore
    return today_usage.ai_requests_count < limits.daily_ai_requests  # type: ignore


def increment_user_ai_usage(user) -> None:
    usage = DailyUsage.get_today_usage(user)  # type: ignore
    usage.ai_requests_count += 1  # type: ignore
    usage.updated_at = timezone.now()
    usage.save()
