"""
Stock Monitoring Background Tasks

Celery tasks for intraday stock price tracking and alert evaluation:
1. collect_price_snapshots: Runs every 1 minute during market hours
2. check_gap_down_alerts: Runs at 9:15 AM IST to check gap down
3. check_intraday_alerts: Runs every 1-5-15-30 min based on severity
"""

from collections import defaultdict
from datetime import datetime, timedelta
import redis

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.alert_rule import AlertRule
from app.models.intraday_price_snapshot import IntradayPriceSnapshot
from app.services.stock_service import StockPriceService
from app.services.alert_evaluator import AlertEvaluator
from app.services.notification_service import NotificationService
from app.dependencies import get_twilio_client
from app.config import REDIS_HOSTNAME, REDIS_PORT
from app.utils.logger import create_logger
from app.utils.market_hours import is_market_open, get_market_phase, get_current_ist_time

logger = create_logger(__name__)


@celery_app.task(bind=True, max_retries=3)
def collect_price_snapshots(self):
    """
    Collect 1-minute price snapshots for all stocks with active alerts.

    - Runs every 1 minute during market hours (9:15 AM - 3:30 PM IST)
    - Stores snapshots in intraday_price_snapshots table
    - Cleans up snapshots older than 2 hours (rolling window limit)

    These snapshots power the rolling window alert calculations.
    """
    db = SessionLocal()
    redis_client = None

    try:
        # Check if market is open
        if not is_market_open():
            logger.debug("Market is closed, skipping price snapshot collection")
            return {"status": "skipped", "reason": "market_closed"}

        logger.info("Collecting 1-minute price snapshots")

        # Initialize Redis client
        redis_client = redis.StrictRedis(
            host=REDIS_HOSTNAME,
            port=REDIS_PORT,
            decode_responses=True,
        )

        # Get unique stock symbols from active alerts
        active_alerts = (
            db.query(AlertRule.stock_symbol)
            .filter(AlertRule.is_active == True)
            .distinct()
            .all()
        )

        if not active_alerts:
            logger.info("No active alerts, skipping snapshot collection")
            return {"status": "success", "snapshots_collected": 0}

        unique_symbols = [symbol[0] for symbol in active_alerts]
        logger.info(f"Collecting snapshots for {len(unique_symbols)} stock(s)")

        # Initialize stock service
        stock_service = StockPriceService(db, redis_client)

        snapshots_collected = 0
        now = get_current_ist_time()
        market_phase = get_market_phase()

        # Collect price snapshot for each stock
        for symbol in unique_symbols:
            try:
                price_data = stock_service.get_current_price(symbol)

                if not price_data:
                    logger.warning(f"Failed to fetch price for {symbol}")
                    continue

                # Create snapshot
                snapshot = IntradayPriceSnapshot(
                    stock_symbol=symbol,
                    ticker_symbol=price_data["ticker_symbol"],
                    price=price_data["current_price"],
                    open_price=price_data.get("open_price"),
                    previous_close=price_data.get("previous_close"),
                    snapshot_time=now,
                    market_phase=market_phase,
                    is_gap_down_checked=False,
                    created_at=datetime.utcnow(),
                )

                db.add(snapshot)
                snapshots_collected += 1

                logger.debug(
                    f"Snapshot: {symbol} = ₹{price_data['current_price']:.2f} @ {now.strftime('%H:%M')}"
                )

            except Exception as e:
                logger.error(f"Error collecting snapshot for {symbol}: {e}")
                continue

        # Commit all snapshots
        db.commit()

        # Clean up old snapshots (older than 2 hours)
        cleanup_cutoff = now - timedelta(hours=2)
        deleted_count = (
            db.query(IntradayPriceSnapshot)
            .filter(IntradayPriceSnapshot.snapshot_time < cleanup_cutoff)
            .delete()
        )

        if deleted_count > 0:
            db.commit()
            logger.info(f"Cleaned up {deleted_count} old snapshot(s)")

        logger.info(f"Collected {snapshots_collected} price snapshot(s)")

        return {
            "status": "success",
            "snapshots_collected": snapshots_collected,
            "old_snapshots_deleted": deleted_count,
        }

    except Exception as e:
        logger.error(f"Error in price snapshot collection: {e}", exc_info=True)
        db.rollback()
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()
        if redis_client:
            redis_client.close()


@celery_app.task(bind=True, max_retries=3)
def check_gap_down_alerts(self):
    """
    Check gap alerts at market open (9:15 AM IST).

    Compares today's open price vs yesterday's close price.
    Triggers alerts for:
    - Gap downs: 5%, 7%, 8%, 9%, 10% drops
    - Gap ups: 5%, 7%, 8%, 9%, 10% rises

    This task should run ONCE per day at 9:15 AM.
    """
    db = SessionLocal()
    redis_client = None
    twilio_client = None

    try:
        logger.info("Checking gap alerts (gap down and gap up)")

        # Check if market is open
        if not is_market_open():
            logger.debug("Market is closed, skipping gap check")
            return {"status": "skipped", "reason": "market_closed"}

        # Initialize clients
        redis_client = redis.StrictRedis(
            host=REDIS_HOSTNAME,
            port=REDIS_PORT,
            decode_responses=True,
        )
        twilio_client = get_twilio_client()

        # Get all active gap alerts (both down and up)
        gap_alerts = (
            db.query(AlertRule)
            .filter(
                AlertRule.is_active == True,
                (AlertRule.alert_type.like("gap_down_%") | AlertRule.alert_type.like("gap_up_%"))
            )
            .all()
        )

        if not gap_alerts:
            logger.info("No active gap alerts")
            return {"status": "success", "alerts_checked": 0}

        logger.info(f"Checking {len(gap_alerts)} gap alert(s) (down and up)")

        # Group by stock symbol
        alerts_by_symbol = defaultdict(list)
        for alert in gap_alerts:
            alerts_by_symbol[alert.stock_symbol].append(alert)

        # Initialize services
        stock_service = StockPriceService(db, redis_client)
        evaluator = AlertEvaluator(db)
        notifier = NotificationService(twilio_client, db)

        notifications_sent = 0
        alerts_triggered = 0

        # Check each symbol
        for symbol, alerts in alerts_by_symbol.items():
            try:
                price_data = stock_service.get_current_price(symbol)

                if not price_data:
                    logger.warning(f"Failed to fetch price for {symbol}")
                    continue

                # Evaluate each alert
                for alert in alerts:
                    try:
                        if evaluator.should_trigger(alert, price_data):
                            alerts_triggered += 1

                            if notifier.can_send_notification(alert):
                                success = notifier.send_alert_notification(alert, price_data)

                                if success:
                                    notifications_sent += 1

                        alert.last_checked_at = datetime.utcnow()

                    except Exception as e:
                        logger.error(f"Error processing alert {alert.id}: {e}")
                        continue

                db.commit()

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                db.rollback()
                continue

        logger.info(
            f"Gap alert check completed: "
            f"checked={len(gap_alerts)}, triggered={alerts_triggered}, sent={notifications_sent}"
        )

        return {
            "status": "success",
            "alerts_checked": len(gap_alerts),
            "alerts_triggered": alerts_triggered,
            "notifications_sent": notifications_sent,
        }

    except Exception as e:
        logger.error(f"Error in gap alert check: {e}", exc_info=True)
        db.rollback()
        raise self.retry(exc=e, countdown=300)

    finally:
        db.close()
        if redis_client:
            redis_client.close()


@celery_app.task(bind=True, max_retries=3)
def check_intraday_alerts(self):
    """
    Check intraday rolling window alerts (1-hour and 2-hour).

    - Runs every 1-5-15-30 minutes based on alert severity
    - Only during market hours (9:15 AM - 3:30 PM IST)
    - Evaluates alerts against rolling window price data

    Dynamic frequency:
    - 10%+ alerts: Every 1 minute (urgent)
    - 7-9% alerts: Every 5 minutes (warning)
    - <7% alerts: Every 15 minutes (normal)
    """
    db = SessionLocal()
    redis_client = None
    twilio_client = None

    try:
        # Check if market is open
        if not is_market_open():
            logger.debug("Market is closed, skipping intraday alert check")
            return {"status": "skipped", "reason": "market_closed"}

        logger.info("Checking intraday rolling window alerts (drops and spikes)")

        # Initialize clients
        redis_client = redis.StrictRedis(
            host=REDIS_HOSTNAME,
            port=REDIS_PORT,
            decode_responses=True,
        )
        twilio_client = get_twilio_client()

        # Get all active intraday alerts (drops, spikes, and legacy)
        intraday_alerts = (
            db.query(AlertRule)
            .filter(
                AlertRule.is_active == True,
                (AlertRule.alert_type.like("drop_%") |
                 AlertRule.alert_type.like("spike_%") |
                 AlertRule.alert_type.like("intraday_%"))
            )
            .all()
        )

        if not intraday_alerts:
            logger.info("No active intraday alerts")
            return {"status": "success", "alerts_checked": 0}

        # Filter alerts based on check frequency
        now = datetime.utcnow()
        alerts_to_check = []

        for alert in intraday_alerts:
            if alert.last_checked_at is None:
                # First time checking this alert
                alerts_to_check.append(alert)
            else:
                # Check if enough time has passed since last check
                time_since_check = (now - alert.last_checked_at).total_seconds()

                if time_since_check >= alert.check_interval_seconds:
                    alerts_to_check.append(alert)

        if not alerts_to_check:
            logger.debug("No alerts due for checking based on frequency")
            return {"status": "success", "alerts_checked": 0}

        logger.info(f"Checking {len(alerts_to_check)} intraday alert(s) due for evaluation")

        # Group by stock symbol
        alerts_by_symbol = defaultdict(list)
        for alert in alerts_to_check:
            alerts_by_symbol[alert.stock_symbol].append(alert)

        # Initialize services
        stock_service = StockPriceService(db, redis_client)
        evaluator = AlertEvaluator(db)
        notifier = NotificationService(twilio_client, db)

        notifications_sent = 0
        alerts_triggered = 0

        # Check each symbol
        for symbol, alerts in alerts_by_symbol.items():
            try:
                price_data = stock_service.get_current_price(symbol)

                if not price_data:
                    logger.warning(f"Failed to fetch price for {symbol}")
                    continue

                # Evaluate each alert
                for alert in alerts:
                    try:
                        if evaluator.should_trigger(alert, price_data):
                            alerts_triggered += 1

                            if notifier.can_send_notification(alert):
                                success = notifier.send_alert_notification(alert, price_data)

                                if success:
                                    notifications_sent += 1

                        alert.last_checked_at = datetime.utcnow()

                    except Exception as e:
                        logger.error(f"Error processing alert {alert.id}: {e}")
                        continue

                db.commit()

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                db.rollback()
                continue

        logger.info(
            f"Intraday check completed: "
            f"checked={len(alerts_to_check)}, triggered={alerts_triggered}, sent={notifications_sent}"
        )

        return {
            "status": "success",
            "alerts_checked": len(alerts_to_check),
            "alerts_triggered": alerts_triggered,
            "notifications_sent": notifications_sent,
        }

    except Exception as e:
        logger.error(f"Error in intraday alert check: {e}", exc_info=True)
        db.rollback()
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()
        if redis_client:
            redis_client.close()
