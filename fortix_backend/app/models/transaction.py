from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.db import Base


class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    amount = Column(Float, nullable=False)
    currency = Column(String, default='INR')
    transaction_type = Column(String, nullable=False)  # e.g., 'CREDIT_CARD', 'UPI'
    device_type = Column(String, nullable=True)
    location = Column(String, nullable=True)
    merchant_category = Column(String, nullable=True)
    card_type = Column(String, nullable=True)
    authentication_method = Column(String, nullable=True)
    transaction_distance = Column(Float, nullable=True)
    sender_id = Column(String, index=True)
    receiver_id = Column(String, index=True)
    device_fingerprint = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    geo_location = Column(String, nullable=True)
    risk_score = Column(Integer, nullable=True)
    status = Column(String, default='processed', index=True)  # 'processed', 'flagged'
    
    alerts = relationship("Alert", back_populates="transaction")


class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('transactions.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    severity = Column(String, nullable=False)  # 'Critical', 'High', 'Medium', 'Low'
    rule_name = Column(String, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    transaction = relationship("Transaction", back_populates="alerts")
    feedback = relationship("Feedback", back_populates="alert", uselist=False)


class Feedback(Base):
    __tablename__ = 'feedback'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey('alerts.id'))
    analyst_id = Column(String, default='system_analyst')
    feedback_type = Column(String)  # 'Confirmed Fraud', 'False Positive'
    comments = Column(Text, nullable=True)
    
    alert = relationship("Alert", back_populates="feedback")


