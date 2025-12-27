"""
User Model

Represents WhatsApp users who interact with the chatbot.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """User model for storing WhatsApp user information."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, nullable=False, index=True)
    wa_id = Column(String, nullable=True)  # WhatsApp ID
    profile_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    alert_rules = relationship("AlertRule", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, phone={self.phone_number}, name={self.profile_name})>"
