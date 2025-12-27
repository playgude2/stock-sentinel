"""
Stock Price Cache Model

Caches stock prices in the database to reduce API calls.
Works alongside Redis cache for multi-level caching strategy.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime

from app.database import Base


class StockPriceCache(Base):
    """Stock price cache model for storing recent price data."""

    __tablename__ = "stock_price_cache"

    id = Column(Integer, primary_key=True, index=True)
    stock_symbol = Column(String, unique=True, nullable=False, index=True)  # e.g., "TCS"
    ticker_symbol = Column(String, nullable=False)  # e.g., "TCS.NS" (with exchange suffix)

    # Price data
    current_price = Column(Float, nullable=False)
    previous_close = Column(Float, nullable=False)
    open_price = Column(Float, nullable=False)

    # Cache metadata
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_stale = Column(Boolean, default=False, nullable=False)
    source = Column(String, default="yfinance", nullable=False)  # Data source identifier

    def __repr__(self):
        return (
            f"<StockPriceCache(symbol={self.stock_symbol}, "
            f"ticker={self.ticker_symbol}, price={self.current_price}, "
            f"updated={self.last_updated})>"
        )
