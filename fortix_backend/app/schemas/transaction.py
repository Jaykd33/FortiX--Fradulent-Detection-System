import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TransactionBase(BaseModel):
    amount: float = Field(gt=0)
    currency: str = Field(default="INR")
    transaction_type: str
    sender_id: Optional[str] = None
    receiver_id: Optional[str] = None
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
    geo_location: Optional[str] = None
    risk_score: Optional[int] = None
    status: str = Field(default="processed")


class TransactionCreate(TransactionBase):
    pass


class TransactionRead(TransactionBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


