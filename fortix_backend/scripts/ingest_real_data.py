"""
Script to ingest real transaction data for testing and development.
This is a placeholder script that would typically connect to external data sources.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_factory
from app.models.transaction import Transaction


async def create_sample_transactions() -> List[Transaction]:
    """Create sample transaction data for testing."""
    
    sample_transactions = [
        {
            "amount": 2500.50,
            "currency": "INR",
            "transaction_type": "UPI",
            "sender_id": "user_123",
            "receiver_id": "merchant_456",
            "device_fingerprint": "device_fp_abc123",
            "ip_address": "203.0.113.1",
            "geo_location": "Mumbai, India",
            "status": "processed"
        },
        {
            "amount": 150000.00,
            "currency": "INR", 
            "transaction_type": "CREDIT_CARD",
            "sender_id": "user_789",
            "receiver_id": "merchant_101",
            "device_fingerprint": "device_fp_def456",
            "ip_address": "198.51.100.1",
            "geo_location": "Delhi, India",
            "status": "flagged"
        },
        {
            "amount": 50000.00,
            "currency": "INR",
            "transaction_type": "NET_BANKING",
            "sender_id": "user_456",
            "receiver_id": "merchant_202",
            "device_fingerprint": None,  # Missing fingerprint
            "ip_address": "192.168.1.100",  # Private IP
            "geo_location": "Bangalore, India",
            "status": "processed"
        }
    ]
    
    transactions = []
    for tx_data in sample_transactions:
        transaction = Transaction(**tx_data)
        transactions.append(transaction)
    
    return transactions


async def ingest_data():
    """Main function to ingest sample data."""
    
    async with async_session_factory() as session:
        # Check if data already exists
        result = await session.execute(select(Transaction).limit(1))
        existing = result.scalars().first()
        
        if existing:
            print("Sample data already exists. Skipping ingestion.")
            return
        
        # Create sample transactions
        transactions = await create_sample_transactions()
        
        # Add to database
        for transaction in transactions:
            session.add(transaction)
        
        await session.commit()
        print(f"Successfully ingested {len(transactions)} sample transactions.")


async def main():
    """Entry point for the ingestion script."""
    print("Starting data ingestion...")
    await ingest_data()
    print("Data ingestion completed.")


if __name__ == "__main__":
    asyncio.run(main())
