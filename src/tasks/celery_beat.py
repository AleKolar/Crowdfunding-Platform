# src/tasks/celery_beat.py
from celery import Celery
from datetime import timedelta

celery = Celery('crowdfunding')

celery.conf.beat_schedule = {
    'send-webinar-reminders': {
        'task': 'src.tasks.tasks.send_webinar_reminders',
        'schedule': timedelta(minutes=5),
    },
    'process-email-queue': {
        'task': 'src.tasks.tasks.process_email_queue',
        'schedule': timedelta(minutes=1),
    },
    'cleanup-old-data': {
        'task': 'src.tasks.tasks.cleanup_old_data',
        'schedule': timedelta(days=1),
    },
    'update-project-statistics': {
        'task': 'src.tasks.tasks.update_project_statistics',
        'schedule': timedelta(hours=1),
    },
}