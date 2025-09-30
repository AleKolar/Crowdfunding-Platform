# src/database/models/webinar_models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Webinar(Base):
    __tablename__ = "webinars"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    project_id = Column(Integer, ForeignKey("projects.id"))
    scheduled_at = Column(DateTime)
    duration = Column(Integer)  # в минутах
    max_participants = Column(Integer)
    room_id = Column(String)  # ID комнаты в LiveKit
    status = Column(String, default="scheduled")  # scheduled, live, ended, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="webinars")
    registrations = relationship("WebinarRegistration", back_populates="webinar")


class WebinarRegistration(Base):
    __tablename__ = "webinar_registrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    webinar_id = Column(Integer, ForeignKey("webinars.id"))
    registered_at = Column(DateTime, default=datetime.utcnow)
    attended = Column(Boolean, default=False)

    user = relationship("User")
    webinar = relationship("Webinar", back_populates="registrations")