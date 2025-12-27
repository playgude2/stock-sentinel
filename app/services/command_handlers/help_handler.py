"""
Help Command Handler

Handles "help" commands to show available commands and usage instructions.
"""

from app.services.command_handlers.base import BaseCommandHandler
from app.services.command_parser import Command


class HelpHandler(BaseCommandHandler):
    """Handler for help commands."""

    def handle(self, command: Command, user_phone: str) -> str:
        """
        Handle help command.

        Args:
            command: Parsed help command
            user_phone: User's WhatsApp phone number

        Returns:
            str: Help message with command reference
        """
        return """📚 *Command Reference*

*Stock Prices:*
• `price <SYMBOL>` - Get current stock price
  Example: price TCS

*Stock Alerts:*
• `alert add <SYMBOL> <PERCENT>` - Add price drop alert
  Examples:
  - alert add TCS -7
  - alert add TCS -8
  - alert add TCS -9
  - alert add TCS -10

• `alert add <SYMBOL> intraday` - Monitor 1% moves in 1 hour
  Example: alert add INFY intraday

• `alert list` - List your active alerts

• `alert remove <ID>` - Remove specific alert
  Example: alert remove 42

• `alert remove <SYMBOL>` - Remove all alerts for stock
  Example: alert remove TCS

*General:*
• `help` - Show this help message
• Or just chat naturally with me!

---
💡 Tip: Alerts stay active until you remove them."""
