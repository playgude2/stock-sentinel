"""
Celery Application Configuration

Configures Celery for background task processing with Redis broker.
Defines beat schedule for periodic stock alert monitoring.
"""

from celery import Celery
from app.config import REDIS_HOSTNAME, REDIS_PORT, ALERT_CHECK_INTERVAL

# Create Celery app
celery_app = Celery(
    "stock_alerts",
    broker=f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/1",  # Redis DB 1 for Celery
    backend=f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/1",
    include=["app.tasks.stock_monitoring"],  # Import task modules
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (prevent memory leaks)
)

# Beat schedule (periodic tasks)
celery_app.conf.beat_schedule = {
    # Collect 1-minute price snapshots during market hours
    "collect-price-snapshots": {
        "task": "app.tasks.stock_monitoring.collect_price_snapshots",
        "schedule": 60.0,  # Every 1 minute
        "options": {
            "expires": 55,  # Task expires if not picked up within 55 seconds
        },
    },

    # Check gap down alerts at market open (9:15 AM IST = 3:45 AM UTC)
    "check-gap-down-alerts": {
        "task": "app.tasks.stock_monitoring.check_gap_down_alerts",
        "schedule": 300.0,  # Every 5 minutes (will self-check market hours)
        "options": {
            "expires": 240,  # Task expires if not picked up within 4 minutes
        },
    },

    # Check intraday rolling window alerts (1-hour, 2-hour)
    "check-intraday-alerts": {
        "task": "app.tasks.stock_monitoring.check_intraday_alerts",
        "schedule": 60.0,  # Every 1 minute (tasks filter by their own frequency)
        "options": {
            "expires": 55,  # Task expires if not picked up within 55 seconds
        },
    },
}

if __name__ == "__main__":
    celery_app.start()
