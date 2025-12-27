"""
Alert Evaluation Service

Evaluates stock alerts against real-time price data:
1. Gap Down Alerts: Compare open vs previous close at 9:15 AM
2. Intraday 1-hour Rolling Window: Find highest price in last 60 min, calculate drop
3. Intraday 2-hour Rolling Window: Find highest price in last 120 min, calculate drop
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.alert_rule import AlertRule
from app.models.intraday_price_snapshot import IntradayPriceSnapshot
from app.utils.logger import create_logger
from app.utils.market_hours import get_current_ist_time

logger = create_logger(__name__)


class AlertEvaluator:
    """Service for evaluating stock alert conditions."""

    def __init__(self, db: Session):
        self.db = db

    def should_trigger(self, alert: AlertRule, current_price_data: Dict) -> bool:
        """
        Check if alert condition is met.

        Args:
            alert: Alert rule to evaluate
            current_price_data: Current stock price data from StockPriceService

        Returns:
            bool: True if alert should be triggered
        """
        alert_type = alert.alert_type

        # Gap alerts (open vs previous close)
        if alert_type.startswith("gap_down_"):
            return self._evaluate_gap_down(alert, current_price_data)
        elif alert_type.startswith("gap_up_"):
            return self._evaluate_gap_up(alert, current_price_data)

        # Drop alerts (price drops from high in rolling window)
        elif alert_type.startswith("drop_1h_"):
            return self._evaluate_drop_from_high(alert, current_price_data, hours=1)
        elif alert_type.startswith("drop_2h_"):
            return self._evaluate_drop_from_high(alert, current_price_data, hours=2)

        # Spike alerts (price rises from low in rolling window)
        elif alert_type.startswith("spike_1h_"):
            return self._evaluate_spike_from_low(alert, current_price_data, hours=1)
        elif alert_type.startswith("spike_2h_"):
            return self._evaluate_spike_from_low(alert, current_price_data, hours=2)

        # Legacy intraday alerts
        elif alert_type.startswith("intraday_1h_"):
            return self._evaluate_drop_from_high(alert, current_price_data, hours=1)
        elif alert_type.startswith("intraday_2h_"):
            return self._evaluate_drop_from_high(alert, current_price_data, hours=2)

        else:
            logger.warning(f"Unknown alert type: {alert_type}")
            return False

    def _evaluate_gap_down(self, alert: AlertRule, price_data: Dict) -> bool:
        """
        Evaluate gap down alert (open vs previous close).

        Gap down occurs when:
        - Stock opens 7%, 8%, 9%, or 10% below previous day's close
        - Checked ONLY at market open (9:15 AM IST)

        Example:
        - Previous close: ₹3500
        - Today's open: ₹3220
        - Gap down: -8.0%
        - Threshold: -8.0
        - Result: TRIGGER

        Args:
            alert: Alert rule
            price_data: Current price data with open_price and previous_close

        Returns:
            bool: True if gap down threshold exceeded
        """
        try:
            open_price = price_data.get("open_price")
            previous_close = price_data.get("previous_close")

            if not open_price or not previous_close:
                logger.warning(f"Missing price data for gap down: {alert.stock_symbol}")
                return False

            # Calculate gap down percentage
            gap_percent = ((open_price - previous_close) / previous_close) * 100

            logger.info(
                f"Gap down check: {alert.stock_symbol} - "
                f"Open: ₹{open_price:.2f}, Prev Close: ₹{previous_close:.2f}, "
                f"Gap: {gap_percent:.2f}%, Threshold: {alert.threshold_percent}%"
            )

            # Alert threshold is negative (e.g., -8.0)
            # Trigger if gap is equal to or worse than threshold
            return gap_percent <= alert.threshold_percent

        except Exception as e:
            logger.error(f"Error evaluating gap down for {alert.stock_symbol}: {e}")
            return False

    def _evaluate_gap_up(self, alert: AlertRule, price_data: Dict) -> bool:
        """
        Evaluate gap up alert (open vs previous close).

        Gap up occurs when:
        - Stock opens 5%, 7%, 8%, 9%, or 10% ABOVE previous day's close
        - Checked at market open (9:15 AM IST)

        Example:
        - Previous close: ₹3500
        - Today's open: ₹3780
        - Gap up: +8.0%
        - Threshold: +8.0
        - Result: TRIGGER

        Args:
            alert: Alert rule
            price_data: Current price data with open_price and previous_close

        Returns:
            bool: True if gap up threshold exceeded
        """
        try:
            open_price = price_data.get("open_price")
            previous_close = price_data.get("previous_close")

            if not open_price or not previous_close:
                logger.warning(f"Missing price data for gap up: {alert.stock_symbol}")
                return False

            # Calculate gap up percentage
            gap_percent = ((open_price - previous_close) / previous_close) * 100

            logger.info(
                f"Gap up check: {alert.stock_symbol} - "
                f"Open: ₹{open_price:.2f}, Prev Close: ₹{previous_close:.2f}, "
                f"Gap: {gap_percent:.2f}%, Threshold: {alert.threshold_percent}%"
            )

            # Alert threshold is positive (e.g., +8.0)
            # Trigger if gap is equal to or better than threshold
            return gap_percent >= alert.threshold_percent

        except Exception as e:
            logger.error(f"Error evaluating gap up for {alert.stock_symbol}: {e}")
            return False

    def _evaluate_drop_from_high(
        self, alert: AlertRule, current_price_data: Dict, hours: int
    ) -> bool:
        """
        Evaluate drop from high in rolling window alert.

        Algorithm:
        1. Get all price snapshots for stock in last N hours
        2. Find highest price in that window
        3. Calculate percentage drop from highest to current
        4. Compare against threshold

        Example (1-hour window):
        - 10:15 AM: ₹3500 (highest in last hour)
        - 10:20 AM: ₹3450
        - 10:25 AM: ₹3400
        - 11:15 AM: ₹3220 (current)
        - Drop from high: -8.0%
        - Threshold: -8.0
        - Result: TRIGGER

        Args:
            alert: Alert rule
            current_price_data: Current stock price
            hours: Window size (1 or 2 hours)

        Returns:
            bool: True if drop from window high exceeds threshold
        """
        try:
            current_price = current_price_data.get("current_price")

            if not current_price:
                logger.warning(f"Missing current price for {alert.stock_symbol}")
                return False

            # Get snapshots from last N hours
            now = get_current_ist_time()
            window_start = now - timedelta(hours=hours)

            snapshots = (
                self.db.query(IntradayPriceSnapshot)
                .filter(
                    and_(
                        IntradayPriceSnapshot.stock_symbol == alert.stock_symbol,
                        IntradayPriceSnapshot.snapshot_time >= window_start,
                        IntradayPriceSnapshot.snapshot_time <= now,
                    )
                )
                .order_by(IntradayPriceSnapshot.snapshot_time.asc())
                .all()
            )

            if not snapshots:
                logger.info(
                    f"No snapshots found for {alert.stock_symbol} in last {hours}h - "
                    f"cannot evaluate rolling window"
                )
                return False

            # Find highest price in window
            highest_price = max(snapshot.price for snapshot in snapshots)

            # Calculate drop from high
            drop_percent = ((current_price - highest_price) / highest_price) * 100

            logger.info(
                f"Rolling window {hours}h: {alert.stock_symbol} - "
                f"High: ₹{highest_price:.2f}, Current: ₹{current_price:.2f}, "
                f"Drop: {drop_percent:.2f}%, Threshold: {alert.threshold_percent}%"
            )

            # Trigger if drop exceeds threshold
            return drop_percent <= alert.threshold_percent

        except Exception as e:
            logger.error(
                f"Error evaluating rolling window for {alert.stock_symbol}: {e}"
            )
            return False

    def _evaluate_spike_from_low(
        self, alert: AlertRule, current_price_data: Dict, hours: int
    ) -> bool:
        """
        Evaluate spike from low in rolling window alert.

        Algorithm:
        1. Get all price snapshots for stock in last N hours
        2. Find LOWEST price in that window
        3. Calculate percentage RISE from lowest to current
        4. Compare against threshold

        Example (1-hour window):
        - 10:15 AM: ₹3200 (lowest in last hour)
        - 10:20 AM: ₹3250
        - 10:25 AM: ₹3300
        - 11:15 AM: ₹3456 (current)
        - Rise from low: +8.0%
        - Threshold: +8.0
        - Result: TRIGGER

        Args:
            alert: Alert rule
            current_price_data: Current stock price
            hours: Window size (1 or 2 hours)

        Returns:
            bool: True if rise from window low exceeds threshold
        """
        try:
            current_price = current_price_data.get("current_price")

            if not current_price:
                logger.warning(f"Missing current price for {alert.stock_symbol}")
                return False

            # Get snapshots from last N hours
            now = get_current_ist_time()
            window_start = now - timedelta(hours=hours)

            snapshots = (
                self.db.query(IntradayPriceSnapshot)
                .filter(
                    and_(
                        IntradayPriceSnapshot.stock_symbol == alert.stock_symbol,
                        IntradayPriceSnapshot.snapshot_time >= window_start,
                        IntradayPriceSnapshot.snapshot_time <= now,
                    )
                )
                .order_by(IntradayPriceSnapshot.snapshot_time.asc())
                .all()
            )

            if not snapshots:
                logger.info(
                    f"No snapshots found for {alert.stock_symbol} in last {hours}h - "
                    f"cannot evaluate spike window"
                )
                return False

            # Find LOWEST price in window (opposite of drop detection)
            lowest_price = min(snapshot.price for snapshot in snapshots)

            # Calculate rise from low
            rise_percent = ((current_price - lowest_price) / lowest_price) * 100

            logger.info(
                f"Spike window {hours}h: {alert.stock_symbol} - "
                f"Low: ₹{lowest_price:.2f}, Current: ₹{current_price:.2f}, "
                f"Rise: {rise_percent:.2f}%, Threshold: {alert.threshold_percent}%"
            )

            # Trigger if rise exceeds threshold (threshold is positive, e.g., +8.0)
            return rise_percent >= alert.threshold_percent

        except Exception as e:
            logger.error(
                f"Error evaluating spike window for {alert.stock_symbol}: {e}"
            )
            return False

    def get_check_interval(self, threshold_percent: float) -> int:
        """
        Get check interval in seconds based on alert severity.

        Dynamic frequency:
        - 10%+ drops: Check every 5 minutes (urgent)
        - 7-9% drops: Check every 15 minutes (warning)
        - <7% drops: Check every 30 minutes (normal)

        Args:
            threshold_percent: Alert threshold (e.g., -8.0)

        Returns:
            int: Check interval in seconds
        """
        abs_threshold = abs(threshold_percent)

        if abs_threshold >= 10:
            return 300  # 5 minutes
        elif abs_threshold >= 7:
            return 900  # 15 minutes
        else:
            return 1800  # 30 minutes
