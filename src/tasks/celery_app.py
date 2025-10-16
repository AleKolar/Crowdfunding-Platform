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
    # 📧 Email задачи
    'process-email-queue': {
        'task': 'src.tasks.tasks.process_email_queue',
        'schedule': 60.0,
    },

    # 🔔 Уведомления и напоминания
    'send-webinar-reminders': {
        'task': 'src.tasks.tasks.send_webinar_reminders',
        'schedule': 3600.0,
    },

    # 📊 Статистика и аналитика
    'update-project-statistics': {
        'task': 'src.tasks.tasks.update_project_statistics',
        'schedule': 3600.0,  # Каждый час
    },
    'update-project-rankings': {
        'task': 'src.tasks.tasks.update_project_rankings',
        'schedule': 86400.0,  # Раз в день (24 часа)
    },

    # 🧹 Очистка данных
    'cleanup-old-data': {
        'task': 'src.tasks.tasks.cleanup_old_data',
        'schedule': 86400.0,  # Раз в день (24 часа)
    },
}
# 3600.0, 86400.0
