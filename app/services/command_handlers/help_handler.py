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
        return """👋 *Hi! I'm your Stock Alert Bot*

📊 *Check Stock Price*
Just type: `price TCS`
I'll show you the latest price and how much it changed today!

🚨 *Set Up Alerts*
I'll notify you when stocks hit your targets:

*Price Drops 📉*
`alert add TCS -8`
→ I'll alert you if TCS drops 8% (works with -7, -8, -9, -10)

*Price Spikes 📈*
`alert add TCS +8`
→ I'll alert you if TCS jumps 8% (works with +5, +7, +8, +9, +10)

*Intraday Moves ⚡*
`alert add INFY intraday`
→ Get notified on 1% moves within 1 hour

*See Your Alerts 📋*
`alert list`
→ Shows all your active alerts

*Remove Alerts 🗑️*
`alert remove 42` - Remove alert #42
`alert remove TCS` - Remove all TCS alerts

📱 *Ask Me Anything!*
You can also just chat normally - I'll understand!

💡 *Good to know:*
• Alerts work during market hours (9:15 AM - 3:30 PM IST)
• I monitor stocks every minute
• Your alerts stay active until you remove them"""
