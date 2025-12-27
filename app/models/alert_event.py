"""
Alert Event Model

Represents historical records of triggered alerts.
Provides audit trail and prevents duplicate notifications.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, Boolean, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class AlertEvent(Base):
    """Alert event model for logging triggered alerts."""

    __tablename__ = "alert_events"

    id = Column(Integer, primary_key=True, index=True)
    alert_rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=False, index=True)
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Price information at trigger time
    stock_price = Column(Float, nullable=False)
    previous_price = Column(Float, nullable=False)
    percent_change = Column(Float, nullable=False)

    # Notification status
    notification_sent = Column(Boolean, default=False, nullable=False)
    notification_sid = Column(String, nullable=True)  # Twilio message SID
    error_message = Column(Text, nullable=True)  # Error details if notification failed

    # Relationships
    alert_rule = relationship("AlertRule", back_populates="alert_events")

    def __repr__(self):
        return (
            f"<AlertEvent(id={self.id}, alert_rule_id={self.alert_rule_id}, "
            f"triggered_at={self.triggered_at}, price={self.stock_price}, "
            f"change={self.percent_change}%, sent={self.notification_sent})>"
        )
