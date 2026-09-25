#!/usr/bin/env python3
"""
Create comprehensive test data for FortiX fraud detection system.
"""

import asyncio
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.db import async_session_factory
from app.models.transaction import Transaction, Alert
from app.services.fraud_engine import fraud_engine


async def create_comprehensive_test_data():
    """Create comprehensive test data with both legitimate and fraudulent transactions."""
    print("🔄 Creating comprehensive test data...")
    
    async with async_session_factory() as session:
        # Clear existing data
        from sqlalchemy import delete
        await session.execute(delete(Alert))
        await session.execute(delete(Transaction))
        await session.commit()
        
        transactions = []
        
        # Create legitimate transactions (70%)
        for i in range(70):
            transaction = Transaction(
                amount=random.uniform(100, 50000),
                currency='INR',
                transaction_type='CREDIT_CARD',
                sender_id=f'legit_user_{i:03d}',
                receiver_id=f'merchant_{i:03d}',
                device_fingerprint=f'device_legit_{i:03d}',
                ip_address=f'203.0.113.{random.randint(1, 255)}',
                geo_location='Mumbai, India',
                status='processed',
                created_at=datetime.now() - timedelta(hours=random.randint(1, 720))
            )
            transactions.append(transaction)
        
        # Create fraudulent transactions (30%)
        for i in range(30):
            # High amount fraud
            if i < 10:
                amount = random.uniform(100000, 500000)
                ip_address = f'192.168.{random.randint(1, 255)}.{random.randint(1, 255)}'
                device_fingerprint = None  # Missing device fingerprint
                geo_location = 'Unknown'
            # Velocity fraud (multiple transactions)
            elif i < 20:
                amount = random.uniform(50000, 150000)
                ip_address = f'10.0.0.{random.randint(1, 255)}'
                device_fingerprint = 'suspicious_device'
                geo_location = 'Private Network'
            # Anomaly fraud
            else:
                amount = random.uniform(200000, 300000)
                ip_address = f'172.16.{random.randint(1, 255)}.{random.randint(1, 255)}'
                device_fingerprint = 'anomaly_device'
                geo_location = 'Suspicious Location'
            
            transaction = Transaction(
                amount=amount,
                currency='INR',
                transaction_type='CREDIT_CARD',
                sender_id=f'fraud_user_{i:03d}',
                receiver_id=f'suspicious_merchant_{i:03d}',
                device_fingerprint=device_fingerprint,
                ip_address=ip_address,
                geo_location=geo_location,
                status='flagged',
                created_at=datetime.now() - timedelta(hours=random.randint(1, 720))
            )
            transactions.append(transaction)
        
        # Add transactions to database
        for tx in transactions:
            session.add(tx)
            await session.flush()  # Get the ID
            
            # Run fraud detection
            risk_score = await fraud_engine.get_risk_score(tx)
            tx.risk_score = risk_score
            
            # Update status based on risk score
            if risk_score >= 70:
                tx.status = "flagged"
            elif risk_score >= 30:
                tx.status = "review"
            else:
                tx.status = "processed"
            
            # Create alerts if fraud detected
            evaluation = await fraud_engine.evaluate_transaction(tx)
            for alert_data in evaluation["alerts"]:
                alert = Alert(
                    transaction_id=tx.id,
                    severity=alert_data["severity"],
                    rule_name=alert_data["rule_name"],
                    description=alert_data["description"],
                    is_active=True
                )
                session.add(alert)
        
        await session.commit()
        print(f"✅ Created {len(transactions)} comprehensive test transactions")
        
        # Print summary
        flagged_count = sum(1 for tx in transactions if tx.status == 'flagged')
        review_count = sum(1 for tx in transactions if tx.status == 'review')
        processed_count = sum(1 for tx in transactions if tx.status == 'processed')
        
        print(f"📊 Transaction Summary:")
        print(f"  Total transactions: {len(transactions)}")
        print(f"  Flagged (fraud): {flagged_count}")
        print(f"  Under review: {review_count}")
        print(f"  Processed: {processed_count}")


async def main():
    """Main function."""
    print("🚀 Creating Comprehensive Test Data for FortiX")
    print("=" * 60)
    
    try:
        await create_comprehensive_test_data()
        print("\n🎉 Test data creation completed!")
        print("💡 You can now run: python scripts/train_evaluate_model.py")
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
