# main.py
import os
import time
import logging
from contextlib import asynccontextmanager
from typing import cast, Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from fastapi.responses import HTMLResponse
from pydantic import ValidationError
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from starlette import status
from starlette.responses import JSONResponse

from src.core.templates import templates
from src.database.postgres import create_tables, engine
from src.database.redis_client import redis_manager
from src.endpoints import webinars
from src.endpoints.auth import auth_router
from src.endpoints.comments import comments_router
from src.endpoints.likes import likes_router
from src.endpoints.payments import payments_router
from src.endpoints.projects import projects_router
from src.endpoints.websocket import projects_web_router

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

# Очистка кэша Swagger (только для разработки)
if os.getenv("ENVIRONMENT") == "development" and os.path.exists("./openapi.json"):
    os.remove("./openapi.json")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup events
    print("🚀 Запуск приложения...")

    try:
        # 1. Инициализация Redis
        print("🔄 Инициализация Redis...")
        await redis_manager.init_redis()
        print("✅ Redis подключен успешно")
    except Exception as e:
        print(f"❌ Ошибка подключения к Redis: {e}")
        if os.getenv("ENVIRONMENT") == "production":
            raise

    try:
        # 2. Создание таблиц (только для разработки)
        if os.getenv("ENVIRONMENT") == "development":
            print("🔄 Создание таблиц БД...")
            await create_tables() # ❌ Только для разработки !!!
            print("✅ Таблицы созданы (development mode)")

        print("✅ Все системы инициализированы")

    except Exception as e:
        print(f"⚠️  Предупреждение при инициализации: {e}")

    yield

    # Shutdown events
    print("🛑 Завершение работы приложения...")

    try:
        # Закрытие Redis подключения
        await redis_manager.close_redis()
        print("✅ Redis отключен")
    except Exception as e:
        print(f"⚠️  Ошибка при отключении Redis: {e}")

    try:
        # Закрытие подключения к БД
        await engine.dispose()
        print("✅ Подключения к БД закрыты")
    except Exception as e:
        print(f"⚠️  Ошибка при закрытии подключений БД: {e}")

    print("👋 Приложение завершило работу")


# Создание FastAPI приложения
app = FastAPI(
    title="Crowdfunding Platform API",
    description="Платформа для краудфандинга с вебинарами и донатами",
    version="1.0.0",
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True,
        "tryItOutEnabled": True,
        "displayRequestDuration": True,
        "defaultModelsExpandDepth": -1,  # Скрыть схемы по умолчанию
        "filter": True,  # Добавить поиск в документации
    },
    redoc_url=None,  # Отключаем ReDoc, используем только Swagger
)

# Middleware и CORS
app.add_middleware(
    cast(Any, CORSMiddleware),
    allow_origins=[
        "http://localhost:8000",      # ← localhost на порту 8000
        "http://127.0.0.1:8000",      # ← 127.0.0.1 на порту 8000
        "http://localhost:8001",      # ← localhost на порту 8001
        "http://127.0.0.1:8001",      # ← 127.0.0.1 на порту 8001
    ] if os.getenv("ENVIRONMENT") == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(
    cast(Any, TrustedHostMiddleware),
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "yourdomain.com",
        "api.yourdomain.com"
    ] if os.getenv("ENVIRONMENT") == "production" else ["*"],
)


# Middleware для логирования медленных запросов
@app.middleware("http")
async def log_slow_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Логируем только медленные запросы (> 1 сек)
    if process_time > 1.0:
        logger.warning(
            f"Медленный запрос: {request.method} {request.url} "
            f"- {process_time:.3f}s"
        )

    return response


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"

    return response

# ========== EXCEPTION HANDLERS ==========

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик исключений"""
    logger.error(f"Необработанное исключение: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal Server Error",
            "error_type": type(exc).__name__
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработчик ошибок валидации запросов"""
    logger.warning(f"Ошибка валидации запроса: {exc}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation Error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request: Request, exc: ValidationError):
    """Обработчик ошибок валидации Pydantic"""
    logger.warning(f"Ошибка валидации Pydantic: {exc}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Data Validation Error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Обработчик превышения лимита запросов"""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Too many requests"}
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    """Обработчик 404 ошибок"""
    # Если запрос к API - возвращаем JSON
    if request.url.path.startswith('/api/'):
        return JSONResponse(
            status_code=404,
            content={"detail": "Endpoint not found"}
        )
    # Если запрос к странице - возвращаем HTML
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

# ========== STATIC FILES & TEMPLATES ==========

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "src", "static")

app.mount("/static", StaticFiles(directory="src/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Главная страница - HTML"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Дашборд - HTML"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Страница регистрации - HTML"""
    return templates.TemplateResponse("auth/register.html", {"request": request})  # ← auth/register.html

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа - HTML"""
    return templates.TemplateResponse("auth/login.html", {"request": request})  # ← auth/login.html

@app.get("/verify-2fa", response_class=HTMLResponse)
async def verify_2fa_page(request: Request):
    """Страница подтверждения 2FA"""
    return templates.TemplateResponse("auth/verify_2fa.html", {"request": request})

# Дополнительные HTML страницы
@app.get("/projects-page", response_class=HTMLResponse)
async def projects_page(request: Request):
    return templates.TemplateResponse("projects.html", {"request": request})

@app.get("/webinars-page", response_class=HTMLResponse)
async def webinars_page(request: Request):
    return templates.TemplateResponse("webinars.html", {"request": request})

@app.get("/comments-page", response_class=HTMLResponse)
async def comments_page(request: Request):
    return templates.TemplateResponse("comments.html", {"request": request})


# ========== ПОТОМ API ЭНДПОИНТЫ ==========

# API эндпоинты
@app.get("/api/health", tags=["System"])
async def health_check(request: Request):
    """Проверка здоровья системы - JSON"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "services": {}
    }

    # Проверка Redis
    try:
        await redis_manager.redis_client.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Проверка PostgreSQL
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        health_status["services"]["postgresql"] = "healthy"
    except Exception as e:
        health_status["services"]["postgresql"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    return health_status

@app.get("/api/root", tags=["System"])
async def api_root():
    """Корневой API endpoint - JSON"""
    return {
        "message": "Добро пожаловать в Crowdfunding Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# Пример защищенного endpoint с rate limiting
@app.get("/api/status", tags=["System"])
@limiter.limit("10/minute")
async def api_status(request: Request):
    """Статус API с ограничением запросов - JSON"""
    return {
        "status": "operational",
        "users_online": await get_online_users_count(),
        "system_load": "normal"
    }

async def get_online_users_count():
    """Получение количества онлайн пользователей из Redis"""
    try:
        if not redis_manager.redis_client:
            return 0
        keys = await redis_manager.redis_client.keys("websocket:*")
        return len(keys)
    except Exception as e:
        logger.warning(f"Ошибка получения онлайн пользователей: {e}")
        return 0

# ========== ПОДКЛЮЧЕНИЕ РОУТЕРОВ ==========

app.include_router(auth_router)
app.include_router(payments_router)
app.include_router(projects_router)
app.include_router(projects_web_router)
app.include_router(comments_router)
app.include_router(likes_router)
app.include_router(webinars.webinar_router)

print("🔍 Зарегистрированные пути:")
for route in app.routes:
    if hasattr(route, 'path'):
        methods = getattr(route, 'methods', ['?'])
        print(f"  {methods} {route.path}")



