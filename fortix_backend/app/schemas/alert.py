from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, Field


class AlertBase(BaseModel):
    """Base alert schema."""
    transaction_id: uuid.UUID
    severity: str = Field(description="Critical, High, Medium, Low")
    rule_name: str
    description: Optional[str] = None
    is_active: bool = True


class AlertCreate(AlertBase):
    """Schema for creating alerts."""
    pass


class AlertRead(AlertBase):
    """Schema for reading alerts."""
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class AlertUpdate(BaseModel):
    """Schema for updating alerts."""
    severity: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class FeedbackBase(BaseModel):
    """Base feedback schema."""
    alert_id: uuid.UUID
    analyst_id: str = Field(default="system_analyst")
    feedback_type: str = Field(description="Confirmed Fraud, False Positive, etc.")
    comments: Optional[str] = None


class FeedbackCreate(FeedbackBase):
    """Schema for creating feedback."""
    pass


class FeedbackRead(FeedbackBase):
    """Schema for reading feedback."""
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
