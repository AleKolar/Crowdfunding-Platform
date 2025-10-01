# src/database/models/notification_models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    message = Column(Text)
    notification_type = Column(String)  #
    # Типы: 'webinar_invite', 'webinar_reminder', 'new_post', 'donation_received',
    # 'donation_sent', 'project_goal', 'project_completed', 'comment', 'like', 'system'

    # Ссылка на связанную сущность
    related_entity_type = Column(String)  # 'project', 'webinar', 'post', 'donation', 'user'
    related_entity_id = Column(Integer)

    # Статус доставки
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    send_via_email = Column(Boolean, default=False)
    send_via_push = Column(Boolean, default=False)
    send_via_websocket = Column(Boolean, default=True)

    # Метаданные для отображения
    action_url = Column(String, nullable=True)  # URL для перехода
    image_url = Column(String, nullable=True)  # Изображение уведомления
    meta_data = Column(JSON)  # Дополнительные данные

    created_at = Column(DateTime, default=datetime.now)
    read_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    user = relationship("User")


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_type = Column(String, unique=True)
    title_template = Column(String)
    message_template = Column(Text)
    email_subject = Column(String, nullable=True)
    email_template = Column(Text, nullable=True)
    push_template = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class UserNotificationSettings(Base):
    __tablename__ = "user_notification_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    # Email уведомления
    email_project_updates = Column(Boolean, default=True)
    email_webinar_invites = Column(Boolean, default=True)
    email_webinar_reminders = Column(Boolean, default=True)
    email_donation_receipts = Column(Boolean, default=True)
    email_newsletter = Column(Boolean, default=False)

    # Push уведомления (внутри платформы)
    push_new_followers = Column(Boolean, default=True)
    push_likes = Column(Boolean, default=True)
    push_comments = Column(Boolean, default=True)
    push_donations = Column(Boolean, default=True)
    push_webinar_starting = Column(Boolean, default=True)

    # SMS уведомления
    sms_webinar_reminders = Column(Boolean, default=False)
    sms_important_updates = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User")


class EmailQueue(Base):
    __tablename__ = "email_queue"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    email = Column(String)
    subject = Column(String)
    template_name = Column(String)
    template_data = Column(JSON)
    status = Column(String, default="pending")  # pending, sent, failed, retrying
    priority = Column(Integer, default=1)  # 1-высокий, 5-низкий
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text, nullable=True)

    scheduled_for = Column(DateTime, default=datetime.now)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User")