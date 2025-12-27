import os

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
TWILIO_TEMPLATE_CONTENT_SID = os.getenv("TWILIO_TEMPLATE_CONTENT_SID")

# Redis Configuration
REDIS_HOSTNAME = os.getenv("REDIS_HOSTNAME")
REDIS_PORT = os.getenv("REDIS_PORT")

# Google Gemini Configuration
GEMINI_APIKEY = os.getenv("GEMINI_APIKEY")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")

# Stock Service Configuration
STOCK_PRICE_CACHE_TTL = int(os.getenv("STOCK_PRICE_CACHE_TTL", "60"))  # Redis cache TTL (seconds)
STOCK_PRICE_DB_CACHE_TTL = int(os.getenv("STOCK_PRICE_DB_CACHE_TTL", "300"))  # DB cache TTL (seconds)

# Alert Configuration
ALERT_CHECK_INTERVAL = int(os.getenv("ALERT_CHECK_INTERVAL", "300"))  # Celery beat interval (seconds)
ALERT_COOLDOWN_PERIOD = int(os.getenv("ALERT_COOLDOWN_PERIOD", "3600"))  # Cooldown period (seconds)

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_PATH = os.getenv("LOG_PATH", "logs/app.log")
