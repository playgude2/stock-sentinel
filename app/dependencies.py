from twilio.rest import Client as TwilioClient
import redis
from redis import Redis as RedisClient
import google.generativeai as genai
from sqlalchemy.orm import Session

from app.config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    REDIS_HOSTNAME,
    REDIS_PORT,
    GEMINI_APIKEY,
)
from app.database import get_db


def get_twilio_client() -> TwilioClient:
    """
    Dependency to provide a Twilio client instance.

    Returns:
        TwilioClient: A Twilio client configured with the application's credentials.
    """
    return TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def get_redis_client() -> RedisClient:
    """
    Dependency to provide a redis client instance.

    Return:
        RedisClient: A redis client configured with the application's host params.
    """
    return redis.StrictRedis(
        host=REDIS_HOSTNAME,  # Nombre del servicio definido en docker-compose.yml
        port=REDIS_PORT,
        decode_responses=True,
    )


def get_gemini_model() -> genai.GenerativeModel:
    """
    Dependency to provide a Gemini model instance.

    Return:
        GenerativeModel: A Gemini model configured with the application's credential.
    """
    genai.configure(api_key=GEMINI_APIKEY)
    return genai.GenerativeModel('gemini-2.0-flash-exp')


def get_db_session():
    """
    Dependency to provide database session for FastAPI routes.

    Yields:
        Session: SQLAlchemy database session
    """
    return next(get_db())
