from fastapi.testclient import TestClient

from app.main import app
from app.routers.whatsapp import get_message_processor
from app.utils.logger import create_logger

logger = create_logger(__name__)


# Mock function to replace the real process_message during testing
def mock_process_message(from_number: str, body: str, to_number: str):
    logger.info(f"Mocked processing: {from_number}, {body}, {to_number}")


# Override the dependency
app.dependency_overrides[get_message_processor] = lambda: mock_process_message

client = TestClient(app)


def test_whatsapp_webhook():
    response = client.post(
        "/whatsapp",
        data={
            "SmsMessageSid": "SM123456",
            "NumMedia": "0",
            "ProfileName": "Mike",
            "MessageType": "text",
            "SmsSid": "SM123456",
            "WaId": "123456789",
            "SmsStatus": "received",
            "Body": "Hello",
            "To": "whatsapp:+14123456789",
            "NumSegments": "1",
            "ReferralNumMedia": "0",
            "MessageSid": "SM123456",
            "AccountSid": "AC123456",
            "From": "whatsapp:+34123456789",
            "ApiVersion": "2010-04-01",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Response sent successfully"}
