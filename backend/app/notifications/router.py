"""
Notifications schemas and router: price alerts and in-app notifications.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.notifications.models import PriceAlert, Notification


class CreateAlertRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    condition: str = Field(pattern="^(above|below)$")
    target_price: float = Field(gt=0)
    notes: Optional[str] = Field(None, max_length=200)


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    symbol: str
    condition: str
    target_price: float
    is_triggered: bool
    is_active: bool
    notes: Optional[str]
    created_at: datetime


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    notification_type: str
    title: str
    message: str
    is_read: bool
    symbol: Optional[str]
    created_at: datetime


router = APIRouter()


@router.post("/alerts", response_model=AlertResponse, status_code=201)
async def create_alert(schema: CreateAlertRequest, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    alert = PriceAlert(user_id=current_user.id, symbol=schema.symbol.upper(), condition=schema.condition, target_price=schema.target_price, notes=schema.notes)
    db.add(alert)
    await db.flush()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.get("/alerts", response_model=List[AlertResponse])
async def list_alerts(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PriceAlert).where(PriceAlert.user_id == current_user.id).order_by(desc(PriceAlert.created_at)))
    return [AlertResponse.model_validate(a) for a in result.scalars().all()]


@router.delete("/alerts/{alert_id}", status_code=204)
async def delete_alert(alert_id: uuid.UUID, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PriceAlert).where(and_(PriceAlert.id == alert_id, PriceAlert.user_id == current_user.id)))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.delete(alert)


@router.get("", response_model=List[NotificationResponse])
async def get_notifications(unread_only: bool = False, limit: int = 50, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    result = await db.execute(query.order_by(desc(Notification.created_at)).limit(limit))
    return [NotificationResponse.model_validate(n) for n in result.scalars().all()]


@router.post("/read-all", status_code=204)
async def mark_all_read(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Notification).where(and_(Notification.user_id == current_user.id, Notification.is_read == False)))
    for notif in result.scalars().all():
        notif.is_read = True
    await db.flush()


@router.get("/unread-count")
async def unread_count(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(func.count(Notification.id)).where(and_(Notification.user_id == current_user.id, Notification.is_read == False)))
    return {"unread_count": result.scalar() or 0}
