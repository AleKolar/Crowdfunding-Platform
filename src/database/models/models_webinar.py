# src/database/models/webinar_models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Webinar(Base):
    __tablename__ = "webinars"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    description = Column(Text)
    project_id = Column(Integer, ForeignKey("projects.id"))
    scheduled_at = Column(DateTime, nullable=False)
    duration = Column(Integer, default=60)  # в минутах
    max_participants = Column(Integer, default=100)
    room_name = Column(String(100))
    status = Column(String(20), default="scheduled")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    project = relationship("Project", back_populates="webinars")
    registrations = relationship("WebinarRegistration", back_populates="webinar", cascade="all, delete-orphan")

    # Вычисляемые свойства
    @property
    def available_slots(self):
        return self.max_participants - len(self.registrations)

    @property
    def is_upcoming(self):
        return self.scheduled_at > datetime.now() and self.status == "scheduled"


class WebinarRegistration(Base):
    __tablename__ = "webinar_registrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    webinar_id = Column(Integer, ForeignKey("webinars.id"))
    registered_at = Column(DateTime, default=datetime.now)
    attended = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)  # Оптимизации рассылок

    user = relationship("User", back_populates="webinar_registrations")
    webinar = relationship("Webinar", back_populates="registrations")