"""
Base Command Handler

Abstract base class for all command handlers.
"""

from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from redis import Redis as RedisClient
from twilio.rest import Client as TwilioClient

from app.services.command_parser import Command


class BaseCommandHandler(ABC):
    """Abstract base class for command handlers."""

    def __init__(self, db: Session, redis: RedisClient, twilio: TwilioClient):
        """
        Initialize command handler.

        Args:
            db: SQLAlchemy database session
            redis: Redis client for caching
            twilio: Twilio client for WhatsApp messaging
        """
        self.db = db
        self.redis = redis
        self.twilio = twilio

    @abstractmethod
    def handle(self, command: Command, user_phone: str) -> str:
        """
        Handle the command and return response message.

        Args:
            command: Parsed command object
            user_phone: User's WhatsApp phone number

        Returns:
            str: Response message to send to user

        Raises:
            Exception: If command handling fails
        """
        pass
