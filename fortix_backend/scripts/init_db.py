#!/usr/bin/env python3
"""
Initialize database and create sample data for FortiX fraud detection system.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.db import async_session_factory, Base, async_engine
from app.models.transaction import Transaction, Alert, Feedback
from app.services.fraud_engine import fraud_engine


async def create_tables():
    """Create database tables."""
    print("🔄 Creating database tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully")


async def create_sample_data():
    """Create sample transaction data."""
    print("🔄 Creating sample transaction data...")
    
    async with async_session_factory() as session:
        # Check if data already exists
        from sqlalchemy import select
        result = await session.execute(select(Transaction).limit(1))
        existing = result.scalars().first()
        
        if existing:
            print("✅ Sample data already exists")
            return
        
        # Create sample transactions
        sample_transactions = [
            # Legitimate transactions
            Transaction(
                amount=2500.50, currency='INR', transaction_type='CREDIT_CARD',
                sender_id='user_001', receiver_id='merchant_001',
                device_fingerprint='device_fp_001', ip_address='203.0.113.1',
                geo_location='Mumbai, India', status='processed'
            ),
            Transaction(
                amount=15000.00, currency='INR', transaction_type='UPI',
                sender_id='user_002', receiver_id='merchant_002',
                device_fingerprint='device_fp_002', ip_address='198.51.100.1',
                geo_location='Delhi, India', status='processed'
            ),
            Transaction(
                amount=5000.00, currency='INR', transaction_type='WALLET',
                sender_id='user_003', receiver_id='merchant_003',
                device_fingerprint='device_fp_003', ip_address='192.0.2.1',
                geo_location='Bangalore, India', status='processed'
            ),
            
            # High-risk transactions
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
        
        # Add transactions and run fraud detection
        for tx in sample_transactions:
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
        print(f"✅ Created {len(sample_transactions)} sample transactions with fraud detection")


async def main():
    """Main function to initialize the system."""
    print("🚀 Initializing FortiX Fraud Detection System")
    print("=" * 50)
    
    try:
        # Create tables
        await create_tables()
        
        # Create sample data
        await create_sample_data()
        
        print("\n" + "=" * 50)
        print("🎉 SYSTEM INITIALIZATION COMPLETED!")
        print("=" * 50)
        print("💡 You can now start the backend server:")
        print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
