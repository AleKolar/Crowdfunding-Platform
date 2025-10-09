# src/endpoints/webinars.py
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from src import schemas
from src.database import models
from src.database.postgres import get_db
from src.dependencies.rbac import admin_or_manager_permission
from src.security.auth import get_current_user
from src.services.webinar_service import webinar_service
from src.services.notification_service import notification_service
from src.repository.webinar_repository import webinar_repository

webinar_router = APIRouter(prefix="/webinars", tags=["webinars"])


# ==================== PUBLIC ENDPOINTS ====================

@webinar_router.get("/announcements", response_model=schemas.WebinarAnnouncementResponse)
async def get_webinar_announcements():
    """Получение активных оповещений о вебинарах для главной страницы (доступно всем)"""
    try:
        announcements = notification_service.get_active_announcements()
        return schemas.WebinarAnnouncementResponse(
            announcements=announcements,
            count=len(announcements)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении анонсов вебинаров"
        )


# ==================== USER ENDPOINTS ====================

@webinar_router.get("/", response_model=schemas.WebinarListResponse)
async def get_webinars_list(
        skip: int = 0,
        limit: int = 20,
        current_user: schemas.UserResponse = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Получение списка доступных вебинаров"""
    try:
        webinars_with_fields = await webinar_repository.get_scheduled_webinars_with_computed_fields(
            db, current_user.id, skip, limit
        )

        webinars_data = []
        for webinar, computed_fields in webinars_with_fields:
            webinars_data.append(schemas.WebinarResponse(
                id=webinar.id,
                title=webinar.title,
                description=webinar.description,
                scheduled_at=webinar.scheduled_at,
                duration=webinar.duration,
                max_participants=webinar.max_participants,
                project_id=webinar.project_id,
                creator_id=webinar.creator_id,
                room_name=computed_fields["room_name"],
                status=webinar.status,
                created_at=webinar.created_at,
                updated_at=webinar.updated_at,
                available_slots=computed_fields["available_slots"],
                is_upcoming=computed_fields["is_upcoming"],
                is_registered=computed_fields["is_registered"]
            ))

        return schemas.WebinarListResponse(
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


@webinar_router.get("/{webinar_id}", response_model=schemas.WebinarResponse)
async def get_webinar_details(
        webinar_id: int,
        current_user: schemas.UserResponse = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Получение детальной информации о вебинаре"""
    try:
        result = await webinar_repository.get_webinar_with_computed_fields(
            db, webinar_id, current_user.id
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Вебинар не найден"
            )

        webinar, computed_fields = result

        return schemas.WebinarResponse(
            id=webinar.id,
            title=webinar.title,
            description=webinar.description,
            scheduled_at=webinar.scheduled_at,
            duration=webinar.duration,
            max_participants=webinar.max_participants,
            project_id=webinar.project_id,
            creator_id=webinar.creator_id,
            room_name=computed_fields["room_name"],
            status=webinar.status,
            created_at=webinar.created_at,
            updated_at=webinar.updated_at,
            available_slots=computed_fields["available_slots"],
            is_upcoming=computed_fields["is_upcoming"],
            is_registered=computed_fields["is_registered"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении информации о вебинаре"
        )


@webinar_router.post("/{webinar_id}/register", response_model=schemas.WebinarRegistrationSuccessResponse)
async def register_for_webinar(
        webinar_id: int,
        current_user: schemas.UserResponse = Depends(get_current_user),
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

    return schemas.WebinarRegistrationSuccessResponse(**result)


@webinar_router.get("/{webinar_id}/join", response_model=schemas.WebinarJoinResponse)
async def join_webinar(
        webinar_id: int,
        current_user: schemas.UserResponse = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Присоединение к вебинару (получение токена для входа)"""
    result = await webinar_service.join_webinar(db, webinar_id, current_user.id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )

    return schemas.WebinarJoinResponse(**result)


@webinar_router.get("/my/registered", response_model=schemas.UserWebinarsResponse)
async def get_my_registered_webinars(
        skip: int = 0,
        limit: int = 20,
        current_user: schemas.UserResponse = Depends(get_current_user),
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

        return schemas.UserWebinarsResponse(
            success=True,
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
            detail="Ошибка при получении списка ваших вебинаров"
        )


@webinar_router.delete("/{webinar_id}/unregister")
async def unregister_from_webinar(
        webinar_id: int,
        current_user: schemas.UserResponse = Depends(get_current_user),
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


# ==================== ADMIN/MANAGER ENDPOINTS ====================

@webinar_router.post(
    "/",
    response_model=schemas.Webinar,
    dependencies=[Depends(admin_or_manager_permission)]
)
async def create_webinar(
        webinar_data: schemas.WebinarCreate,
        current_user: schemas.UserResponse = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Создание вебинара (только для admin/manager)"""
    return await webinar_service.create_webinar(
        db=db,
        creator_id=current_user.id,
        title=webinar_data.title,
        description=webinar_data.description,
        scheduled_at=webinar_data.scheduled_at,
        duration=webinar_data.duration,
        max_participants=webinar_data.max_participants,
        is_public=webinar_data.is_public,
    )

@webinar_router.put(
    "/{webinar_id}",
    response_model=schemas.Webinar,
    dependencies=[Depends(admin_or_manager_permission)]
)
async def update_webinar(
        webinar_id: int,
        update_data: schemas.WebinarUpdate,
        current_user: schemas.UserResponse = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Обновление вебинара (только для admin/manager)"""
    webinar = await webinar_service.update_webinar(
        db=db,
        webinar_id=webinar_id,
        updater_id=current_user.id,
        update_data=update_data.dict(exclude_unset=True)
    )

    if not webinar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webinar not found"
        )

    return webinar


@webinar_router.post(
    "/{webinar_id}/invite",
    dependencies=[Depends(admin_or_manager_permission)]
)
async def invite_users_to_webinar(
        webinar_id: int,
        user_ids: List[int],
        current_user: schemas.UserResponse = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Отправка приглашений на вебинар (только для admin/manager)"""
    sent_count = await webinar_service.send_webinar_invitations(
        db=db,
        webinar_id=webinar_id,
        user_ids=user_ids
    )

    return {
        "message": f"Invitations sent to {sent_count} users",
        "sent_count": sent_count
    }


@webinar_router.get(
    "/admin/statistics",
    dependencies=[Depends(admin_or_manager_permission)]
)
async def get_webinar_statistics(
        db: AsyncSession = Depends(get_db),
        current_user: schemas.UserResponse = Depends(get_current_user)
):
    """Статистика по вебинарам (только для admin/manager)"""
    try:
        # Получаем все вебинары
        result = await db.execute(select(models.Webinar))
        webinars = result.scalars().all()

        statistics = {
            "total_webinars": len(webinars),
            "upcoming_webinars": len([w for w in webinars if w.is_upcoming]),
            "completed_webinars": len([w for w in webinars if not w.is_upcoming]),
            "total_registrations": 0,
            "average_attendance": 0
        }

        return statistics

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении статистики"
        )