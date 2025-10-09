# src/api/endpoints/webinars.py
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import models
from src.database.postgres import get_db
from src.schemas.webinar import (
    WebinarResponse,
    WebinarListResponse,
    WebinarRegistrationSuccessResponse,
    WebinarJoinResponse,
    WebinarAnnouncementResponse
)
from src.security.auth import get_current_user
from src.services.webinar_service import webinar_service
from src.services.notification_service import notification_service
from src.repository.webinar_repository import webinar_repository

webinar_router = APIRouter(prefix="/webinars", tags=["webinars"])


@webinar_router.get("/announcements", response_model=WebinarAnnouncementResponse)
async def get_webinar_announcements():
    """Получение активных оповещений о вебинарах для главной страницы"""
    try:
        announcements = notification_service.get_active_announcements()
        return WebinarAnnouncementResponse(
            announcements=announcements,
            count=len(announcements)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении анонсов вебинаров"
        )


@webinar_router.post("/{webinar_id}/register", response_model=WebinarRegistrationSuccessResponse)
async def register_for_webinar(
    webinar_id: int,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ПРОСТАЯ регистрация на вебинар в ОДИН КЛИК!
    """
    result = await webinar_service.register_for_webinar(db, webinar_id, current_user.id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )

    return WebinarRegistrationSuccessResponse(**result)


@webinar_router.get("/{webinar_id}/join", response_model=WebinarJoinResponse)
async def join_webinar(
    webinar_id: int,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Присоединение к вебинару (получение токена для входа)"""
    result = await webinar_service.join_webinar(db, webinar_id, current_user.id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )

    return WebinarJoinResponse(**result)


@webinar_router.get("/{webinar_id}", response_model=WebinarResponse)
async def get_webinar_details(
    webinar_id: int,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение детальной информации о вебинаре"""
    try:
        webinar, registration = await webinar_repository.get_webinar_with_registration(
            db, webinar_id, current_user.id
        )

        if not webinar:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Вебинар не найден"
            )

        return WebinarResponse(
            id=webinar.id,
            title=webinar.title,
            description=webinar.description,
            scheduled_at=webinar.scheduled_at,
            duration=webinar.duration,
            max_participants=webinar.max_participants,
            project_id=webinar.project_id,
            creator_id=webinar.creator_id,
            room_name=webinar.room_name,
            status=webinar.status,
            created_at=webinar.created_at,
            updated_at=webinar.updated_at,
            available_slots=webinar.available_slots,
            is_upcoming=webinar.is_upcoming,
            is_registered=registration is not None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении информации о вебинаре"
        )


@webinar_router.get("/", response_model=WebinarListResponse)
async def get_webinars_list(
    skip: int = 0,
    limit: int = 20,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка доступных вебинаров"""
    try:
        webinars = await webinar_repository.get_scheduled_webinars(db, skip, limit)

        webinars_data = []
        for webinar in webinars:
            registration = await webinar_repository.get_user_registration(
                db, webinar.id, current_user.id
            )

            webinars_data.append(WebinarResponse(
                id=webinar.id,
                title=webinar.title,
                description=webinar.description,
                scheduled_at=webinar.scheduled_at,
                duration=webinar.duration,
                max_participants=webinar.max_participants,
                project_id=webinar.project_id,
                creator_id=webinar.creator_id,
                room_name=webinar.room_name,
                status=webinar.status,
                created_at=webinar.created_at,
                updated_at=webinar.updated_at,
                available_slots=webinar.available_slots,
                is_upcoming=webinar.is_upcoming,
                is_registered=registration is not None
            ))

        return WebinarListResponse(
            webinars=webinars_data,
            pagination={
                "skip": skip,
                "limit": limit,
                "total": len(webinars_data)
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении списка вебинаров"
        )


@webinar_router.get("/my/registered")
async def get_my_registered_webinars(
    skip: int = 0,
    limit: int = 20,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка вебинаров, на которые зарегистрирован пользователь"""
    try:
        registrations = await webinar_repository.get_user_registered_webinars(
            db, current_user.id, skip, limit
        )

        webinars_data = []
        for registration in registrations:
            webinar = registration.webinar
            webinars_data.append({
                "id": webinar.id,
                "title": webinar.title,
                "description": webinar.description,
                "scheduled_at": webinar.scheduled_at,
                "duration": webinar.duration,
                "status": webinar.status,
                "registered_at": registration.registered_at,
                "attended": registration.attended,
                "reminder_sent": registration.reminder_sent,
                "can_join": webinar.is_upcoming and webinar.scheduled_at <= datetime.now() + timedelta(hours=1)
            })

        return {
            "success": True,
            "webinars": webinars_data,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": len(webinars_data)
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении списка ваших вебинаров"
        )


@webinar_router.delete("/{webinar_id}/unregister")
async def unregister_from_webinar(
    webinar_id: int,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отмена регистрации на вебинар"""
    try:
        webinar = await webinar_repository.get_webinar_by_id(db, webinar_id)
        if not webinar:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Вебинар не найден"
            )

        if webinar.scheduled_at < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя отменить регистрацию на начавшийся вебинар"
            )

        success = await webinar_repository.delete_registration(db, webinar_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Вы не зарегистрированы на этот вебинар"
            )

        return {
            "success": True,
            "message": "Регистрация на вебинар отменена",
            "webinar_title": webinar.title
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при отмене регистрации"
        )