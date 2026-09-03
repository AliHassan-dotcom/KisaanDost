"""Endpoints for Notification Preferences, In-App Alerts Inbox, Unread Count, and Background Rule Evaluation."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query

from app.backend.schemas import (
    NotificationMarkReadRequest,
    NotificationPreferencesUpdateRequest,
)
from app.backend.services.notification_service import NotificationService, get_notification_service
from app.security.auth import get_current_user_optional

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/preferences")
async def get_preferences(
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    """Return user's notification channel preferences and alert thresholds."""
    user_id = current_user.get("user_id", "default_farmer") if current_user else "default_farmer"
    resp = service.get_preferences(user_id=user_id)
    return {"success": True, "data": resp.model_dump()}


@router.put("/preferences")
async def update_preferences(
    req: NotificationPreferencesUpdateRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    """Update user's notification preferences and threshold configurations."""
    user_id = current_user.get("user_id", "default_farmer") if current_user else "default_farmer"
    resp = service.update_preferences(req, user_id=user_id)
    return {"success": True, "data": resp.model_dump()}


@router.get("/history")
async def get_history(
    unread_only: bool = Query(False),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    """Return user's notification inbox history with unread count."""
    user_id = current_user.get("user_id", "default_farmer") if current_user else "default_farmer"
    resp = service.get_history(user_id=user_id, unread_only=unread_only)
    return {"success": True, "data": resp.model_dump()}


@router.get("/unread-count")
async def get_unread_count(
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    """Return current count of unread notifications."""
    user_id = current_user.get("user_id", "default_farmer") if current_user else "default_farmer"
    resp = service.get_unread_count(user_id=user_id)
    return {"success": True, "data": resp.model_dump()}


@router.put("/mark-read")
async def mark_notifications_read(
    req: NotificationMarkReadRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    """Mark one or more notifications (or all) as read."""
    user_id = current_user.get("user_id", "default_farmer") if current_user else "default_farmer"
    resp = service.mark_multiple_read(req, user_id=user_id)
    return {"success": True, "data": resp.model_dump()}


@router.post("/{notification_id}/read")
async def mark_single_notification_read(
    notification_id: str = Path(...),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    """Mark a specific notification item as read."""
    user_id = current_user.get("user_id", "default_farmer") if current_user else "default_farmer"
    success = service.mark_as_read(notification_id=notification_id, user_id=user_id)
    return {"success": success, "message": "Notification marked as read" if success else "Notification not found"}


@router.post("/evaluate")
async def evaluate_notifications(
    background_tasks: BackgroundTasks,
    run_async: bool = Query(False),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    """Evaluate weather, market mover, and advisory rules synchronously or in background."""
    user_id = current_user.get("user_id", "default_farmer") if current_user else "default_farmer"
    if run_async:
        background_tasks.add_task(service.evaluate_rules, user_id)
        return {"success": True, "message": "Evaluation scheduled in background"}
    resp = service.evaluate_rules(user_id=user_id)
    return {"success": True, "data": resp.model_dump()}
