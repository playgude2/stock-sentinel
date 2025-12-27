import json
import google.generativeai as genai
from redis import Redis as RedisClient

from twilio.rest import Client
from twilio.rest import Client as TwilioClient

from app.config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_TEMPLATE_CONTENT_SID,
)
from app.utils.logger import create_logger
from app.schemas.phone_number import PhoneNumber
from app.templates.whatsapp_templates import (
    GREETINGS,
    DEFAULT_RESPONSE,
    LIST_PICKER_CONTENT_VARIABLES,
)

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
logger = create_logger(__name__)


def send_list_picker(from_number: PhoneNumber, to_number: PhoneNumber):
    try:
        content_sid = TWILIO_TEMPLATE_CONTENT_SID

        # Se utilizan las variables externas para el contenido
        content_variables = LIST_PICKER_CONTENT_VARIABLES

        message = client.messages.create(
            to=to_number,
            from_=from_number,
            content_sid=content_sid,
            content_variables=json.dumps(content_variables),
        )

        logger.info(f"List picker sent correctly! SID: {message.sid}")
    except Exception as e:
        logger.error(f"Error trying to send the list picker (check twilio CLI): {e}")


def process_message(
    twilio_client: TwilioClient,
    redis_client: RedisClient,
    gemini_model: genai.GenerativeModel,
    from_number: PhoneNumber,
    body: str,
    to_number: PhoneNumber,
    db=None,  # Database session (optional for backward compatibility)
) -> None:
    original_body = body.strip()
    body_lower = original_body.lower()
    logger.info(f"Body retrieved: {original_body}")

    # NEW: Priority 1 - Command Detection
    if db:
        from app.services.command_parser import CommandParser
        from app.services.command_handlers import PriceHandler, AlertHandler, HelpHandler

        parser = CommandParser()
        if parser.is_command(original_body):
            try:
                command = parser.parse(original_body)
                if not command:
                    # Invalid command format
                    error_msg = "❌ Invalid command format.\n\nType 'help' for usage instructions."
                    twilio_client.messages.create(
                        from_=to_number, body=error_msg, to=from_number
                    )
                    return

                # Route to appropriate handler
                if command.name == "price":
                    handler = PriceHandler(db, redis_client, twilio_client)
                elif command.name == "alert":
                    handler = AlertHandler(db, redis_client, twilio_client)
                elif command.name == "help":
                    handler = HelpHandler(db, redis_client, twilio_client)
                else:
                    logger.warning(f"Unknown command: {command.name}")
                    error_msg = f"❌ Unknown command: {command.name}\n\nType 'help' for available commands."
                    twilio_client.messages.create(
                        from_=to_number, body=error_msg, to=from_number
                    )
                    return

                # Handle command
                response = handler.handle(command, from_number)

                # Send response via WhatsApp
                twilio_client.messages.create(
                    from_=to_number, body=response, to=from_number
                )
                logger.info(f"Command '{command.name}' processed successfully for {from_number}")
                return

            except Exception as e:
                logger.error(f"Error processing command: {e}", exc_info=True)
                error_msg = "❌ Error processing command. Please try again later."
                twilio_client.messages.create(
                    from_=to_number, body=error_msg, to=from_number
                )
                return

    # EXISTING: Priority 2 - Greeting Detection
    if any(greeting in body_lower for greeting in GREETINGS):
        logger.info("Mensaje reconocido como saludo. Enviando list picker.")
        send_list_picker(
            from_number=to_number, to_number=from_number
        )  # Enviar el mensaje interactivo con el list picker
    else:
        try:
            # Get conversation history from Redis
            conversation_key = f"conversation:{from_number}"
            history = redis_client.lrange(conversation_key, 0, 9)  # Get last 10 messages

            # Build conversation context
            context = "\n".join(reversed(history)) if history else ""

            # Create prompt with context
            prompt = f"""You are a helpful WhatsApp chatbot assistant. Respond naturally and helpfully to the user's message.

Previous conversation:
{context}

User: {original_body}"""

            # Generate response using Gemini
            logger.info("Generating response with Gemini model...")
            response = gemini_model.generate_content(prompt)
            ai_response = response.text

            # Store conversation in Redis
            redis_client.rpush(conversation_key, f"User: {original_body}")
            redis_client.rpush(conversation_key, f"Bot: {ai_response}")
            redis_client.expire(conversation_key, 3600)  # Expire after 1 hour

            # Send response via WhatsApp
            message = twilio_client.messages.create(
                from_=to_number, body=ai_response, to=from_number
            )
            logger.info(f"Response message generated: {message.body}")
        except Exception as e:
            logger.error(f"Error al enviar el mensaje: {e}")