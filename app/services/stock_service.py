"""
Stock Price Service

Fetches stock prices from yfinance with multi-level caching:
1. Redis cache (1-minute TTL) - Hot cache for frequent requests
2. Database cache (5-minute TTL) - Warm cache for distributed access
3. yfinance API - Live data fetch

Supports Indian stocks (NSE) with automatic .NS suffix addition.
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session
from redis import Redis as RedisClient

from app.models.stock_price_cache import StockPriceCache
from app.utils.logger import create_logger
from app.config import STOCK_PRICE_CACHE_TTL, STOCK_PRICE_DB_CACHE_TTL

logger = create_logger(__name__)


class StockPriceService:
    """Service for fetching and caching stock prices."""

    # Known Indian stocks for NSE
    INDIAN_STOCKS = {
        "TCS", "INFY", "RELIANCE", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL",
        "HINDUNILVR", "ITC", "LT", "KOTAKBANK", "ASIANPAINT", "AXISBANK",
        "MARUTI", "TITAN", "BAJFINANCE", "WIPRO", "ULTRACEMCO", "SUNPHARMA",
        "NESTLEIND", "TECHM", "HCLTECH", "POWERGRID", "NTPC", "ONGC",
        "TATASTEEL", "TATAMOTORS", "M&M", "ADANIPORTS", "JSWSTEEL"
    }

    def __init__(self, db: Session, redis: RedisClient):
        """
        Initialize stock price service.

        Args:
            db: SQLAlchemy database session
            redis: Redis client for caching
        """
        self.db = db
        self.redis = redis
        self.cache_ttl = STOCK_PRICE_CACHE_TTL  # Redis TTL (seconds)
        self.db_cache_ttl = STOCK_PRICE_DB_CACHE_TTL  # DB cache TTL (seconds)

    def get_current_price(self, symbol: str) -> Optional[Dict]:
        """
        Get current stock price with multi-level caching.

        Args:
            symbol: Stock symbol (e.g., "TCS", "AAPL")

        Returns:
            dict: Price data or None if fetch failed
            {
                "symbol": "TCS",
                "ticker_symbol": "TCS.NS",
                "current_price": 3450.50,
                "previous_close": 3500.00,
                "open_price": 3480.00,
                "percent_change": -1.41,
                "timestamp": "2025-12-26T10:30:00Z"
            }
        """
        symbol = symbol.upper()

        # Level 1: Check Redis cache
        cached = self._get_from_redis_cache(symbol)
        if cached:
            logger.info(f"Redis cache hit for {symbol}")
            return cached

        # Level 2: Check DB cache
        db_cached = self._get_from_db_cache(symbol)
        if db_cached and not self._is_db_cache_stale(db_cached):
            logger.info(f"DB cache hit for {symbol}")
            self._set_redis_cache(symbol, db_cached)
            return db_cached

        # Level 3: Fetch from yfinance
        logger.info(f"Cache miss for {symbol}, fetching from yfinance")
        price_data = self._fetch_from_yfinance(symbol)

        if price_data:
            self._update_db_cache(symbol, price_data)
            self._set_redis_cache(symbol, price_data)

        return price_data

    def _get_from_redis_cache(self, symbol: str) -> Optional[Dict]:
        """
        Get price data from Redis cache.

        Args:
            symbol: Stock symbol

        Returns:
            dict: Cached price data or None
        """
        try:
            cache_key = f"stock_price:{symbol}"
            cached_json = self.redis.get(cache_key)

            if cached_json:
                return json.loads(cached_json)
        except Exception as e:
            logger.error(f"Redis cache read error: {e}")

        return None

    def _set_redis_cache(self, symbol: str, price_data: Dict):
        """
        Store price data in Redis cache.

        Args:
            symbol: Stock symbol
            price_data: Price data dictionary
        """
        try:
            cache_key = f"stock_price:{symbol}"
            self.redis.setex(cache_key, self.cache_ttl, json.dumps(price_data))
            logger.debug(f"Cached {symbol} in Redis (TTL: {self.cache_ttl}s)")
        except Exception as e:
            logger.error(f"Redis cache write error: {e}")

    def _get_from_db_cache(self, symbol: str) -> Optional[Dict]:
        """
        Get price data from database cache.

        Args:
            symbol: Stock symbol

        Returns:
            dict: Cached price data or None
        """
        try:
            cache_entry = (
                self.db.query(StockPriceCache)
                .filter(StockPriceCache.stock_symbol == symbol)
                .first()
            )

            if cache_entry:
                return {
                    "symbol": cache_entry.stock_symbol,
                    "ticker_symbol": cache_entry.ticker_symbol,
                    "current_price": cache_entry.current_price,
                    "previous_close": cache_entry.previous_close,
                    "open_price": cache_entry.open_price,
                    "percent_change": self._calculate_percent_change(
                        cache_entry.current_price, cache_entry.previous_close
                    ),
                    "timestamp": cache_entry.last_updated.isoformat(),
                }
        except Exception as e:
            logger.error(f"DB cache read error: {e}")

        return None

    def _is_db_cache_stale(self, cached_data: Dict) -> bool:
        """
        Check if DB cache entry is stale.

        Args:
            cached_data: Cached price data

        Returns:
            bool: True if cache is stale (older than DB_CACHE_TTL)
        """
        try:
            cached_time = datetime.fromisoformat(cached_data["timestamp"])
            age_seconds = (datetime.utcnow() - cached_time).total_seconds()
            return age_seconds > self.db_cache_ttl
        except:
            return True

    def _update_db_cache(self, symbol: str, price_data: Dict):
        """
        Update database cache with fresh price data.

        Args:
            symbol: Stock symbol
            price_data: Fresh price data from yfinance
        """
        try:
            cache_entry = (
                self.db.query(StockPriceCache)
                .filter(StockPriceCache.stock_symbol == symbol)
                .first()
            )

            if cache_entry:
                # Update existing entry
                cache_entry.ticker_symbol = price_data["ticker_symbol"]
                cache_entry.current_price = price_data["current_price"]
                cache_entry.previous_close = price_data["previous_close"]
                cache_entry.open_price = price_data["open_price"]
                cache_entry.last_updated = datetime.utcnow()
                cache_entry.is_stale = False
            else:
                # Create new entry
                cache_entry = StockPriceCache(
                    stock_symbol=symbol,
                    ticker_symbol=price_data["ticker_symbol"],
                    current_price=price_data["current_price"],
                    previous_close=price_data["previous_close"],
                    open_price=price_data["open_price"],
                    last_updated=datetime.utcnow(),
                    is_stale=False,
                    source="yfinance",
                )
                self.db.add(cache_entry)

            self.db.commit()
            logger.debug(f"Updated DB cache for {symbol}")

        except Exception as e:
            logger.error(f"DB cache write error: {e}")
            self.db.rollback()

    def _fetch_from_yfinance(self, symbol: str) -> Optional[Dict]:
        """
        Fetch stock price from Yahoo Finance API directly.

        Args:
            symbol: Stock symbol

        Returns:
            dict: Price data or None if fetch failed
        """
        try:
            import requests

            # Normalize symbol (add .NS for Indian stocks)
            ticker_symbol = self._normalize_symbol(symbol)

            logger.info(f"Fetching {symbol} as {ticker_symbol} from Yahoo Finance")

            # Use Yahoo Finance API directly
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_symbol}?interval=1d&range=5d"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                logger.warning(f"Yahoo Finance returned status {response.status_code} for {ticker_symbol}")
                return None

            data = response.json()

            # Parse Yahoo Finance response
            if not data.get('chart') or not data['chart'].get('result'):
                logger.warning(f"Invalid response structure for {ticker_symbol}")
                return None

            result = data['chart']['result'][0]

            # Get quote data
            if 'timestamp' not in result or 'indicators' not in result:
                logger.warning(f"Missing timestamp or indicators for {ticker_symbol}")
                return None

            timestamps = result['timestamp']
            quotes = result['indicators']['quote'][0]

            if not timestamps or not quotes.get('close'):
                logger.warning(f"No price data for {ticker_symbol}")
                return None

            # Get latest prices
            close_prices = [p for p in quotes['close'] if p is not None]
            open_prices = [p for p in quotes['open'] if p is not None]

            if not close_prices:
                logger.warning(f"No valid close prices for {ticker_symbol}")
                return None

            current_price = float(close_prices[-1])
            open_price = float(open_prices[0] if open_prices else current_price)

            # Get previous close
            if len(close_prices) >= 2:
                previous_close = float(close_prices[-2])
            else:
                # Use meta previous close if available
                meta = result.get('meta', {})
                previous_close = float(meta.get('previousClose', current_price))

            price_data = {
                "symbol": symbol,
                "ticker_symbol": ticker_symbol,
                "current_price": current_price,
                "previous_close": previous_close,
                "open_price": open_price,
                "percent_change": self._calculate_percent_change(current_price, previous_close),
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"Fetched {symbol}: ₹{current_price:.2f}")
            return price_data

        except Exception as e:
            logger.error(f"Yahoo Finance fetch error for {symbol}: {e}")
            return None

    def _normalize_symbol(self, symbol: str) -> str:
        """
        Normalize stock symbol by adding exchange suffix.

        Args:
            symbol: Raw stock symbol (e.g., "TCS", "AAPL")

        Returns:
            str: Normalized ticker symbol (e.g., "TCS.NS", "AAPL")

        Notes:
            - Indian stocks get .NS suffix for NSE
            - US/Global stocks remain unchanged
        """
        symbol = symbol.upper()

        # Check if it's a known Indian stock
        if symbol in self.INDIAN_STOCKS:
            return f"{symbol}.NS"

        # If already has exchange suffix, return as-is
        if "." in symbol:
            return symbol

        # Default: assume US stock
        return symbol

    def _calculate_percent_change(self, current: float, previous: float) -> float:
        """
        Calculate percentage change.

        Args:
            current: Current price
            previous: Previous close price

        Returns:
            float: Percentage change (e.g., -1.41 for 1.41% drop)
        """
        if previous == 0:
            return 0.0

        return ((current - previous) / previous) * 100
