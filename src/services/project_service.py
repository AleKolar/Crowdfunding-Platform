# src/services/project_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.database.models.models_content import Project, ProjectStatus
from src.schemas.project import (
    ProjectCreate, ProjectResponse, ProjectUpdate, ProjectWithMediaResponse,
    ProjectMediaResponse, PostResponse, CommentResponse, ProjectNewsResponse
)
from src.repository.projects_repository import projects_repository
from src.repository.project_media_repository import project_media_repository
from src.repository.posts_repository import posts_repository
from src.repository.comments_repository import comments_repository
from src.repository.likes_repository import likes_repository
from src.repository.project_news_repository import project_news_repository


class ProjectService:
    """Сервис для работы с проектами и преобразования моделей"""

    @staticmethod
    def to_response(project: Project) -> ProjectResponse:
        """Преобразование SQLAlchemy модели в Pydantic схему"""
        return ProjectResponse.model_validate(project)

    @staticmethod
    def to_response_with_media(project: Project) -> ProjectWithMediaResponse:
        """Преобразование с медиа"""
        return ProjectWithMediaResponse.model_validate(project)

    @staticmethod
    def to_response_list(projects: List[Project]) -> List[ProjectResponse]:
        """Преобразование списка моделей"""
        return [ProjectService.to_response(project) for project in projects]

    # Основные методы проектов
    @classmethod
    async def create_project(
            cls,
            db: AsyncSession,
            project_data: ProjectCreate,
            creator_id: int
    ) -> ProjectResponse:
        """Создание проекта с преобразованием"""
        project = await projects_repository.create(db, project_data, creator_id=creator_id)
        return cls.to_response(project)

    @classmethod
    async def get_projects_with_filters(
            cls,
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            category: Optional[str] = None,
            status: Optional[str] = None,
            is_featured: Optional[bool] = None,
            min_goal: Optional[float] = None,
            max_goal: Optional[float] = None
    ) -> List[ProjectResponse]:
        """Получение проектов с фильтрами"""
        status_enum = ProjectStatus(status) if status else None
        projects = await projects_repository.get_with_filters(
            db, skip, limit, category, status_enum, is_featured, min_goal, max_goal
        )
        return cls.to_response_list(projects)

    @classmethod
    async def search_projects(
            cls,
            db: AsyncSession,
            query: str,
            skip: int = 0,
            limit: int = 100
    ) -> List[ProjectResponse]:
        """Поиск проектов"""
        projects = await projects_repository.search(db, query, skip, limit)
        return cls.to_response_list(projects)

    @classmethod
    async def get_project_with_media(
            cls,
            db: AsyncSession,
            project_id: int
    ) -> ProjectWithMediaResponse:
        """Получение проекта с медиа"""
        project = await projects_repository.get_with_media(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        await projects_repository.increment_views(db, project_id)
        return cls.to_response_with_media(project)

    @classmethod
    async def update_project(
            cls,
            db: AsyncSession,
            project_id: int,
            project_data: ProjectUpdate,
            creator_id: int
    ) -> ProjectResponse:
        """Обновление проекта с проверкой прав"""
        project = await projects_repository.get(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.creator_id != creator_id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        updated_project = await projects_repository.update(db, project_id, project_data)
        return cls.to_response(updated_project)

    @classmethod
    async def delete_project(
            cls,
            db: AsyncSession,
            project_id: int,
            creator_id: int
    ) -> dict:
        """Удаление проекта с проверкой прав"""
        project = await projects_repository.get(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.creator_id != creator_id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        success = await projects_repository.delete(db, project_id)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")

        return {"message": "Project deleted successfully"}

    # Методы для медиа
    @classmethod
    async def get_project_media(
            cls,
            db: AsyncSession,
            project_id: int,
            media_type: Optional[str] = None,
            skip: int = 0,
            limit: int = 100
    ) -> List[ProjectMediaResponse]:
        """Получение медиа файлов проекта"""
        from src.database.models.models_content import MediaType
        media_type_enum = MediaType(media_type) if media_type else None

        media_files = await project_media_repository.get_by_project(
            db, project_id, media_type_enum, skip, limit
        )
        return [ProjectMediaResponse.model_validate(media) for media in media_files]

    # Методы для постов
    @classmethod
    async def create_project_post(
            cls,
            db: AsyncSession,
            project_id: int,
            post_data,
            author_id: int
    ) -> PostResponse:
        """Создание поста в проекте"""
        project = await projects_repository.get(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        post = await posts_repository.create(
            db,
            post_data,
            author_id=author_id,
            project_id=project_id
        )
        return PostResponse.model_validate(post)

    @classmethod
    async def get_project_posts(
            cls,
            db: AsyncSession,
            project_id: int,
            skip: int = 0,
            limit: int = 50
    ) -> List[PostResponse]:
        """Получение постов проекта"""
        posts = await posts_repository.get_by_project(db, project_id, skip, limit)
        return [PostResponse.model_validate(post) for post in posts]

    # Методы для комментариев
    @classmethod
    async def create_project_comment(
            cls,
            db: AsyncSession,
            project_id: int,
            comment_data,
            user_id: int
    ) -> CommentResponse:
        """Создание комментария к проекту"""
        project = await projects_repository.get(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        comment = await comments_repository.create(
            db,
            comment_data,
            user_id=user_id,
            post_id=project_id
        )
        return CommentResponse.model_validate(comment)

    @classmethod
    async def get_project_comments(
            cls,
            db: AsyncSession,
            project_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> List[CommentResponse]:
        """Получение комментариев проекта"""
        comments = await comments_repository.get_by_post(db, project_id, skip, limit)
        return [CommentResponse.model_validate(comment) for comment in comments]

    # Методы для лайков
    @classmethod
    async def like_project(
            cls,
            db: AsyncSession,
            project_id: int,
            user_id: int
    ) -> dict:
        """Лайк проекта"""
        project = await projects_repository.get(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if await likes_repository.user_has_liked(db, user_id, project_id):
            raise HTTPException(status_code=400, detail="Project already liked")

        like = await likes_repository.create(db, user_id, project_id)
        return {"message": "Project liked successfully", "like": like}

    @classmethod
    async def unlike_project(
            cls,
            db: AsyncSession,
            project_id: int,
            user_id: int
    ) -> dict:
        """Удаление лайка с проекта"""
        success = await likes_repository.delete(db, user_id, project_id)
        if not success:
            raise HTTPException(status_code=404, detail="Like not found")

        return {"message": "Like removed successfully"}

    # Методы для новостей
    @classmethod
    async def create_project_news(
            cls,
            db: AsyncSession,
            project_id: int,
            news_data,
            creator_id: int
    ) -> ProjectNewsResponse:
        """Создание новости проекта"""
        project = await projects_repository.get(db, project_id)
        if not project or project.creator_id != creator_id:
            raise HTTPException(status_code=404, detail="Project not found or access denied")

        news = await project_news_repository.create(
            db,
            news_data,
            project_id=project_id
        )
        return ProjectNewsResponse.model_validate(news)

    @classmethod
    async def get_project_news(
            cls,
            db: AsyncSession,
            project_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> List[ProjectNewsResponse]:
        """Получение новостей проекта"""
        news = await project_news_repository.get_by_project(db, project_id, skip, limit)
        return [ProjectNewsResponse.model_validate(item) for item in news]

    @classmethod
    async def update_project_news(
            cls,
            db: AsyncSession,
            project_id: int,
            news_id: int,
            news_data,
            creator_id: int
    ) -> ProjectNewsResponse:
        """Обновление новости проекта"""
        project = await projects_repository.get(db, project_id)
        if not project or project.creator_id != creator_id:
            raise HTTPException(status_code=404, detail="Project not found or access denied")

        updated_news = await project_news_repository.update(db, news_id, news_data)
        if not updated_news:
            raise HTTPException(status_code=404, detail="News not found")

        return ProjectNewsResponse.model_validate(updated_news)

    @classmethod
    async def delete_project_news(
            cls,
            db: AsyncSession,
            project_id: int,
            news_id: int,
            creator_id: int
    ) -> dict:
        """Удаление новости проекта"""
        project = await projects_repository.get(db, project_id)
        if not project or project.creator_id != creator_id:
            raise HTTPException(status_code=404, detail="Project not found or access denied")

        success = await project_news_repository.delete(db, news_id)
        if not success:
            raise HTTPException(status_code=404, detail="News not found")

        return {"message": "News deleted successfully"}

    @classmethod
    async def get_user_projects(
        cls,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[ProjectResponse]:
        """Получение проектов пользователя"""
        projects = await projects_repository.get_by_creator(db, user_id, skip, limit)
        return cls.to_response_list(projects)