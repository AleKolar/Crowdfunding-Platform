# src/api/endpoints/webinars.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import models
from src.database.postgres import get_db
from src.security.auth import get_current_user
from src.services.webinar_service import webinar_service

from src.services.notification_service import notification_service

webinar_router = APIRouter(prefix="/webinars", tags=["webinars"])


@webinar_router.get("/announcements")
async def get_webinar_announcements():
    """Получение активных оповещений о вебинарах для главной страницы"""
    announcements = notification_service.get_active_announcements()
    return {"announcements": announcements}


@webinar_router.post("/{webinar_id}/register-simple")
async def register_for_webinar_simple(
        webinar_id: int,
        current_user: models.User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    ПРОСТАЯ регистрация на вебинар,
    в ОДИН КЛИК!
    """
    result = await webinar_service.register_for_webinar(db, webinar_id, current_user.id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@webinar_router.get("/{webinar_id}/quick-join")
async def quick_join_webinar(
        webinar_id: int,
        current_user: models.User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Быстрое присоединение к вебинару (когда он начался)"""
    result = await webinar_service.join_webinar(db, webinar_id, current_user.id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result