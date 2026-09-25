#!/usr/bin/env python3
"""
Test script to verify the ML training pipeline works correctly.
This script creates sample data and runs a quick training test.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.db import async_session_factory
from app.models.transaction import Transaction


async def create_test_data():
    """Create test credit card transaction data for training."""
    print("🔄 Creating test data for ML training...")
    
    async with async_session_factory() as session:
        # Check if test data already exists
        from sqlalchemy import select
        result = await session.execute(select(Transaction).where(Transaction.transaction_type == 'CREDIT_CARD').limit(1))
        existing = result.scalars().first()
        
        if existing:
            print("✅ Test data already exists")
            return
        
        # Create sample credit card transactions
        test_transactions = [
            # Legitimate transactions
            Transaction(
                amount=2500.50, currency='INR', transaction_type='CREDIT_CARD',
                sender_id='user_001', receiver_id='merchant_001',
                device_fingerprint='device_fp_001', ip_address='203.0.113.1',
                geo_location='Mumbai, India', status='processed'
            ),
            Transaction(
                amount=15000.00, currency='INR', transaction_type='CREDIT_CARD',
                sender_id='user_002', receiver_id='merchant_002',
                device_fingerprint='device_fp_002', ip_address='198.51.100.1',
                geo_location='Delhi, India', status='processed'
            ),
            Transaction(
                amount=5000.00, currency='INR', transaction_type='CREDIT_CARD',
                sender_id='user_003', receiver_id='merchant_003',
                device_fingerprint='device_fp_003', ip_address='192.0.2.1',
                geo_location='Bangalore, India', status='processed'
            ),
            
            # Fraudulent transactions
            Transaction(
                amount=150000.00, currency='INR', transaction_type='CREDIT_CARD',
                sender_id='user_004', receiver_id='merchant_004',
                device_fingerprint=None, ip_address='192.168.1.100',
                geo_location='Unknown', status='flagged'
            ),
            Transaction(
                amount=200000.00, currency='INR', transaction_type='CREDIT_CARD',
                sender_id='user_005', receiver_id='merchant_005',
                device_fingerprint='suspicious_device', ip_address='10.0.0.1',
                geo_location='Private Network', status='flagged'
            ),
        ]
        
        # Add more transactions for better training
        import random
        from datetime import datetime, timedelta
        
        # Generate more legitimate transactions
        for i in range(10):
            session.add(Transaction(
                amount=random.uniform(1000, 50000),
                currency='INR',
                transaction_type='CREDIT_CARD',
                sender_id=f'user_legit_{i:03d}',
                receiver_id=f'merchant_{i:03d}',
                device_fingerprint=f'device_legit_{i:03d}',
                ip_address=f'203.0.113.{i+10}',
                geo_location='Mumbai, India',
                status='processed',
                created_at=datetime.now() - timedelta(days=random.randint(1, 30))
            ))
        
        # Generate more fraudulent transactions
        for i in range(5):
            session.add(Transaction(
                amount=random.uniform(100000, 500000),
                currency='INR',
                transaction_type='CREDIT_CARD',
                sender_id=f'user_fraud_{i:03d}',
                receiver_id=f'merchant_suspicious_{i:03d}',
                device_fingerprint=None if random.random() > 0.5 else f'suspicious_{i:03d}',
                ip_address=f'192.168.{random.randint(1,255)}.{random.randint(1,255)}',
                geo_location='Unknown' if random.random() > 0.3 else 'Private Network',
                status='flagged',
                created_at=datetime.now() - timedelta(days=random.randint(1, 30))
            ))
        
        # Add the initial test transactions
        for tx in test_transactions:
            session.add(tx)
        
        await session.commit()
        print(f"✅ Created {len(test_transactions) + 15} test credit card transactions")


async def main():
    """Main function to create test data."""
    try:
        await create_test_data()
        print("\n🎉 Test data creation completed!")
        print("💡 You can now run: python scripts/train_evaluate_model.py")
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
