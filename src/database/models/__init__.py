# src/database/models/__init__.py
from .base import Base

# Экспортируем все модели для Alembic
__all__ = [
    'Base',
    'User', 'SMSVerificationCode',
    'UserProfile', 'UserSettings', 'Subscription',
    'Project', 'Post', 'Like', 'Repost',
    'Webinar', 'WebinarRegistration',
    'Donation', 'Transaction', 'Wallet', 'PayoutRequest',
    'Notification', 'NotificationTemplate', 'UserNotificationSettings', 'EmailQueue'
]

from .models_auth import User, SMSVerificationCode
from .models_content import Project, Post, Like, Repost
from .models_notification import Notification, NotificationTemplate, UserNotificationSettings, EmailQueue
from .models_payment import Donation, Transaction, Wallet, PayoutRequest
from .models_user import UserProfile, UserSettings, Subscription
from .models_webinar import Webinar, WebinarRegistration
