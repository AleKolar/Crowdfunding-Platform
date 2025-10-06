# src/services/tasks/celery_beat.py
from celery import Celery
from datetime import timedelta

celery = Celery('crowdfunding')

celery.conf.beat_schedule = {
    'send-webinar-reminders': {
        'task': 'worker.tasks.notify_webinar_registrants',
        'schedule': timedelta(minutes=30),  # Каждые 30 минут
    },
    'cleanup-old-notifications': {
        'task': 'worker.tasks.cleanup_old_notifications',
        'schedule': timedelta(days=1),  # Ежедневно
    },
    'update-project-statistics': {
        'task': 'worker.tasks.update_project_statistics',
        'schedule': timedelta(hours=1),  # Каждый час
    },
}