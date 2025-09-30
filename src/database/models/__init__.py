# src/database/models/__init__.py
from .base import Base
from .auth_models import User, SMSVerificationCode
from .user_models import UserProfile, UserSettings, Subscription
from .content_models import Project, Post, Like, Repost
from .webinar_models import Webinar, WebinarRegistration
from .payment_models import Donation, Transaction, Wallet, PayoutRequest
from .notification_models import Notification, NotificationTemplate, UserNotificationSettings, EmailQueue

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