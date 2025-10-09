# src/schemas/notification.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
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
    meta_data: Optional[Dict[str, Any]] = None


class NotificationResponse(NotificationBase):
    """Схема ответа уведомления"""
    id: int
    user_id: int
    is_read: bool = False
    is_sent: bool = False
    send_via_email: bool = False
    send_via_push: bool = False
    send_via_websocket: bool = True
    created_at: datetime
    read_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    """Схема ответа списка уведомлений"""
    success: bool = True
    notifications: List[NotificationResponse]
    unread_count: int = 0
    pagination: Optional[dict] = None


class NotificationUpdate(BaseModel):
    """Схема обновления уведомления"""
    is_read: Optional[bool] = None

    model_config = ConfigDict(extra='forbid')


class MarkAsReadResponse(BaseModel):
    """Схема ответа пометки как прочитанного"""
    success: bool = True
    message: str = "Уведомление помечено как прочитанное"


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
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationTemplateCreate(NotificationTemplateBase):
    """Схема создания шаблона"""
    pass


class NotificationTemplateUpdate(BaseModel):
    """Схема обновления шаблона"""
    template_type: Optional[str] = None
    title_template: Optional[str] = None
    message_template: Optional[str] = None
    email_subject: Optional[str] = None
    email_template: Optional[str] = None
    push_template: Optional[str] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra='forbid')


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

    model_config = ConfigDict(from_attributes=True)


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
    status: str = "pending"
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    scheduled_for: datetime
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmailQueueCreate(EmailQueueBase):
    """Схема создания email в очереди"""
    user_id: int


class EmailQueueUpdate(BaseModel):
    """Схема обновления email в очереди"""
    status: Optional[str] = None
    retry_count: Optional[int] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None

    model_config = ConfigDict(extra='forbid')


class NotificationCreateRequest(BaseModel):
    """Схема запроса создания уведомления"""
    user_id: int
    title: str
    message: str
    notification_type: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    action_url: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


class NotificationCreateResponse(BaseModel):
    """Схема ответа создания уведомления"""
    success: bool = True
    notification: NotificationResponse
    message: str = "Уведомление создано успешно"