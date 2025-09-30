from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import os
import time
import asyncio

from src.database.postgres import create_tables, delete_tables, engine
from src.database.redis_client import redis_manager

# Инициализация лимитера для rate limiting
limiter = Limiter(key_func=get_remote_address)


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
        # В зависимости от критичности, можно либо продолжить, либо завершить
        if os.getenv("ENVIRONMENT") == "production":
            raise

    try:
        # 2. Создание таблиц (только для разработки)
        if os.getenv("ENVIRONMENT") == "development":
            print("🔄 Создание таблиц БД...")
            await create_tables()
            print("✅ Таблицы созданы (development mode)")

        # 3. Дополнительные инициализации можно добавить здесь
        # Например: кэширование начальных данных, загрузка конфигураций и т.д.

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

# Добавляем лимитер в состояние приложения
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware для измерения времени выполнения запроса"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Логируем медленные запросы
    if process_time > 1.0:  # больше 1 секунды
        print(f"⚠️  Медленный запрос: {request.method} {request.url} - {process_time:.3f}s")

    return response


@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    """Middleware для управления кэшированием"""
    response = await call_next(request)

    # Добавляем заголовки кэширования для статических ресурсов
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=3600"  # 1 час

    return response


# Основные middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://yourdomain.com"
    ] if os.getenv("ENVIRONMENT") == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time", "X-Total-Count"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "yourdomain.com",
        "api.yourdomain.com"
    ] if os.getenv("ENVIRONMENT") == "production" else ["*"],
)

# Rate limiting middleware (только для production)
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(SlowAPIMiddleware)


# Health check endpoint
@app.get("/health", tags=["System"])
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Проверка здоровья системы"""
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


@app.get("/", tags=["System"])
async def root():
    """Корневой endpoint с информацией о API"""
    return {
        "message": "Добро пожаловать в Crowdfunding Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "environment": os.getenv("ENVIRONMENT", "development")
    }


# Пример защищенного endpoint с rate limiting
@app.get("/api/status", tags=["System"])
@limiter.limit("10/minute")
async def api_status(request: Request):
    """Статус API с ограничением запросов"""
    return {
        "status": "operational",
        "users_online": await get_online_users_count(),
        "system_load": "normal"
    }


async def get_online_users_count():
    """Получение количества онлайн пользователей из Redis"""
    try:
        # Пример: получаем количество подключенных WebSocket сессий
        keys = await redis_manager.redis_client.keys("websocket:*")
        return len(keys)
    except:
        return 0
