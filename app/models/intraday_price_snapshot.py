"""
Intraday Price Snapshot Model

Stores 1-minute price snapshots during market hours for accurate intraday tracking.
Used for rolling window calculations (1-hour, 2-hour gap detection).
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Index
from app.database import Base


class IntradayPriceSnapshot(Base):
    """
    1-minute price snapshots for intraday tracking.

    Lifecycle:
    - Created every minute during market hours (9:15 AM - 3:30 PM IST)
    - Retained for 2 hours (sliding window)
    - Cleaned up after market close

    Usage:
    - Gap down detection (open vs previous close)
    - 1-hour rolling window (find max price in last 60 min, compare to current)
    - 2-hour rolling window (find max price in last 120 min, compare to current)
    """

    __tablename__ = "intraday_price_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    stock_symbol = Column(String(20), nullable=False, index=True)  # "TCS"
    ticker_symbol = Column(String(30), nullable=False)  # "TCS.NS"

    # Price data
    price = Column(Float, nullable=False)  # Current price at snapshot time
    open_price = Column(Float, nullable=True)  # Day's open price
    previous_close = Column(Float, nullable=True)  # Previous day's close
    volume = Column(Integer, nullable=True)  # Trading volume

    # Metadata
    snapshot_time = Column(DateTime, nullable=False, index=True)  # IST timestamp
    market_phase = Column(String(20), nullable=False)  # "open", "pre_market", "post_market"
    is_gap_down_checked = Column(Boolean, default=False)  # Track if gap down alert evaluated

    created_at = Column(DateTime, default=datetime.utcnow)

    # Composite indexes for efficient queries
    __table_args__ = (
        # For rolling window queries: "Get all TCS prices in last 60 minutes"
        Index('ix_symbol_snapshot_time', 'stock_symbol', 'snapshot_time'),

        # For gap down queries: "Get TCS open price for today"
        Index('ix_symbol_phase_time', 'stock_symbol', 'market_phase', 'snapshot_time'),
    )

    def __repr__(self):
        return f"<IntradaySnapshot {self.stock_symbol} @ {self.snapshot_time}: ₹{self.price:.2f}>"
