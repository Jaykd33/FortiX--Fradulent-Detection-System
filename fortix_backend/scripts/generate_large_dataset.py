#!/usr/bin/env python3
"""
Generate a large training dataset with 1M+ records for fraud detection model training.
This script creates a realistic dataset with various transaction patterns and fraud indicators.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os
from pathlib import Path

def generate_large_dataset(num_records: int = 1000000, output_file: str = "large_training_dataset.csv"):
    """Generate a large dataset for training."""
    
    print(f"Generating {num_records:,} transaction records...")
    
    # Set random seed for reproducibility
    np.random.seed(42)
    random.seed(42)
    
    # Generate base transaction data
    data = []
    
    # Transaction types and their fraud probabilities
    transaction_types = {
        'CREDIT_CARD': 0.15,  # 15% fraud rate
        'UPI': 0.08,          # 8% fraud rate
        'NET_BANKING': 0.12,  # 12% fraud rate
        'WALLET': 0.06,       # 6% fraud rate
        'CASH': 0.02,         # 2% fraud rate
        'CHEQUE': 0.05        # 5% fraud rate
    }
    
    # Geographic locations
    locations = [
        'Mumbai, India', 'Delhi, India', 'Bangalore, India', 'Chennai, India',
        'Kolkata, India', 'Hyderabad, India', 'Pune, India', 'Ahmedabad, India',
        'Beijing, China', 'Shanghai, China', 'Moscow, Russia', 'St Petersburg, Russia',
        'Pyongyang, North Korea', 'Tehran, Iran', 'Dubai, UAE', 'London, UK',
        'New York, USA', 'Los Angeles, USA', 'Toronto, Canada', 'Sydney, Australia'
    ]
    
    # IP address patterns (some suspicious, some normal)
    normal_ips = [
        '192.168.1.{}', '10.0.0.{}', '172.16.0.{}', '203.0.113.{}',
        '198.51.100.{}', '192.0.2.{}'
    ]
    
    suspicious_ips = [
        '185.220.101.{}', '45.154.35.{}', '91.92.109.{}', '103.149.162.{}'
    ]
    
    # Generate data in chunks to manage memory
    chunk_size = 10000
    
    for chunk_start in range(0, num_records, chunk_size):
        chunk_end = min(chunk_start + chunk_size, num_records)
        chunk_data = []
        
        for i in range(chunk_start, chunk_end):
            # Generate transaction type
            tx_type = np.random.choice(list(transaction_types.keys()))
            fraud_prob = transaction_types[tx_type]
            
            # Determine if this transaction is fraudulent
            is_fraud = np.random.random() < fraud_prob
            
            # Generate amount (fraudulent transactions tend to be higher)
            if is_fraud:
                amount = np.random.exponential(50000) + np.random.uniform(10000, 100000)
                amount = min(amount, 1000000)  # Cap at 1M
            else:
                amount = np.random.exponential(5000) + np.random.uniform(100, 50000)
                amount = min(amount, 100000)
            
            # Generate location (fraudulent transactions from suspicious locations)
            if is_fraud and np.random.random() < 0.3:
                location = np.random.choice(locations[8:])  # Foreign locations
            else:
                location = np.random.choice(locations[:8])  # Indian locations
            
            # Generate IP address
            if is_fraud and np.random.random() < 0.4:
                ip_pattern = np.random.choice(suspicious_ips)
            else:
                ip_pattern = np.random.choice(normal_ips)
            
            ip_address = ip_pattern.format(random.randint(1, 254))
            
            # Generate device fingerprint
            if is_fraud and np.random.random() < 0.6:
                device_fingerprint = None  # Missing device fingerprint
            else:
                device_fingerprint = f"device_{random.randint(100000, 999999)}"
            
            # Generate user IDs
            sender_id = f"user_{random.randint(1, 100000)}"
            receiver_id = f"merchant_{random.randint(1, 50000)}"
            
            # Generate timestamp (spread over last 2 years)
            days_ago = random.randint(1, 730)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            
            timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            
            # Determine status based on fraud
            if is_fraud:
                status = 'flagged'
                risk_score = np.random.randint(70, 100)
            else:
                if np.random.random() < 0.05:  # 5% false positives
                    status = 'flagged'
                    risk_score = np.random.randint(70, 85)
                elif np.random.random() < 0.1:  # 10% review
                    status = 'review'
                    risk_score = np.random.randint(30, 69)
                else:
                    status = 'processed'
                    risk_score = np.random.randint(0, 29)
            
            chunk_data.append({
                'amount': round(amount, 2),
                'currency': 'INR',
                'transaction_type': tx_type,
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'device_fingerprint': device_fingerprint,
                'ip_address': ip_address,
                'geo_location': location,
                'risk_score': risk_score,
                'status': status,
                'created_at': timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        data.extend(chunk_data)
        
        # Progress update
        progress = (chunk_end / num_records) * 100
        print(f"Generated {chunk_end:,}/{num_records:,} records ({progress:.1f}%)")
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Shuffle the data
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Save to CSV
    output_path = Path(output_file)
    df.to_csv(output_path, index=False)
    
    print(f"\nDataset generated successfully!")
    print(f"File: {output_path.absolute()}")
    print(f"Records: {len(df):,}")
    print(f"Size: {output_path.stat().st_size / (1024*1024):.1f} MB")
    
    # Print summary statistics
    print(f"\nDataset Summary:")
    print(f"Fraudulent transactions: {len(df[df['status'] == 'flagged']):,} ({len(df[df['status'] == 'flagged'])/len(df)*100:.1f}%)")
    print(f"Average amount: ₹{df['amount'].mean():,.2f}")
    print(f"Average risk score: {df['risk_score'].mean():.1f}")
    
    print(f"\nTransaction types:")
    for tx_type in df['transaction_type'].value_counts().items():
        fraud_count = len(df[(df['transaction_type'] == tx_type[0]) & (df['status'] == 'flagged')])
        total_count = tx_type[1]
        fraud_rate = (fraud_count / total_count) * 100
        print(f"  {tx_type[0]}: {total_count:,} transactions, {fraud_rate:.1f}% fraud rate")
    
    return df

if __name__ == "__main__":
    # Generate 1M records
    dataset = generate_large_dataset(1000000, "large_training_dataset.csv")
    print("\n✅ Large training dataset generation completed!")
    print("\nYou can now use this dataset to train your fraud detection model.")
    print("Upload the 'large_training_dataset.csv' file through the Training page.")
