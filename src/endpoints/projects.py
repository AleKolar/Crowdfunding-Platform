# src/endpoints/projects.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.database.postgres import get_db
from src.security.auth import get_current_user
from src.schemas.project import (
    ProjectCreate, ProjectResponse, ProjectUpdate, ProjectWithMediaResponse,
    ProjectMediaResponse, PostCreate, PostResponse, CommentCreate, CommentResponse,
    ProjectMediaCreate, ProjectNewsResponse, ProjectNewsCreate, ProjectNewsUpdate
)
from src.database.models.models_content import MediaType
from src.utils.file_utils import validate_and_get_media_type, generate_file_path, save_uploaded_file
from src.services.project_service import ProjectService
from src.repository.project_media_repository import project_media_repository

projects_router = APIRouter(prefix="/projects", tags=["projects"])


@projects_router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание нового проекта"""
    return await ProjectService.create_project(db, project_data, current_user.id)


@projects_router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_featured: Optional[bool] = Query(None),
    min_goal: Optional[float] = Query(None, ge=0),
    max_goal: Optional[float] = Query(None, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка проектов с фильтрами"""
    return await ProjectService.get_projects_with_filters(
        db, skip, limit, category, status, is_featured, min_goal, max_goal
    )


@projects_router.get("/search/", response_model=List[ProjectResponse])
async def search_projects(
    query: str = Query(..., min_length=1, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Поиск проектов"""
    return await ProjectService.search_projects(db, query, skip, limit)


@projects_router.get("/{project_id}", response_model=ProjectWithMediaResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получение проекта по ID"""
    return await ProjectService.get_project_with_media(db, project_id)


@projects_router.post("/{project_id}/upload-media", response_model=ProjectMediaResponse)
async def upload_project_media(
    project_id: int,
    file: UploadFile = File(...),
    description: str = Form(None),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Загрузка медиа для проекта"""
    # Проверяем права доступа
    from src.repository.projects_repository import projects_repository
    project = await projects_repository.get(db, project_id)
    if not project or project.creator_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found or access denied")

    # Валидация и сохранение файла
    media_type, mime_type = await validate_and_get_media_type(file)
    file_path = generate_file_path(project_id, media_type, file.filename)
    file_size = await save_uploaded_file(file, file_path)

    # Создаем запись в БД через репозиторий
    media_data = ProjectMediaCreate(
        project_id=project_id,
        file_url=f"/{file_path}",
        file_type=media_type,
        file_name=file.filename,
        file_size=file_size,
        mime_type=mime_type,
        description=description
    )

    media = await project_media_repository.create(db, media_data)
    return ProjectMediaResponse.model_validate(media)


@projects_router.get("/{project_id}/media", response_model=List[ProjectMediaResponse])
async def get_project_media(
    project_id: int,
    media_type: Optional[MediaType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Получение медиа файлов проекта"""
    return await ProjectService.get_project_media(db, project_id, media_type, skip, limit)


@projects_router.post("/{project_id}/posts", response_model=PostResponse)
async def create_project_post(
    project_id: int,
    post_data: PostCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание поста в проекте"""
    return await ProjectService.create_project_post(db, project_id, post_data, current_user.id)


@projects_router.get("/{project_id}/posts", response_model=List[PostResponse])
async def get_project_posts(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Получение постов проекта"""
    return await ProjectService.get_project_posts(db, project_id, skip, limit)


@projects_router.post("/{project_id}/comments", response_model=CommentResponse)
async def create_project_comment(
    project_id: int,
    comment_data: CommentCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание комментария к проекту"""
    return await ProjectService.create_project_comment(db, project_id, comment_data, current_user.id)


@projects_router.get("/{project_id}/comments", response_model=List[CommentResponse])
async def get_project_comments(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Получение комментариев проекта"""
    return await ProjectService.get_project_comments(db, project_id, skip, limit)


@projects_router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление проекта"""
    return await ProjectService.update_project(db, project_id, project_data, current_user.id)


@projects_router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление проекта"""
    return await ProjectService.delete_project(db, project_id, current_user.id)


@projects_router.post("/{project_id}/like")
async def like_project(
    project_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Лайк проекта"""
    return await ProjectService.like_project(db, project_id, current_user.id)


@projects_router.delete("/{project_id}/like")
async def unlike_project(
    project_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление лайка с проекта"""
    return await ProjectService.unlike_project(db, project_id, current_user.id)


@projects_router.post("/{project_id}/news", response_model=ProjectNewsResponse)
async def create_project_news(
    project_id: int,
    news_data: ProjectNewsCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание новости проекта"""
    return await ProjectService.create_project_news(db, project_id, news_data, current_user.id)


@projects_router.get("/{project_id}/news", response_model=List[ProjectNewsResponse])
async def get_project_news(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Получение новостей проекта"""
    return await ProjectService.get_project_news(db, project_id, skip, limit)


@projects_router.put("/{project_id}/news/{news_id}", response_model=ProjectNewsResponse)
async def update_project_news(
    project_id: int,
    news_id: int,
    news_data: ProjectNewsUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление новости проекта"""
    return await ProjectService.update_project_news(db, project_id, news_id, news_data, current_user.id)


@projects_router.delete("/{project_id}/news/{news_id}")
async def delete_project_news(
    project_id: int,
    news_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление новости проекта"""
    return await ProjectService.delete_project_news(db, project_id, news_id, current_user.id)

