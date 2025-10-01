# src/endpoints/projects.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.database.postgres import get_db
from src.security.auth import get_current_user
from src.schemas.project import (
    ProjectCreate, ProjectResponse, ProjectUpdate, ProjectWithMediaResponse,
    ProjectMediaResponse, PostCreate, PostResponse, CommentCreate, CommentResponse,
    ProjectMediaCreate,
    ProjectNewsResponse, ProjectNewsCreate, ProjectNewsUpdate
)
from src.database.models.models_content import MediaType, ProjectStatus
from src.utils.file_utils import validate_and_get_media_type, generate_file_path, save_uploaded_file

# Импортируем репозитории
from src.repository.projects_repository import projects_repository
from src.repository.project_media_repository import project_media_repository
from src.repository.posts_repository import posts_repository
from src.repository.comments_repository import comments_repository
from src.repository.likes_repository import likes_repository
# ИЗМЕНЕНО: новые названия репозиториев
from src.repository.project_news_repository import project_news_repository
from src.repository.news_media_repository import news_media_repository

projects_router = APIRouter(prefix="/projects", tags=["projects"])


@projects_router.post("/", response_model=ProjectResponse)
async def create_project(
        project_data: ProjectCreate,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Создание нового проекта"""
    # Используем репозиторий для создания проекта
    project = await projects_repository.create(
        db,
        project_data,
        extra_data={"creator_id": current_user.id}  # Добавляем creator_id к данным
    )
    return project


@projects_router.get("/", response_model=List[ProjectResponse])
async def get_projects(
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        status: Optional[str] = None,
        is_featured: Optional[bool] = None,
        min_goal: Optional[float] = None,
        max_goal: Optional[float] = None,
        db: AsyncSession = Depends(get_db)
):
    """Получение списка проектов с фильтрами"""
    # Используем специализированный метод репозитория для фильтрации
    projects = await projects_repository.get_with_filters(
        db,
        skip=skip,
        limit=limit,
        category=category,
        status=ProjectStatus(status) if status else None,
        is_featured=is_featured,
        min_goal=min_goal,
        max_goal=max_goal
    )
    return projects


@projects_router.get("/search/", response_model=List[ProjectResponse])
async def search_projects(
        query: str,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db)
):
    """Поиск проектов"""
    projects = await projects_repository.search(db, query, skip, limit)
    return projects


@projects_router.get("/{project_id}", response_model=ProjectWithMediaResponse)
async def get_project(
        project_id: int,
        db: AsyncSession = Depends(get_db)
):
    """Получение проекта по ID"""
    # Используем базовый метод get из репозитория
    project = await projects_repository.get(db, project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Инкрементируем счетчик просмотров
    await projects_repository.increment_views(db, project_id)

    return project


@projects_router.post("/{project_id}/upload-media", response_model=ProjectMediaResponse)
async def upload_project_media(
        project_id: int,
        file: UploadFile = File(...),
        description: str = Form(None),
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Загрузка медиа для проекта"""
    # Проверяем права доступа через репозиторий
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
    return media


@projects_router.get("/{project_id}/media", response_model=List[ProjectMediaResponse])
async def get_project_media(
        project_id: int,
        media_type: Optional[MediaType] = None,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db)
):
    """Получение медиа файлов проекта"""
    # Используем специализированный метод репозитория
    media_files = await project_media_repository.get_by_project(
        db, project_id, media_type, skip, limit
    )
    return media_files


@projects_router.post("/{project_id}/posts", response_model=PostResponse)
async def create_project_post(
        project_id: int,
        post_data: PostCreate,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Создание поста в проекте"""
    # Проверяем существование проекта через репозиторий
    project = await projects_repository.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Создаем пост через репозиторий
    post = await posts_repository.create(
        db,
        post_data,
        extra_data={
            "author_id": current_user.id,
            "project_id": project_id
        }
    )
    return post


@projects_router.get("/{project_id}/posts", response_model=List[PostResponse])
async def get_project_posts(
        project_id: int,
        skip: int = 0,
        limit: int = 50,
        db: AsyncSession = Depends(get_db)
):
    """Получение постов проекта"""
    # Используем специализированный метод репозитория
    posts = await posts_repository.get_by_project(db, project_id, skip, limit)
    return posts


@projects_router.post("/{project_id}/comments", response_model=CommentResponse)
async def create_project_comment(
        project_id: int,
        comment_data: CommentCreate,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Создание комментария к проекту"""
    # Проверяем существование проекта через репозиторий
    project = await projects_repository.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Создаем комментарий через репозиторий
    comment = await comments_repository.create(
        db,
        comment_data,
        extra_data={
            "user_id": current_user.id,
            "post_id": project_id  # Используем project_id как post_id для комментариев к проекту
        }
    )
    return comment


@projects_router.get("/{project_id}/comments", response_model=List[CommentResponse])
async def get_project_comments(
        project_id: int,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db)
):
    """Получение комментариев проекта"""
    # Используем специализированный метод репозитория
    comments = await comments_repository.get_by_post(db, project_id, skip, limit)
    return comments


@projects_router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
        project_id: int,
        project_data: ProjectUpdate,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Обновление проекта"""
    # Проверяем права доступа через репозиторий
    project = await projects_repository.get(db, project_id)
    if not project or project.creator_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found or access denied")

    # Обновляем через репозиторий
    updated_project = await projects_repository.update(db, project_id, project_data)
    return updated_project


@projects_router.delete("/{project_id}")
async def delete_project(
        project_id: int,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Удаление проекта"""
    # Проверяем права доступа через репозиторий
    project = await projects_repository.get(db, project_id)
    if not project or project.creator_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found or access denied")

    # Удаляем через репозиторий
    success = await projects_repository.delete(db, project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"message": "Project deleted successfully"}


@projects_router.post("/{project_id}/like")
async def like_project(
        project_id: int,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Лайк проекта"""
    project = await projects_repository.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Проверяем, не лайкал ли уже пользователь
    if await likes_repository.user_has_liked(db, current_user.id, project_id):
        raise HTTPException(status_code=400, detail="Project already liked")

    like = await likes_repository.create(db, current_user.id, project_id)
    return {"message": "Project liked successfully", "like": like}


@projects_router.delete("/{project_id}/like")
async def unlike_project(
        project_id: int,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Удаление лайка с проекта"""
    success = await likes_repository.delete(db, current_user.id, project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Like not found")

    return {"message": "Like removed successfully"}


# ИЗМЕНЕНО: эндпоинты для новостей проекта (обновлений)
@projects_router.post("/{project_id}/news", response_model=ProjectNewsResponse)
async def create_project_news(
        project_id: int,
        news_data: ProjectNewsCreate,  # ИЗМЕНЕНО
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Создание новости проекта"""
    project = await projects_repository.get(db, project_id)
    if not project or project.creator_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found or access denied")

    # Добавляем project_id к данным
    news = await project_news_repository.create(  # ИЗМЕНЕНО
        db,
        news_data,
        extra_data={"project_id": project_id}
    )
    return news


@projects_router.get("/{project_id}/news", response_model=List[ProjectNewsResponse])
async def get_project_news(  # ИЗМЕНЕНО
        project_id: int,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db)
):
    """Получение новостей проекта"""
    news = await project_news_repository.get_by_project(db, project_id, skip, limit)  # ИЗМЕНЕНО
    return news


@projects_router.put("/{project_id}/news/{news_id}", response_model=ProjectNewsResponse)
async def update_project_news(  # ИЗМЕНЕНО
        project_id: int,
        news_id: int,
        news_data: ProjectNewsUpdate,  # ИЗМЕНЕНО
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Обновление новости проекта"""
    # Проверяем права доступа
    project = await projects_repository.get(db, project_id)
    if not project or project.creator_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found or access denied")

    # Обновляем новость
    updated_news = await project_news_repository.update(db, news_id, news_data)  # ИЗМЕНЕНО
    if not updated_news:
        raise HTTPException(status_code=404, detail="News not found")

    return updated_news


@projects_router.delete("/{project_id}/news/{news_id}")
async def delete_project_news(  # ИЗМЕНЕНО
        project_id: int,
        news_id: int,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Удаление новости проекта"""
    # Проверяем права доступа
    project = await projects_repository.get(db, project_id)
    if not project or project.creator_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found or access denied")

    # Удаляем новость
    success = await project_news_repository.delete(db, news_id)  # ИЗМЕНЕНО
    if not success:
        raise HTTPException(status_code=404, detail="News not found")

    return {"message": "News deleted successfully"}