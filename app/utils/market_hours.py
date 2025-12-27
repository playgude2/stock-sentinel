"""
Market Hours Utility

Detects if Indian stock market (NSE/BSE) is open for trading.
Handles market timings, holidays, and weekends.
"""

from datetime import datetime, time
import pytz
from typing import Tuple


# Indian Stock Market Hours (IST)
MARKET_OPEN_TIME = time(9, 15)  # 9:15 AM IST
MARKET_CLOSE_TIME = time(15, 30)  # 3:30 PM IST

# Pre-market session (optional for gap down detection)
PRE_MARKET_OPEN = time(9, 0)  # 9:00 AM IST
PRE_MARKET_CLOSE = time(9, 15)  # 9:15 AM IST

# Post-market session (optional)
POST_MARKET_OPEN = time(15, 30)  # 3:30 PM IST
POST_MARKET_CLOSE = time(16, 0)  # 4:00 PM IST

# Indian timezone
IST = pytz.timezone('Asia/Kolkata')


def is_market_open(dt: datetime = None) -> bool:
    """
    Check if Indian stock market is currently open.

    Args:
        dt: Datetime to check (defaults to now in IST)

    Returns:
        bool: True if market is open, False otherwise
    """
    if dt is None:
        dt = datetime.now(IST)
    elif dt.tzinfo is None:
        # Assume UTC if no timezone
        dt = pytz.utc.localize(dt).astimezone(IST)
    else:
        dt = dt.astimezone(IST)

    # Check if weekend (Saturday=5, Sunday=6)
    if dt.weekday() >= 5:
        return False

    # Check market hours
    current_time = dt.time()
    return MARKET_OPEN_TIME <= current_time <= MARKET_CLOSE_TIME


def is_trading_day(dt: datetime = None) -> bool:
    """
    Check if today is a trading day (not weekend or holiday).

    Args:
        dt: Date to check (defaults to today in IST)

    Returns:
        bool: True if trading day, False otherwise

    Note:
        This doesn't check for market holidays.
        You can extend this to check against a holiday calendar.
    """
    if dt is None:
        dt = datetime.now(IST)
    elif dt.tzinfo is None:
        dt = pytz.utc.localize(dt).astimezone(IST)

    # Check if weekend
    if dt.weekday() >= 5:
        return False

    # TODO: Add NSE holiday calendar check
    # For now, assume all weekdays are trading days
    return True


def get_market_status() -> Tuple[bool, str]:
    """
    Get current market status with description.

    Returns:
        tuple: (is_open, status_message)

    Examples:
        (True, "Market is open")
        (False, "Market is closed (Weekend)")
        (False, "Market is closed (After hours)")
    """
    now = datetime.now(IST)

    # Check weekend
    if now.weekday() >= 5:
        day_name = now.strftime('%A')
        return False, f"Market is closed ({day_name})"

    current_time = now.time()

    # Check if market is open
    if MARKET_OPEN_TIME <= current_time <= MARKET_CLOSE_TIME:
        return True, "Market is open"

    # Check if before market hours
    if current_time < MARKET_OPEN_TIME:
        return False, "Market is closed (Pre-market)"

    # After market hours
    return False, "Market is closed (After hours)"


def seconds_until_market_open() -> int:
    """
    Get seconds until market opens.

    Returns:
        int: Seconds until market opens (0 if already open)
    """
    now = datetime.now(IST)

    if is_market_open(now):
        return 0

    # Find next market open time
    target = now.replace(
        hour=MARKET_OPEN_TIME.hour,
        minute=MARKET_OPEN_TIME.minute,
        second=0,
        microsecond=0
    )

    # If we're past today's market hours, move to next trading day
    if now.time() > MARKET_CLOSE_TIME:
        # Move to next day
        target = target.replace(day=target.day + 1)

    # Skip weekends
    while target.weekday() >= 5:
        target = target.replace(day=target.day + 1)

    delta = (target - now).total_seconds()
    return max(0, int(delta))


def get_market_phase() -> str:
    """
    Get current market phase.

    Returns:
        str: One of 'pre_market', 'open', 'post_market', 'closed'
    """
    now = datetime.now(IST)

    # Check weekend
    if now.weekday() >= 5:
        return 'closed'

    current_time = now.time()

    # Pre-market
    if PRE_MARKET_OPEN <= current_time < MARKET_OPEN_TIME:
        return 'pre_market'

    # Market hours
    if MARKET_OPEN_TIME <= current_time <= MARKET_CLOSE_TIME:
        return 'open'

    # Post-market
    if POST_MARKET_OPEN <= current_time <= POST_MARKET_CLOSE:
        return 'post_market'

    # Closed
    return 'closed'


def should_send_alerts() -> bool:
    """
    Check if alerts should be sent.

    Returns:
        bool: True if during market hours, False otherwise
    """
    # Only send alerts during market hours
    return is_market_open()


def get_current_ist_time() -> datetime:
    """
    Get current time in IST.

    Returns:
        datetime: Current datetime in IST timezone
    """
    return datetime.now(IST)
