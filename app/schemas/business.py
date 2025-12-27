from typing import List, Annotated
from pydantic import BaseModel, Field
from app.schemas.phone_number import PhoneNumber


class Service(BaseModel):
    service_name: Annotated[
        str,
        Field(
            max_length=24,
            description="Name of the service (maximum 24 characters).",
            example="Service 1",
        ),
    ]
    service_id: Annotated[
        str,
        Field(
            max_length=200,
            description="Unique identifier for the service (maximum 200 characters).",
            example="service_1_unique_id",
        ),
    ]
    service_description: Annotated[
        str,
        Field(
            max_length=72,
            description="Short description of the service (maximum 72 characters).",
            example="Brief description of service 1",
        ),
    ]
    service_price: Annotated[
        str,
        Field(
            max_length=15,
            description="Price of the service (maximum 15 characters).",
            example="50€",
        ),
    ]
    service_duration_minutes: Annotated[
        int, Field(ge=0, description="Duration of the service in minutes.", example=30)
    ]


class ServiceSelector(BaseModel):
    body: Annotated[
        str,
        Field(
            max_length=1600,
            description="Welcome message (maximum 1600 characters).",
            example="Welcome to Business Name. We are here to assist you with our services.",
        ),
    ]
    button_text: Annotated[
        str,
        Field(
            max_length=20,
            description="Button text to list services (maximum 20 characters).",
            example="List services",
        ),
    ]
    services: Annotated[List[Service], Field(description="List of services offered.")]


class Business(BaseModel):
    business_id: Annotated[
        str,
        Field(
            max_length=200,
            description="Unique identifier for the business.",
            example="business_12345",
        ),
    ]
    business_name: Annotated[
        str,
        Field(
            max_length=100, description="Name of the business.", example="Business Name"
        ),
    ]
    business_type: Annotated[
        str,
        Field(
            max_length=50, description="Type of business.", example="Health and Beauty"
        ),
    ]
    phone_number: PhoneNumber
    service_selector: ServiceSelector
