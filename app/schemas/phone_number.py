from pydantic import BaseModel, Field, field_validator
import re


class PhoneNumber(BaseModel):
    phone: str = Field(
        ...,
        description="A valid WhatsApp phone number in the format 'whatsapp:+12345678912'.",
    )

    @field_validator("phone")
    def validate_phone(cls, value):
        # Regular expression pattern for validating the phone number
        pattern = r"^whatsapp:\+\d{10,15}$"

        # Check if the phone number matches the pattern
        if not re.match(pattern, value):
            raise ValueError(
                'Must be a valid WhatsApp phone number in the format "whatsapp:+12345678912".'
            )
        return value
