from typing import Optional

from fastapi import Form
from pydantic import BaseModel, Field


class WhatsAppMessage(BaseModel):
    SmsMessageSid: Optional[str] = Field(
        None, description="Unique identifier for the SMS message."
    )
    NumMedia: Optional[int] = Field(None, description="Number of media attachments.")
    ProfileName: Optional[str] = Field(None, description="Profile name of the sender.")
    MessageType: Optional[str] = Field(None, description="Type of the message (e.g., text).")
    SmsSid: Optional[str] = Field(None, description="Unique identifier for the SMS.")
    WaId: Optional[str] = Field(None, description="WhatsApp ID of the sender.")
    SmsStatus: Optional[str] = Field(None, description="Status of the SMS (e.g., received).")
    Body: str = Field(..., description="Body of the message.")
    To: str = Field(..., description="Recipient's phone number in WhatsApp format.")
    NumSegments: Optional[int] = Field(None, description="Number of segments in the SMS.")
    ReferralNumMedia: Optional[int] = Field(
        None, description="Number of referral media attachments."
    )
    MessageSid: str = Field(..., description="Unique identifier for the message.")
    AccountSid: Optional[str] = Field(None, description="Account SID associated with the message.")
    From: str = Field(..., description="Sender's phone number in WhatsApp format.")
    ApiVersion: Optional[str] = Field(None, description="API version used to send the message.")

    @classmethod
    def as_form(
        cls,
        SmsMessageSid: Optional[str] = Form(None),
        NumMedia: Optional[int] = Form(None),
        ProfileName: Optional[str] = Form(None),
        MessageType: Optional[str] = Form(None),
        SmsSid: Optional[str] = Form(None),
        WaId: Optional[str] = Form(None),
        SmsStatus: Optional[str] = Form(None),
        Body: str = Form(...),
        To: str = Form(...),
        NumSegments: Optional[int] = Form(None),
        ReferralNumMedia: Optional[int] = Form(None),
        MessageSid: str = Form(...),
        AccountSid: Optional[str] = Form(None),
        From: str = Form(...),
        ApiVersion: Optional[str] = Form(None),
    ):
        """
        A helper method to parse form-encoded data into the model.
        """
        return cls(
            SmsMessageSid=SmsMessageSid,
            NumMedia=NumMedia,
            ProfileName=ProfileName,
            MessageType=MessageType,
            SmsSid=SmsSid,
            WaId=WaId,
            SmsStatus=SmsStatus,
            Body=Body,
            To=To,
            NumSegments=NumSegments,
            ReferralNumMedia=ReferralNumMedia,
            MessageSid=MessageSid,
            AccountSid=AccountSid,
            From=From,
            ApiVersion=ApiVersion,
        )
