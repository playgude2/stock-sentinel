"""
Alert Rule Model

Represents stock price alert rules configured by users.
Supports:
- Gap down alerts (7%, 8%, 9%, 10% open vs previous close)
- Intraday 1-hour rolling window (7%, 8%, 9%, 10%)
- Intraday 2-hour rolling window (7%, 8%, 9%, 10%)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class AlertRule(Base):
    """Alert rule model for stock price alerts."""

    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    stock_symbol = Column(String, nullable=False, index=True)  # e.g., "TCS" (stored uppercase)

    # Alert types:
    # - "gap_down_7", "gap_down_8", "gap_down_9", "gap_down_10"
    # - "intraday_1h_7", "intraday_1h_8", "intraday_1h_9", "intraday_1h_10"
    # - "intraday_2h_7", "intraday_2h_8", "intraday_2h_9", "intraday_2h_10"
    alert_type = Column(String, nullable=False, index=True)
    threshold_percent = Column(Float, nullable=False)  # e.g., -8.0 for 8% drop

    # Dynamic check frequency (in seconds)
    # - 10%+ drops: 300 seconds (5 minutes)
    # - 7-9% drops: 900 seconds (15 minutes)
    # - <7% drops: 1800 seconds (30 minutes)
    check_interval_seconds = Column(Integer, default=900, nullable=False)

    # For intraday tracking
    reference_price = Column(Float, nullable=True)  # Baseline price for intraday comparison
    reference_timestamp = Column(DateTime, nullable=True)  # When reference was set

    # Alert state
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_checked_at = Column(DateTime, nullable=True)
    last_triggered_at = Column(DateTime, nullable=True)  # For cooldown tracking

    # Relationships
    user = relationship("User", back_populates="alert_rules")
    alert_events = relationship("AlertEvent", back_populates="alert_rule", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<AlertRule(id={self.id}, user_id={self.user_id}, "
            f"symbol={self.stock_symbol}, type={self.alert_type}, "
            f"threshold={self.threshold_percent}%)>"
        )
