"""
Comprehensive data preprocessing pipeline for fraud detection.
Handles column normalization, null imputation, and feature engineering.
"""

from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger("fortix.preprocessing")


def normalize_column_names(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Normalize column names to match training schema.
    
    Returns:
        DataFrame with normalized columns and mapping dictionary
    """
    mapping: Dict[str, str] = {}
    df_normalized = df.copy()
    
    # Comprehensive synonym mapping
    synonym_map = {
        # Amount variations
        "transaction_amount": "Transaction_Amount",
        "amount": "Transaction_Amount",
        "amt": "Transaction_Amount",
        "txn_amount": "Transaction_Amount",
        "Value": "Transaction_Amount",
        
        # User ID variations
        "user_id": "User_ID",
        "senderid": "User_ID",
        "sender_id": "User_ID",
        "userid": "User_ID",
        "customer_id": "User_ID",
        "account_id": "User_ID",
        
        # Merchant/Receiver variations
        "merchant": "Receiver_ID",
        "merchant_id": "Receiver_ID",
        "receiverid": "Receiver_ID",
        "receiver_id": "Receiver_ID",
        "merchant_name": "Receiver_ID",
        "payee": "Receiver_ID",
        
        # Timestamp variations
        "timestamp": "Transaction_Timestamp",
        "transaction_timestamp": "Transaction_Timestamp",
        "created_at": "Transaction_Timestamp",
        "date": "Transaction_Timestamp",
        "time": "Transaction_Timestamp",
        "datetime": "Transaction_Timestamp",
        
        # Transaction type variations
        "type": "Transaction_Type",
        "transaction_type": "Transaction_Type",
        "txn_type": "Transaction_Type",
        "payment_type": "Transaction_Type",
        
        # Device variations
        "device": "Device_Type",
        "device_type": "Device_Type",
        "device_category": "Device_Type",
        
        # Location variations
        "location": "Location",
        "city": "Location",
        "region": "Location",
        "country": "Location",
        
        # Merchant category
        "merchant_category": "Merchant_Category",
        "category": "Merchant_Category",
        "merchant_type": "Merchant_Category",
        
        # Card type
        "card_type": "Card_Type",
        "card_category": "Card_Type",
        
        # Authentication
        "auth_method": "Authentication_Method",
        "authentication_method": "Authentication_Method",
        "auth": "Authentication_Method",
        "authentication": "Authentication_Method",
        
        # Distance
        "distance": "Transaction_Distance",
        "transaction_distance": "Transaction_Distance",
        "geo_distance": "Transaction_Distance",
        
        # IP and Geo
        "ip": "IPAddress",
        "ip_address": "IPAddress",
        "ipaddr": "IPAddress",
        "geolocation": "GeoLocation",
        "geo_location": "GeoLocation",
        "geo": "GeoLocation",
        
        # Labels
        "fraud": "Fraud_Label",
        "fraud_label": "Fraud_Label",
        "label": "Fraud_Label",
        "is_fraud": "Fraud_Label",
        "fraudulent": "Fraud_Label",
    }
    
    # Apply normalization
    for col in list(df_normalized.columns):
        col_lower = col.strip().replace("-", "_").replace(" ", "_").lower()
        if col_lower in synonym_map:
            new_name = synonym_map[col_lower]
            if new_name != col:
                df_normalized.rename(columns={col: new_name}, inplace=True)
                mapping[col] = new_name
        else:
            # Try to standardize format (Title_Case)
            if not any(c.isupper() for c in col):
                new_name = col.replace("_", " ").title().replace(" ", "_")
                if new_name != col:
                    df_normalized.rename(columns={col: new_name}, inplace=True)
                    mapping[col] = new_name
    
    logger.info(f"Normalized {len(mapping)} column names")
    return df_normalized, mapping


def clean_and_impute(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean data and impute missing values with sensible defaults.
    Ensures all required fields have non-null values.
    """
    df_clean = df.copy()
    
    # Required fields with defaults
    required_fields = {
        "Transaction_Amount": 0.0,
        "Transaction_Type": "CREDIT_CARD",
        "User_ID": "unknown_user",
        "Receiver_ID": "unknown_merchant",
        "Device_Type": "Unknown",
        "Location": "Unknown",
        "Merchant_Category": "OTHER",
        "Card_Type": "DEBIT",
        "Authentication_Method": "Password",
        "Transaction_Distance": 0.0,
    }
    
    # Fill missing values
    for field, default_value in required_fields.items():
        if field not in df_clean.columns:
            df_clean[field] = default_value
            logger.warning(f"Missing required field '{field}', using default: {default_value}")
        else:
            null_count = df_clean[field].isnull().sum()
            if null_count > 0:
                if pd.api.types.is_numeric_dtype(df_clean[field]):
                    df_clean[field].fillna(default_value, inplace=True)
                else:
                    df_clean[field].fillna(str(default_value), inplace=True)
                logger.info(f"Imputed {null_count} null values in '{field}' with default: {default_value}")
    
    # Handle optional fields
    optional_fields = {
        "IPAddress": "0.0.0.0",
        "GeoLocation": "Unknown",
        "DeviceFingerprint": "unknown_device",
    }
    
    for field, default_value in optional_fields.items():
        if field in df_clean.columns:
            df_clean[field].fillna(default_value, inplace=True)
        else:
            df_clean[field] = default_value
    
    # Ensure numeric types
    numeric_fields = ["Transaction_Amount", "Transaction_Distance"]
    for field in numeric_fields:
        if field in df_clean.columns:
            df_clean[field] = pd.to_numeric(df_clean[field], errors='coerce').fillna(0.0)
    
    # Ensure string types for categoricals
    categorical_fields = [
        "Transaction_Type", "User_ID", "Receiver_ID", "Device_Type",
        "Location", "Merchant_Category", "Card_Type", "Authentication_Method"
    ]
    for field in categorical_fields:
        if field in df_clean.columns:
            df_clean[field] = df_clean[field].astype(str).replace('nan', 'Unknown')
    
    # Remove rows with critical missing data (shouldn't happen after imputation, but safety check)
    initial_rows = len(df_clean)
    df_clean = df_clean.dropna(subset=["Transaction_Amount", "Transaction_Type"])
    if len(df_clean) < initial_rows:
        logger.warning(f"Dropped {initial_rows - len(df_clean)} rows with critical missing data")
    
    return df_clean


def prepare_for_database(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map feature-engineered columns to database schema column names.
    """
    df_db = df.copy()
    
    # Map to database column names
    db_column_mapping = {
        'Transaction_Amount': 'amount',
        'Transaction_Type': 'transaction_type',
        'Device_Type': 'device_type',
        'Location': 'location',
        'Merchant_Category': 'merchant_category',
        'Card_Type': 'card_type',
        'Authentication_Method': 'authentication_method',
        'Transaction_Distance': 'transaction_distance',
        'User_ID': 'sender_id',
        'Receiver_ID': 'receiver_id',
        'IPAddress': 'ip_address',
        'GeoLocation': 'geo_location',
        'DeviceFingerprint': 'device_fingerprint',
    }
    
    # Rename columns
    for old_name, new_name in db_column_mapping.items():
        if old_name in df_db.columns:
            df_db.rename(columns={old_name: new_name}, inplace=True)
    
    # Ensure required database fields exist
    if 'currency' not in df_db.columns:
        df_db['currency'] = 'INR'
    
    if 'receiver_id' not in df_db.columns:
        df_db['receiver_id'] = 'unknown_merchant'
    
    if 'sender_id' not in df_db.columns:
        df_db['sender_id'] = 'unknown_user'
    
    # Ensure non-null for required fields
    required_db_fields = {
        'amount': 0.0,
        'transaction_type': 'CREDIT_CARD',
        'currency': 'INR',
        'sender_id': 'unknown_user',
        'receiver_id': 'unknown_merchant',
    }
    
    for field, default in required_db_fields.items():
        if field in df_db.columns:
            df_db[field] = df_db[field].fillna(default)
        else:
            df_db[field] = default
    
    return df_db

