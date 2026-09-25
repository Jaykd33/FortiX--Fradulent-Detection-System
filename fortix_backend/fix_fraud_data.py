#!/usr/bin/env python3
"""
Fix fraud data by manually creating some flagged transactions.
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.core.db import async_session_factory
from app.models.transaction import Transaction, Alert
from app.services.fraud_engine import fraud_engine


async def fix_fraud_data():
    """Manually create some fraudulent transactions."""
    print("🔄 Fixing fraud data...")
    
    async with async_session_factory() as session:
        # Create some clearly fraudulent transactions
        fraud_transactions = [
            Transaction(
                amount=500000.0,  # Very high amount
                currency='INR',
                transaction_type='CREDIT_CARD',
                sender_id='fraud_user_001',
                receiver_id='suspicious_merchant_001',
                device_fingerprint=None,  # Missing device fingerprint
                ip_address='192.168.1.100',  # Private IP
                geo_location='Unknown',
                status='flagged',
                risk_score=85
            ),
            Transaction(
                amount=750000.0,  # Very high amount
                currency='INR',
                transaction_type='CREDIT_CARD',
                sender_id='fraud_user_002',
                receiver_id='suspicious_merchant_002',
                device_fingerprint='suspicious_device',
                ip_address='10.0.0.1',  # Private IP
                geo_location='Private Network',
                status='flagged',
                risk_score=90
            ),
            Transaction(
                amount=1000000.0,  # Extremely high amount
                currency='INR',
                transaction_type='CREDIT_CARD',
                sender_id='fraud_user_003',
                receiver_id='suspicious_merchant_003',
                device_fingerprint=None,
                ip_address='172.16.0.1',  # Private IP
                geo_location='Suspicious Location',
                status='flagged',
                risk_score=95
            ),
        ]
        
        for tx in fraud_transactions:
            session.add(tx)
            await session.flush()  # Get the ID
            
            # Create alerts for these fraud cases
            alert = Alert(
                transaction_id=tx.id,
                severity="High",
                rule_name="HIGH_AMOUNT_FRAUD",
                description=f"High amount transaction {tx.amount} with suspicious characteristics",
                is_active=True
            )
            session.add(alert)
        
        await session.commit()
        print(f"✅ Added {len(fraud_transactions)} fraudulent transactions")
        
        # Print current status
        from sqlalchemy import select, func
        total_result = await session.execute(select(func.count(Transaction.id)))
        total_transactions = total_result.scalar()
        
        flagged_result = await session.execute(
            select(func.count(Transaction.id)).where(Transaction.status == "flagged")
        )
        flagged_transactions = flagged_result.scalar()
        
        print(f"📊 Current Status:")
        print(f"  Total transactions: {total_transactions}")
        print(f"  Flagged transactions: {flagged_transactions}")
        print(f"  Fraud rate: {(flagged_transactions/total_transactions)*100:.1f}%")


async def main():
    """Main function."""
    print("🚀 Fixing Fraud Data for FortiX")
    print("=" * 40)
    
    try:
        await fix_fraud_data()
        print("\n🎉 Fraud data fixed!")
        print("💡 You can now run: python scripts/train_evaluate_model.py")
    except Exception as e:
        print(f"❌ Error fixing fraud data: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
