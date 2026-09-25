from datetime import datetime
from typing import List, Optional
import uuid

from pydantic import BaseModel, Field


class KPIResponse(BaseModel):
    """KPI statistics for dashboard."""
    total_transactions: int
    fraud_detected: int
    protection_rate: float
    false_positives: float
    avg_risk_score: float
    high_risk_transactions: int


class LiveTransactionResponse(BaseModel):
    """Live transaction data for dashboard."""
    id: uuid.UUID
    created_at: datetime
    amount: float
    currency: str
    transaction_type: str
    sender_id: Optional[str]
    receiver_id: Optional[str]
    risk_score: Optional[int]
    status: str


class RiskTrendPoint(BaseModel):
    """Single point in risk score trend."""
    timestamp: datetime
    avg_risk_score: float
    transaction_count: int


class RiskTrendsResponse(BaseModel):
    """Risk score trends over time."""
    trends: List[RiskTrendPoint]
    period: str  # e.g., "24h", "7d", "30d"


class AlertResponse(BaseModel):
    """Alert data for dashboard."""
    id: uuid.UUID
    transaction_id: uuid.UUID
    created_at: datetime
    severity: str
    rule_name: str
    description: Optional[str]
    is_active: bool
    transaction_amount: Optional[float]
    transaction_type: Optional[str]


class FeedbackRequest(BaseModel):
    """Analyst feedback on alerts."""
    alert_id: uuid.UUID
    analyst_id: str = Field(default="system_analyst")
    feedback_type: str = Field(description="Confirmed Fraud, False Positive, etc.")
    comments: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Feedback response."""
    id: uuid.UUID
    alert_id: uuid.UUID
    analyst_id: str
    feedback_type: str
    comments: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
