# src/schemas/notification.py
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class NotificationBase(BaseModel):
    """Базовая схема уведомления"""
    title: str
    message: str
    notification_type: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    action_url: Optional[str] = None
    image_url: Optional[str] = None


class NotificationResponse(NotificationBase):
    """Схема ответа уведомления"""
    id: int
    user_id: int
    is_read: bool
    is_sent: bool
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    read_at: Optional[datetime]
    sent_at: Optional[datetime]

    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    """Схема обновления уведомления"""
    is_read: Optional[bool] = None


class NotificationTemplateBase(BaseModel):
    """Базовая схема шаблона уведомления"""
    template_type: str
    title_template: str
    message_template: str
    email_subject: Optional[str] = None
    email_template: Optional[str] = None
    push_template: Optional[str] = None


class NotificationTemplateResponse(NotificationTemplateBase):
    """Схема ответа шаблона"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserNotificationSettingsBase(BaseModel):
    """Базовая схема настроек уведомлений"""
    email_project_updates: bool = True
    email_webinar_invites: bool = True
    email_webinar_reminders: bool = True
    email_donation_receipts: bool = True
    email_newsletter: bool = False
    push_new_followers: bool = True
    push_likes: bool = True
    push_comments: bool = True
    push_donations: bool = True
    push_webinar_starting: bool = True
    sms_webinar_reminders: bool = False
    sms_important_updates: bool = False


class UserNotificationSettingsUpdate(UserNotificationSettingsBase):
    """Схема обновления настроек уведомлений"""
    pass


class UserNotificationSettingsResponse(UserNotificationSettingsBase):
    """Схема ответа настроек уведомлений"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailQueueBase(BaseModel):
    """Базовая схема очереди email"""
    email: str
    subject: str
    template_name: str
    template_data: Dict[str, Any]
    priority: int = 1


class EmailQueueResponse(EmailQueueBase):
    """Схема ответа очереди email"""
    id: int
    user_id: int
    status: str
    retry_count: int
    max_retries: int
    error_message: Optional[str]
    scheduled_for: datetime
    sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True