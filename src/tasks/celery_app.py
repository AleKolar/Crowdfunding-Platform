# src/tasks/celery_app.py
from celery import Celery
from src.config.settings import settings

celery_app = Celery('crowdfunding')

# Конфигурация Celery
celery_app.conf.update(
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Europe/Moscow',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

# Автоматическое обнаружение задач
celery_app.autodiscover_tasks(['src.tasks'])

# Периодические задачи
celery_app.conf.beat_schedule = {
    'cleanup-expired-sessions': {
        'task': 'src.tasks.tasks.cleanup_expired_sessions',
        'schedule': 3600.0,  # Каждый час
    },
    'send-webinar-reminders': {
        'task': 'src.tasks.tasks.send_webinar_reminders',
        'schedule': 1800.0,  # Каждые 30 минут
    },
}