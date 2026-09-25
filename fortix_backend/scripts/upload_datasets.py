#!/usr/bin/env python3
"""
Upload and process fraud datasets for FortiX fraud detection system.
"""

import asyncio
import sys
import pandas as pd
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.db import async_session_factory, Base, async_engine
from app.models.transaction import Transaction, Alert
from app.services.fraud_engine import fraud_engine


async def upload_fraud_datasets(train_file: str, test_file: str):
    """Upload and process fraud datasets."""
    print("🔄 Uploading fraud datasets...")
    
    try:
        # Read the datasets
        train_df = pd.read_csv(train_file)
        test_df = pd.read_csv(test_file)
        
        print(f"✅ Loaded training data: {len(train_df)} records")
        print(f"✅ Loaded test data: {len(test_df)} records")
        
        # Display column information
        print(f"\n📊 Training data columns: {list(train_df.columns)}")
        print(f"📊 Test data columns: {list(test_df.columns)}")
        
        # Process training data
        await process_dataset(train_df, "training")
        
        # Process test data
        await process_dataset(test_df, "test")
        
        print("\n🎉 Dataset upload completed successfully!")
        print("💡 You can now train the ML model using: python scripts/train_evaluate_model.py")
        
    except Exception as e:
        print(f"❌ Error uploading datasets: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


async def process_dataset(df: pd.DataFrame, dataset_type: str):
    """Process a dataset and add to database."""
    print(f"\n🔄 Processing {dataset_type} dataset...")
    
    async with async_session_factory() as session:
        # Clear existing data if it's training data
        if dataset_type == "training":
            print("🗑️  Clearing existing training data...")
            await session.execute("DELETE FROM alerts")
            await session.execute("DELETE FROM transactions")
            await session.commit()
        
        # Map columns to transaction fields (adjust based on your CSV structure)
        transactions_added = 0
        
        for index, row in df.iterrows():
            try:
                # Create transaction (adjust field mapping based on your CSV columns)
                transaction = Transaction(
                    amount=float(row.get('amount', row.get('Amount', 0))),
                    currency='INR',
                    transaction_type=row.get('transaction_type', row.get('TransactionType', 'CREDIT_CARD')),
                    sender_id=str(row.get('sender_id', row.get('SenderID', f'user_{index}'))),
                    receiver_id=str(row.get('receiver_id', row.get('ReceiverID', f'merchant_{index}'))),
                    device_fingerprint=str(row.get('device_fingerprint', row.get('DeviceFingerprint', f'device_{index}'))),
                    ip_address=str(row.get('ip_address', row.get('IPAddress', '192.168.1.1'))),
                    geo_location=str(row.get('geo_location', row.get('GeoLocation', 'Mumbai, India'))),
                    status='processed'
                )
                
                session.add(transaction)
                await session.flush()  # Get the ID
                
                # Run fraud detection
                risk_score = await fraud_engine.get_risk_score(transaction)
                transaction.risk_score = risk_score
                
                # Update status based on risk score
                if risk_score >= 70:
                    transaction.status = "flagged"
                elif risk_score >= 30:
                    transaction.status = "review"
                else:
                    transaction.status = "processed"
                
                # Create alerts if fraud detected
                evaluation = await fraud_engine.evaluate_transaction(transaction)
                for alert_data in evaluation["alerts"]:
                    alert = Alert(
                        transaction_id=transaction.id,
                        severity=alert_data["severity"],
                        rule_name=alert_data["rule_name"],
                        description=alert_data["description"],
                        is_active=True
                    )
                    session.add(alert)
                
                transactions_added += 1
                
                # Commit in batches
                if transactions_added % 100 == 0:
                    await session.commit()
                    print(f"  ✅ Processed {transactions_added} transactions...")
                    
            except Exception as e:
                print(f"  ⚠️  Error processing row {index}: {str(e)}")
                continue
        
        # Final commit
        await session.commit()
        print(f"✅ Added {transactions_added} transactions from {dataset_type} dataset")


async def main():
    """Main function to upload datasets."""
    print("🚀 FortiX Dataset Upload Tool")
    print("=" * 50)
    
    # Check if files exist
    train_file = "fraudTrain.csv"
    test_file = "fraudTest.csv"
    
    if not Path(train_file).exists():
        print(f"❌ Training file not found: {train_file}")
        print("💡 Please place fraudTrain.csv in the current directory")
        return
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        print("💡 Please place fraudTest.csv in the current directory")
        return
    
    try:
        await upload_fraud_datasets(train_file, test_file)
        
    except Exception as e:
        print(f"\n❌ Error during upload: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
