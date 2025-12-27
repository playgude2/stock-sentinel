"""
Command Parser

Parses user messages to detect and extract commands for stock price queries
and alert management.

Supported commands:
- price <SYMBOL>                 → Get current stock price
- alert add <SYMBOL> <PERCENT>   → Add price drop alert
- alert add <SYMBOL> intraday    → Add intraday monitoring
- alert list                     → List user's alerts
- alert remove <ID>              → Remove specific alert
- alert remove <SYMBOL>          → Remove all alerts for symbol
- help                           → Show command help
"""

import re
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class Command:
    """Represents a parsed command."""

    name: str  # "price", "alert", "help"
    action: str  # "add", "list", "remove" (for alert command)
    args: List[str]  # Additional arguments
    raw_text: str  # Original message text

    def __repr__(self):
        return f"<Command(name={self.name}, action={self.action}, args={self.args})>"


class CommandParser:
    """Parser for extracting commands from user messages."""

    # Command patterns
    COMMAND_KEYWORDS = ["price", "alert", "help"]
    ALERT_ACTIONS = ["add", "list", "remove", "delete"]

    def is_command(self, text: str) -> bool:
        """
        Check if the message is a command.

        Args:
            text: User message text

        Returns:
            bool: True if message starts with a command keyword
        """
        text_lower = text.strip().lower()
        return any(text_lower.startswith(cmd) for cmd in self.COMMAND_KEYWORDS)

    def parse(self, text: str) -> Optional[Command]:
        """
        Parse a command from user message.

        Args:
            text: User message text

        Returns:
            Command object if parsed successfully, None otherwise

        Examples:
            "price TCS" → Command(name="price", action="", args=["TCS"])
            "alert add TCS -8" → Command(name="alert", action="add", args=["TCS", "-8"])
            "alert list" → Command(name="alert", action="list", args=[])
        """
        text = text.strip()
        text_lower = text.lower()
        parts = text.split()

        if not parts:
            return None

        command_name = parts[0].lower()

        # Price command: "price TCS"
        if command_name == "price":
            if len(parts) < 2:
                return None  # Missing symbol
            symbol = parts[1].upper()
            return Command(name="price", action="", args=[symbol], raw_text=text)

        # Alert commands: "alert add TCS -8", "alert list", "alert remove 1"
        elif command_name == "alert":
            if len(parts) < 2:
                return None  # Missing action

            action = parts[1].lower()
            if action not in self.ALERT_ACTIONS:
                return None  # Invalid action

            # "alert list"
            if action == "list":
                return Command(name="alert", action="list", args=[], raw_text=text)

            # "alert add TCS -8" or "alert add TCS intraday"
            elif action == "add":
                if len(parts) < 4:
                    return None  # Missing symbol or threshold
                symbol = parts[2].upper()
                threshold_or_type = parts[3]
                return Command(
                    name="alert",
                    action="add",
                    args=[symbol, threshold_or_type],
                    raw_text=text,
                )

            # "alert remove 1" or "alert remove TCS"
            elif action in ["remove", "delete"]:
                if len(parts) < 3:
                    return None  # Missing ID or symbol
                identifier = parts[2]
                return Command(
                    name="alert",
                    action="remove",
                    args=[identifier],
                    raw_text=text,
                )

        # Help command: "help"
        elif command_name == "help":
            return Command(name="help", action="", args=[], raw_text=text)

        return None

    def parse_alert_threshold(self, threshold_str: str) -> Optional[tuple]:
        """
        Parse alert threshold from string.

        Args:
            threshold_str: Threshold string (e.g., "-8", "+8", "8%")

        Returns:
            tuple: (alert_type, threshold_percent) or None if invalid

        Examples:
            "-8" → ("drop_8", -8.0)   - Price drops
            "+8" → ("spike_8", 8.0)   - Price rises
            "8" → ("drop_8", -8.0)    - Defaults to drop
            "-10" → ("drop_10", -10.0)
            "+5" → ("spike_5", 5.0)
        """
        threshold_str = threshold_str.lower().strip()

        # Intraday monitoring (legacy support)
        if threshold_str == "intraday":
            return ("intraday_1h", 1.0)

        # Remove % sign if present
        threshold_str = threshold_str.replace("%", "").strip()

        try:
            # Detect if it's explicitly positive (has + sign)
            is_spike = threshold_str.startswith("+")

            threshold_value = float(threshold_str)

            # Get absolute value for validation
            abs_value = abs(threshold_value)

            # Validate supported thresholds: 5, 7, 8, 9, 10
            if abs_value not in [5.0, 7.0, 8.0, 9.0, 10.0]:
                return None  # Unsupported threshold

            threshold_int = int(abs_value)

            # Determine direction
            if is_spike or (threshold_value > 0 and not threshold_str.startswith("-")):
                # Upward movement (spike/gap up)
                alert_type = f"spike_{threshold_int}"
                return (alert_type, abs_value)
            else:
                # Downward movement (drop/gap down)
                alert_type = f"drop_{threshold_int}"
                return (alert_type, -abs_value)

        except ValueError:
            return None  # Invalid number format

    def parse_alert_identifier(self, identifier: str) -> tuple:
        """
        Parse alert identifier as either ID or symbol.

        Args:
            identifier: Alert ID (numeric) or stock symbol (alphabetic)

        Returns:
            tuple: ("id", int_value) or ("symbol", str_value)

        Examples:
            "1" → ("id", 1)
            "42" → ("id", 42)
            "TCS" → ("symbol", "TCS")
        """
        if identifier.isdigit():
            return ("id", int(identifier))
        else:
            return ("symbol", identifier.upper())
