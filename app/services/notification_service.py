"""
Notification Service

Handles sending WhatsApp notifications for triggered stock alerts.
Logs alert events and implements cooldown to prevent spam.
"""

from datetime import datetime, timedelta
from typing import Dict
from sqlalchemy.orm import Session
from twilio.rest import Client as TwilioClient

from app.models.alert_rule import AlertRule
from app.models.alert_event import AlertEvent
from app.config import TWILIO_WHATSAPP_NUMBER, ALERT_COOLDOWN_PERIOD
from app.utils.logger import create_logger

logger = create_logger(__name__)


class NotificationService:
    """Service for sending alert notifications via WhatsApp."""

    def __init__(self, twilio_client: TwilioClient, db: Session):
        """
        Initialize notification service.

        Args:
            twilio_client: Twilio client for sending messages
            db: SQLAlchemy database session
        """
        self.twilio = twilio_client
        self.db = db
        self.cooldown_period = ALERT_COOLDOWN_PERIOD  # seconds

    def can_send_notification(self, alert: AlertRule) -> bool:
        """
        Check if alert is eligible for notification (cooldown check).

        Args:
            alert: Alert rule to check

        Returns:
            bool: True if cooldown period has passed or no previous trigger
        """
        if not alert.last_triggered_at:
            return True  # Never triggered before

        time_since_last = datetime.utcnow() - alert.last_triggered_at
        cooldown_passed = time_since_last.total_seconds() >= self.cooldown_period

        if not cooldown_passed:
            remaining = self.cooldown_period - time_since_last.total_seconds()
            logger.debug(
                f"Alert {alert.id} in cooldown: {remaining / 60:.1f} minutes remaining"
            )

        return cooldown_passed

    def send_alert_notification(self, alert: AlertRule, price_data: Dict) -> bool:
        """
        Send WhatsApp notification for triggered alert.

        Args:
            alert: Triggered alert rule
            price_data: Current stock price data

        Returns:
            bool: True if notification sent successfully

        Side effects:
            - Sends WhatsApp message via Twilio
            - Logs alert event in database
            - Updates alert.last_triggered_at
            - Keeps alert.is_active = True (recurring alerts per user preference)
        """
        try:
            user = alert.user
            message_body = self._format_alert_message(alert, price_data)

            # Send WhatsApp message
            logger.info(f"Sending alert notification to {user.phone_number} for {alert.stock_symbol}")

            response = self.twilio.messages.create(
                from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
                body=message_body,
                to=user.phone_number,
            )

            # Log successful alert event
            event = AlertEvent(
                alert_rule_id=alert.id,
                triggered_at=datetime.utcnow(),
                stock_price=price_data["current_price"],
                previous_price=price_data["previous_close"],
                percent_change=price_data["percent_change"],
                notification_sent=True,
                notification_sid=response.sid,
            )
            self.db.add(event)

            # Update alert (keep active, update last_triggered_at for cooldown)
            alert.last_triggered_at = datetime.utcnow()
            # alert.is_active remains True (recurring alerts)

            self.db.commit()

            logger.info(
                f"Alert notification sent successfully: "
                f"alert_id={alert.id}, SID={response.sid}, "
                f"symbol={alert.stock_symbol}, price=₹{price_data['current_price']:.2f}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to send alert notification for alert {alert.id}: {e}")

            # Log failed alert event
            try:
                event = AlertEvent(
                    alert_rule_id=alert.id,
                    triggered_at=datetime.utcnow(),
                    stock_price=price_data.get("current_price", 0),
                    previous_price=price_data.get("previous_close", 0),
                    percent_change=price_data.get("percent_change", 0),
                    notification_sent=False,
                    error_message=str(e),
                )
                self.db.add(event)
                self.db.commit()
            except Exception as log_error:
                logger.error(f"Failed to log alert event: {log_error}")
                self.db.rollback()

            return False

    def _format_alert_message(self, alert: AlertRule, price_data: Dict) -> str:
        """
        Format WhatsApp alert notification message.

        Args:
            alert: Alert rule
            price_data: Current stock price data

        Returns:
            str: Formatted message

        Example:
            "🚨 STOCK ALERT: TCS

            Current Price: ₹3,220.00
            Previous Close: ₹3,500.00
            Change: -8.0% ⬇️

            Alert: 8% drop threshold reached
            Alert ID: #42

            This alert will continue monitoring. To stop, use: alert remove 42"
        """
        symbol = alert.stock_symbol
        current = price_data["current_price"]
        previous = price_data["previous_close"]
        change = price_data["percent_change"]

        arrow = "⬇️" if change < 0 else "⬆️"
        change_symbol = "" if change < 0 else "+"

        # Get alert description
        alert_desc = self._get_alert_description(alert)

        message = f"""🚨 STOCK ALERT: {symbol}

Current Price: ₹{current:,.2f}
Previous Close: ₹{previous:,.2f}
Change: {change_symbol}{change:.2f}% {arrow}

Alert: {alert_desc}
Alert ID: #{alert.id}

This alert will continue monitoring. To stop, use: alert remove {alert.id}"""

        return message

    def _get_alert_description(self, alert: AlertRule) -> str:
        """
        Get human-readable alert description.

        Args:
            alert: Alert rule

        Returns:
            str: Alert description
        """
        if alert.alert_type == "drop_7":
            return "7% drop threshold reached"
        elif alert.alert_type == "drop_8":
            return "8% drop threshold reached"
        elif alert.alert_type == "drop_9":
            return "9% drop threshold reached"
        elif alert.alert_type == "drop_10":
            return "10% drop threshold reached"
        elif alert.alert_type == "intraday_1h":
            return "1% intraday movement detected"
        else:
            return f"Custom threshold ({alert.threshold_percent}%) reached"
