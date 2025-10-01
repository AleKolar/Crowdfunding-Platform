# src/endpoints/projects.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from src.database.postgres import get_db
from src.security.auth import get_current_user
from src.schemas.project import (
    ProjectCreate, ProjectResponse, ProjectUpdate, ProjectWithMediaResponse,
    ProjectMediaResponse, PostCreate, PostResponse, CommentCreate, CommentResponse
)
from src.database.models.models_content import Project, ProjectMedia, Post, Comment, MediaType, ProjectStatus
from src.utils.file_utils import validate_and_get_media_type, generate_file_path, save_uploaded_file

projects_router = APIRouter(prefix="/projects", tags=["projects"])


@projects_router.post("/", response_model=ProjectResponse)
async def create_project(
        project_data: ProjectCreate,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Создание нового проекта"""
    project = Project(
        **project_data.model_dump(),
        creator_id=current_user.id
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@projects_router.get("/", response_model=List[ProjectResponse])
async def get_projects(
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        status: Optional[str] = None,
        db: AsyncSession = Depends(get_db)
):
    """Получение списка проектов"""
    stmt = select(Project)

    if category:
        stmt = stmt.where(Project.category == category)
    if status:
        stmt = stmt.where(Project.status == ProjectStatus(status))

    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    projects = result.scalars().all()
    return projects


@projects_router.get("/{project_id}", response_model=ProjectWithMediaResponse)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """Получение проекта по ID"""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
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
    # Проверяем права доступа
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project or project.creator_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found or access denied")

    # Валидация и сохранение файла
    media_type, mime_type = await validate_and_get_media_type(file)
    file_path = generate_file_path(project_id, media_type, file.filename)
    file_size = await save_uploaded_file(file, file_path)

    # Создаем запись в БД
    media = ProjectMedia(
        project_id=project_id,
        file_url=f"/{file_path}",
        file_type=media_type,
        file_name=file.filename,
        file_size=file_size,
        mime_type=mime_type,
        description=description
    )

    db.add(media)
    await db.commit()
    await db.refresh(media)
    return media


@projects_router.get("/{project_id}/media", response_model=List[ProjectMediaResponse])
async def get_project_media(
        project_id: int,
        media_type: Optional[MediaType] = None,
        db: AsyncSession = Depends(get_db)
):
    """Получение медиа файлов проекта"""
    stmt = select(ProjectMedia).where(ProjectMedia.project_id == project_id)

    if media_type:
        stmt = stmt.where(ProjectMedia.file_type == media_type)

    stmt = stmt.order_by(ProjectMedia.sort_order, ProjectMedia.created_at)

    result = await db.execute(stmt)
    media_files = result.scalars().all()
    return media_files


@projects_router.post("/{project_id}/posts", response_model=PostResponse)
async def create_project_post(
        project_id: int,
        post_data: PostCreate,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Создание поста в проекте"""
    # Проверяем существование проекта
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    post = Post(
        **post_data.model_dump(),
        author_id=current_user.id,
        project_id=project_id
    )

    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


@projects_router.get("/{project_id}/posts", response_model=List[PostResponse])
async def get_project_posts(
        project_id: int,
        skip: int = 0,
        limit: int = 50,
        db: AsyncSession = Depends(get_db)
):
    """Получение постов проекта"""
    stmt = (
        select(Post)
        .where(Post.project_id == project_id)
        .order_by(Post.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(stmt)
    posts = result.scalars().all()
    return posts


@projects_router.post("/{project_id}/comments", response_model=CommentResponse)
async def create_project_comment(
        project_id: int,
        comment_data: CommentCreate,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Создание комментария к проекту"""
    # Проверяем существование проекта
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    comment = Comment(
        **comment_data.model_dump(),
        user_id=current_user.id,
        post_id=project_id  # Используем project_id как post_id для комментариев к проекту
    )

    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


@projects_router.get("/{project_id}/comments", response_model=List[CommentResponse])
async def get_project_comments(
        project_id: int,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db)
):
    """Получение комментариев проекта"""
    stmt = (
        select(Comment)
        .where(Comment.post_id == project_id)  # Комментарии к проекту
        .order_by(Comment.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(stmt)
    comments = result.scalars().all()
    return comments


@projects_router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
        project_id: int,
        project_data: ProjectUpdate,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Обновление проекта"""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project or project.creator_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found or access denied")

    # Обновляем только переданные поля
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return project


@projects_router.delete("/{project_id}")
async def delete_project(
        project_id: int,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Удаление проекта"""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project or project.creator_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found or access denied")

    await db.delete(project)
    await db.commit()

    return {"message": "Project deleted successfully"}