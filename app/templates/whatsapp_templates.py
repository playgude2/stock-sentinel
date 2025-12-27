"""
WhatsApp Message Templates and Constants

This module contains template definitions for WhatsApp messages,
including greetings, responses, and interactive message content.
"""

# Greetings that trigger the list picker menu
GREETINGS = [
    "hello",
    "hi",
    "hey",
    "hola",
    "namaste",
    "start",
    "menu",
    "good morning",
    "good afternoon",
    "good evening",
]

# Default response for unrecognized messages
DEFAULT_RESPONSE = (
    "I'm here to help! You can:\n"
    "- Check stock prices: 'price TCS'\n"
    "- Set alerts: 'alert add TCS -8'\n"
    "- List alerts: 'alert list'\n"
    "- Or just chat with me naturally!"
)

# List picker content variables for Twilio interactive messages
LIST_PICKER_CONTENT_VARIABLES = {
    "1": "Welcome! How can I assist you today?",
    "2": "Choose an option from the list below:",
    "3": "Stock Prices",
    "4": "Set Alerts",
    "5": "My Alerts",
    "6": "Help",
}

# Command help text
HELP_TEXT = """📊 *Stock Alert Bot - Commands*

*Get Stock Price:*
• `price TCS` - Get current price of TCS stock
• `price INFY` - Get current price of Infosys

*Set Price Alerts:*
• `alert add TCS -7` - Alert on 7% drop
• `alert add TCS -8` - Alert on 8% drop
• `alert add TCS -9` - Alert on 9% drop
• `alert add TCS -10` - Alert on 10% drop
• `alert add TCS intraday` - 1% movement in 1 hour

*Manage Alerts:*
• `alert list` - View all your active alerts
• `alert remove 123` - Remove alert by ID
• `alert remove TCS` - Remove all TCS alerts

*General:*
• `help` - Show this help message

Alerts are recurring and stay active until you remove them manually.
"""

# Alert notification template
ALERT_NOTIFICATION_TEMPLATE = """🚨 *STOCK ALERT: {symbol}*

Current Price: ₹{current_price:,.2f}
Previous Close: ₹{previous_close:,.2f}
Change: {percent_change:+.2f}% {arrow}

Alert: {alert_description}
Alert ID: #{alert_id}
"""

# Error messages
ERROR_INVALID_COMMAND = "❌ Invalid command format.\n\nType 'help' for usage instructions."
ERROR_UNKNOWN_COMMAND = "❌ Unknown command: {command}\n\nType 'help' for available commands."
ERROR_PROCESSING = "❌ Error processing command. Please try again later."
ERROR_STOCK_NOT_FOUND = "❌ Stock symbol '{symbol}' not found. Please check the symbol and try again."
ERROR_INVALID_THRESHOLD = "❌ Invalid threshold value. Use -7, -8, -9, -10, or 'intraday'."
ERROR_ALERT_NOT_FOUND = "❌ Alert not found with ID: {alert_id}"
ERROR_NO_ALERTS = "You don't have any active alerts.\n\nCreate one with: alert add TCS -8"

# Success messages
SUCCESS_ALERT_CREATED = "✅ *Alert Created Successfully*\n\nStock: {symbol}\nType: {alert_type}\nYou'll be notified when the condition is met.\n\nAlert ID: #{alert_id}"
SUCCESS_ALERT_REMOVED = "✅ Alert removed successfully (ID: #{alert_id})"
SUCCESS_ALERTS_REMOVED = "✅ Removed {count} alert(s) for {symbol}"
