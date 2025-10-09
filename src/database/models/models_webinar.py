# src/database/models/models_webinar.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
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
    is_public = Column(Boolean, default=True)
    room_name = Column(String(100))
    status = Column(String(20), default="scheduled")
    meta_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # ✅ ССЫЛКА НА СОЗДАТЕЛЯ
    creator_id = Column(Integer, ForeignKey("users.id"))

    project = relationship("Project", back_populates="webinars")
    registrations = relationship("WebinarRegistration", back_populates="webinar", cascade="all, delete-orphan")

    # ✅ СВЯЗЬ С СОЗДАТЕЛЕМ
    creator = relationship("User", back_populates="created_webinars")

    # Вычисляемые свойства
    @property
    def available_slots(self):
        """Вычисляет доступные слоты без ленивой загрузки"""
        # Свойство available_slots не работает при попытки
        # загрузить связанные регистрации (self.registrations) --> ленивая загрузка
        # ленивая загрузка - не работает без правильного вызова greenlet_spawn
        return self.max_participants

    async def get_available_slots(self, session):
        """Асинхронный метод для получения доступных слотов"""
        from sqlalchemy import select, func
        result = await session.execute(
            select(func.count(WebinarRegistration.id)).where(
                WebinarRegistration.webinar_id == self.id
            )
        )
        registrations_count = result.scalar()
        return self.max_participants - registrations_count

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