"""
Price Command Handler

Handles "price <SYMBOL>" commands to fetch current stock prices.
"""

from app.services.command_handlers.base import BaseCommandHandler
from app.services.command_parser import Command
from app.utils.logger import create_logger

logger = create_logger(__name__)


class PriceHandler(BaseCommandHandler):
    """Handler for price query commands."""

    def handle(self, command: Command, user_phone: str) -> str:
        """
        Handle price command.

        Args:
            command: Parsed command with symbol in args[0]
            user_phone: User's WhatsApp phone number

        Returns:
            str: Formatted price information or error message

        Example:
            Command: "price TCS"
            Response: "TCS (TCS.NS)\nCurrent Price: ₹3,450.50\nPrevious Close: ₹3,500.00\nChange: -1.4% ⬇️"
        """
        try:
            if not command.args:
                return "❌ Please specify a stock symbol.\n\nUsage: price <SYMBOL>\nExample: price TCS"

            symbol = command.args[0].upper()
            logger.info(f"Fetching price for {symbol} requested by {user_phone}")

            # Import here to avoid circular dependency
            from app.services.stock_service import StockPriceService

            stock_service = StockPriceService(self.db, self.redis)
            price_data = stock_service.get_current_price(symbol)

            if not price_data:
                return f"❌ Unable to fetch price for {symbol}.\n\nPlease verify the stock symbol and try again."

            # Format response
            current = price_data["current_price"]
            previous = price_data["previous_close"]
            change_percent = price_data["percent_change"]
            ticker = price_data["ticker_symbol"]

            arrow = "⬇️" if change_percent < 0 else "⬆️"
            change_symbol = "" if change_percent < 0 else "+"

            response = f"""📊 {symbol} ({ticker})

Current Price: ₹{current:,.2f}
Previous Close: ₹{previous:,.2f}
Change: {change_symbol}{change_percent:.2f}% {arrow}"""

            logger.info(f"Price fetched successfully for {symbol}: ₹{current}")
            return response

        except Exception as e:
            logger.error(f"Error handling price command: {e}")
            return f"❌ Error fetching price for {symbol}. Please try again later."
