"""
Alert Command Handler

Handles alert management commands:
- alert add <SYMBOL> <PERCENT> - Create new alert
- alert list - List user's alerts
- alert remove <ID|SYMBOL> - Remove alert(s)
"""

from datetime import datetime
from sqlalchemy.orm import Session

from app.services.command_handlers.base import BaseCommandHandler
from app.services.command_parser import Command, CommandParser
from app.models.user import User
from app.models.alert_rule import AlertRule
from app.utils.logger import create_logger

logger = create_logger(__name__)


class AlertHandler(BaseCommandHandler):
    """Handler for alert management commands."""

    def handle(self, command: Command, user_phone: str) -> str:
        """
        Handle alert command based on action.

        Args:
            command: Parsed alert command
            user_phone: User's WhatsApp phone number

        Returns:
            str: Response message
        """
        action = command.action

        if action == "add":
            return self._handle_add(command, user_phone)
        elif action == "list":
            return self._handle_list(user_phone)
        elif action == "remove":
            return self._handle_remove(command, user_phone)
        else:
            return "❌ Invalid alert command.\n\nType 'help' for usage instructions."

    def _handle_add(self, command: Command, user_phone: str) -> str:
        """
        Add a new alert rule.

        Args:
            command: Command with args=[symbol, threshold_or_type]
            user_phone: User's phone number

        Returns:
            str: Confirmation or error message
        """
        try:
            if len(command.args) < 2:
                return "❌ Missing arguments.\n\nUsage: alert add <SYMBOL> <PERCENT>\nExample: alert add TCS -8 (drop) or alert add TCS +8 (spike)"

            symbol = command.args[0].upper()
            threshold_str = command.args[1]

            # Parse threshold
            parser = CommandParser()
            threshold_result = parser.parse_alert_threshold(threshold_str)

            if not threshold_result:
                return f"❌ Invalid threshold: {threshold_str}\n\nSupported:\n- Drops: -5, -7, -8, -9, -10\n- Spikes: +5, +7, +8, +9, +10"

            alert_type, threshold_percent = threshold_result

            # Get or create user
            user = self._get_or_create_user(user_phone)

            # Check if user already has alerts for this symbol and threshold
            threshold_pct_int = abs(int(threshold_percent))
            existing_alerts = (
                self.db.query(AlertRule)
                .filter(
                    AlertRule.user_id == user.id,
                    AlertRule.stock_symbol == symbol,
                    AlertRule.threshold_percent == threshold_percent,
                    AlertRule.is_active == True,
                )
                .all()
            )

            if existing_alerts:
                alert_ids = [str(alert.id) for alert in existing_alerts]
                direction = "drop" if threshold_percent < 0 else "spike"
                return f"⚠️ You already have active {threshold_pct_int}% {direction} alerts for {symbol}.\n\nAlert IDs: #{', #'.join(alert_ids)}\n\nUse 'alert remove TCS' to remove all alerts for this stock."

            # Create THREE alerts based on direction
            threshold_pct_int = abs(int(threshold_percent))
            is_drop = threshold_percent < 0  # True for drops, False for spikes

            # Determine check frequency based on severity
            if threshold_pct_int >= 10:
                check_interval = 300  # 5 minutes
            elif threshold_pct_int >= 7:
                check_interval = 900  # 15 minutes
            else:
                check_interval = 1800  # 30 minutes

            created_alerts = []

            # 1. Gap Alert (Gap Down for drops, Gap Up for spikes)
            gap_type = f"gap_down_{threshold_pct_int}" if is_drop else f"gap_up_{threshold_pct_int}"
            gap_label = "Gap Down" if is_drop else "Gap Up"

            gap_alert = AlertRule(
                user_id=user.id,
                stock_symbol=symbol,
                alert_type=gap_type,
                threshold_percent=threshold_percent,
                check_interval_seconds=check_interval,
                is_active=True,
                created_at=datetime.utcnow(),
            )
            self.db.add(gap_alert)
            created_alerts.append((gap_label, gap_alert))

            # 2. 1-Hour Rolling Window Alert (Drop from high OR Spike from low)
            window_1h_type = f"drop_1h_{threshold_pct_int}" if is_drop else f"spike_1h_{threshold_pct_int}"
            window_1h_label = "1-Hour Drop" if is_drop else "1-Hour Spike"

            window_1h_alert = AlertRule(
                user_id=user.id,
                stock_symbol=symbol,
                alert_type=window_1h_type,
                threshold_percent=threshold_percent,
                check_interval_seconds=check_interval,
                is_active=True,
                created_at=datetime.utcnow(),
            )
            self.db.add(window_1h_alert)
            created_alerts.append((window_1h_label, window_1h_alert))

            # 3. 2-Hour Rolling Window Alert (Drop from high OR Spike from low)
            window_2h_type = f"drop_2h_{threshold_pct_int}" if is_drop else f"spike_2h_{threshold_pct_int}"
            window_2h_label = "2-Hour Drop" if is_drop else "2-Hour Spike"

            window_2h_alert = AlertRule(
                user_id=user.id,
                stock_symbol=symbol,
                alert_type=window_2h_type,
                threshold_percent=threshold_percent,
                check_interval_seconds=check_interval,
                is_active=True,
                created_at=datetime.utcnow(),
            )
            self.db.add(window_2h_alert)
            created_alerts.append((window_2h_label, window_2h_alert))

            self.db.commit()

            # Refresh all alerts to get IDs
            for _, alert in created_alerts:
                self.db.refresh(alert)

            logger.info(
                f"Created 3 alerts for user={user_phone}, symbol={symbol}, "
                f"threshold={threshold_pct_int}%, IDs={[a.id for _, a in created_alerts]}"
            )

            # Format check frequency
            if check_interval == 300:
                freq_desc = "5 minutes (urgent)"
            elif check_interval == 900:
                freq_desc = "15 minutes"
            else:
                freq_desc = "30 minutes"

            # Build alert summary
            direction_word = "drop" if is_drop else "spike"
            alert_summary = "\n".join([
                f"• #{alert.id}: {name} ({threshold_pct_int}% {direction_word})"
                for name, alert in created_alerts
            ])

            # Build description based on direction
            if is_drop:
                description = f"""📊 What these alerts do:
1️⃣ Gap Down: Triggers if stock opens {threshold_pct_int}% below yesterday's close
2️⃣ 1-Hour Drop: Triggers if stock drops {threshold_pct_int}% from highest price in last 60 min
3️⃣ 2-Hour Drop: Triggers if stock drops {threshold_pct_int}% from highest price in last 120 min"""
            else:
                description = f"""📊 What these alerts do:
1️⃣ Gap Up: Triggers if stock opens {threshold_pct_int}% above yesterday's close
2️⃣ 1-Hour Spike: Triggers if stock rises {threshold_pct_int}% from lowest price in last 60 min
3️⃣ 2-Hour Spike: Triggers if stock rises {threshold_pct_int}% from lowest price in last 120 min"""

            return f"""✅ 3 Alerts created successfully!

Stock: {symbol}
Threshold: {threshold_pct_int}% {direction_word}
Check Frequency: Every {freq_desc}

{alert_summary}

{description}

⏰ Alerts run during market hours only (9:15 AM - 3:30 PM IST)
♻️ Alerts stay active until you remove them

Type 'alert list' to see all your alerts."""

        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            self.db.rollback()
            return "❌ Error creating alert. Please try again later."

    def _handle_list(self, user_phone: str) -> str:
        """
        List all active alerts for user.

        Args:
            user_phone: User's phone number

        Returns:
            str: List of alerts or empty message
        """
        try:
            user = self._get_user(user_phone)

            if not user:
                return "📋 You don't have any alerts yet.\n\nType 'help' to see how to create alerts."

            alerts = (
                self.db.query(AlertRule)
                .filter(AlertRule.user_id == user.id, AlertRule.is_active == True)
                .order_by(AlertRule.created_at.desc())
                .all()
            )

            if not alerts:
                return "📋 You don't have any active alerts.\n\nType 'help' to see how to create alerts."

            response = "📋 *Your Active Alerts*\n\n"

            for alert in alerts:
                # Format alert type
                percent = abs(int(alert.threshold_percent))

                # Gap alerts
                if alert.alert_type.startswith("gap_down_"):
                    alert_desc = f"Gap Down {percent}%"
                elif alert.alert_type.startswith("gap_up_"):
                    alert_desc = f"Gap Up {percent}%"
                # Drop alerts (rolling window downward)
                elif alert.alert_type.startswith("drop_1h_"):
                    alert_desc = f"1h Drop {percent}%"
                elif alert.alert_type.startswith("drop_2h_"):
                    alert_desc = f"2h Drop {percent}%"
                # Spike alerts (rolling window upward)
                elif alert.alert_type.startswith("spike_1h_"):
                    alert_desc = f"1h Spike {percent}%"
                elif alert.alert_type.startswith("spike_2h_"):
                    alert_desc = f"2h Spike {percent}%"
                # Legacy intraday alerts
                elif alert.alert_type.startswith("intraday_1h_"):
                    alert_desc = f"1h Intraday {percent}%"
                elif alert.alert_type.startswith("intraday_2h_"):
                    alert_desc = f"2h Intraday {percent}%"
                else:
                    alert_desc = f"{percent}%"

                # Format last checked time
                if alert.last_checked_at:
                    last_check = alert.last_checked_at.strftime("%H:%M")
                    check_info = f" • {last_check}"
                else:
                    check_info = ""

                response += f"#{alert.id} • {alert.stock_symbol} • {alert_desc}{check_info}\n"

            response += f"\n📊 Total: {len(alerts)} alert(s)"
            response += "\n\nTo remove: `alert remove <ID>` or `alert remove TCS`"

            return response

        except Exception as e:
            logger.error(f"Error listing alerts: {e}")
            return "❌ Error retrieving alerts. Please try again later."

    def _handle_remove(self, command: Command, user_phone: str) -> str:
        """
        Remove alert(s) by ID or symbol.

        Args:
            command: Command with args=[identifier]
            user_phone: User's phone number

        Returns:
            str: Confirmation or error message
        """
        try:
            if not command.args:
                return "❌ Please specify alert ID or symbol.\n\nUsage: alert remove <ID>\nExample: alert remove 42"

            identifier = command.args[0]
            user = self._get_user(user_phone)

            if not user:
                return "❌ No alerts found."

            parser = CommandParser()
            id_type, value = parser.parse_alert_identifier(identifier)

            if id_type == "id":
                # Remove specific alert by ID
                alert = (
                    self.db.query(AlertRule)
                    .filter(AlertRule.id == value, AlertRule.user_id == user.id, AlertRule.is_active == True)
                    .first()
                )

                if not alert:
                    return f"❌ Alert #{value} not found or already removed."

                alert.is_active = False
                self.db.commit()

                logger.info(f"Alert removed: ID={alert.id}, user={user_phone}")

                return f"✅ Alert #{alert.id} for {alert.stock_symbol} removed successfully."

            elif id_type == "symbol":
                # Remove all alerts for symbol
                symbol = value
                alerts = (
                    self.db.query(AlertRule)
                    .filter(AlertRule.user_id == user.id, AlertRule.stock_symbol == symbol, AlertRule.is_active == True)
                    .all()
                )

                if not alerts:
                    return f"❌ No active alerts found for {symbol}."

                count = len(alerts)
                for alert in alerts:
                    alert.is_active = False

                self.db.commit()

                logger.info(f"Alerts removed: count={count}, user={user_phone}, symbol={symbol}")

                return f"✅ {count} alert(s) for {symbol} removed successfully."

        except Exception as e:
            logger.error(f"Error removing alert: {e}")
            self.db.rollback()
            return "❌ Error removing alert. Please try again later."

    def _get_or_create_user(self, phone_number: str) -> User:
        """
        Get existing user or create new one.

        Args:
            phone_number: User's WhatsApp phone number

        Returns:
            User: User object
        """
        user = self.db.query(User).filter(User.phone_number == phone_number).first()

        if not user:
            user = User(phone_number=phone_number, created_at=datetime.utcnow(), is_active=True)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"New user created: {phone_number}")

        return user

    def _get_user(self, phone_number: str) -> User:
        """
        Get existing user.

        Args:
            phone_number: User's WhatsApp phone number

        Returns:
            User: User object or None if not found
        """
        return self.db.query(User).filter(User.phone_number == phone_number).first()
