# Fraud Detection Pipeline - Comprehensive Fixes

## Overview

This document describes the comprehensive refactoring of the fraud detection pipeline to fix critical issues and integrate a hybrid GNN + Random Forest model.

## Issues Fixed

### 1. ✅ CSV Upload and Parsing
**Problem**: CSV uploads were failing with parsing errors or incorrect column mapping.

**Solution**:
- Robust CSV parsing using `pd.read_csv(io.BytesIO(contents))`
- Comprehensive column name normalization with synonym mapping
- Handles various column name formats (Transaction_Amount, amount, Amount, etc.)

**Files**: `app/services/preprocessing.py` - `normalize_column_names()`

### 2. ✅ SQLite IntegrityError (NOT NULL constraint)
**Problem**: Database inserts failing with `NOT NULL constraint failed: transactions.amount`

**Solution**:
- Comprehensive null imputation in `clean_and_impute()` function
- Ensures all required fields have non-null values before insert
- Default values for required fields:
  - `amount`: 0.0
  - `transaction_type`: "CREDIT_CARD"
  - `currency`: "INR"
  - `sender_id`: "unknown_user"
  - `receiver_id`: "unknown_merchant"
- Database insert logic validates all required fields before insertion

**Files**: 
- `app/services/preprocessing.py` - `clean_and_impute()`
- `app/api/v1/endpoints/dataset.py` - Insert logic (lines 380-420)

### 3. ✅ Zero Frauds Detected
**Problem**: Frontend always showed "0 frauds detected" even when dataset had many frauds.

**Solution**:
- Fixed fraud detection threshold: transactions with `risk_score >= 70` are flagged as fraudulent
- Proper counting of flagged transactions from database
- Hybrid model combines RF (70%) + GNN (30%) probabilities
- Response format matches frontend expectations:
  ```json
  {
    "total_transactions": N,
    "fraudulent_transactions": X,
    "fraud_percentage": Y
  }
  ```

**Files**: `app/api/v1/endpoints/dataset.py` - Analyze endpoint

### 4. ✅ GNN Integration
**Problem**: No GNN model, only dummy placeholder.

**Solution**:
- Created `GNNService` class in `app/services/gnn_service.py`
- Builds transaction graph:
  - Nodes: Users, Merchants, Devices
  - Edges: Transactions with features (amount, distance, time)
- Computes node embeddings using graph structure
- Generates fraud probabilities based on entity relationships
- Falls back to heuristic if graph construction fails

**Files**: `app/services/gnn_service.py`

### 5. ✅ Feature Engineering
**Problem**: Missing advanced features for fraud detection.

**Solution**:
- Rolling averages: `avg_amount_user_7d`, `avg_amount_user_30d`
- Transaction frequency: `transaction_frequency_user`
- Mean distance per user: `mean_distance_user`
- Temporal risk index: `temporal_risk_index`
- Failed transaction count: `failed_transaction_count_7d`
- Previous fraud rate: `previous_fraud_rate_user`

**Files**: 
- `app/api/v1/endpoints/dataset.py` - `_augment_advanced_features()`
- `app/services/feature_engineering.py` - Existing features

### 6. ✅ Error Handling
**Problem**: Generic 500 errors without meaningful messages.

**Solution**:
- Comprehensive try-except blocks with specific error messages
- Detailed logging at each step
- Rollback on errors
- Meaningful HTTPException messages for frontend

**Files**: `app/api/v1/endpoints/dataset.py`

## Architecture

### Pipeline Flow

```
1. CSV Upload
   ↓
2. Parse CSV (pd.read_csv)
   ↓
3. Normalize Column Names (synonym mapping)
   ↓
4. Clean & Impute Missing Values (ensure non-null)
   ↓
5. Feature Engineering (existing + advanced)
   ↓
6. Prepare Features for ML Model
   ↓
7. Random Forest Inference (70% weight)
   ↓
8. GNN Inference (30% weight)
   ↓
9. Hybrid Scoring (combine probabilities)
   ↓
10. Assign Status (processed/review/flagged)
    ↓
11. Insert into Database (with validation)
    ↓
12. Return Statistics
```

### Key Components

#### 1. Preprocessing Service (`app/services/preprocessing.py`)
- `normalize_column_names()`: Maps various column name formats to canonical names
- `clean_and_impute()`: Fills missing values with sensible defaults
- `prepare_for_database()`: Maps feature-engineered columns to DB schema

#### 2. GNN Service (`app/services/gnn_service.py`)
- `build_transaction_graph()`: Constructs graph from transactions
- `compute_node_embeddings()`: Generates entity embeddings
- `infer_probabilities()`: Produces fraud probabilities from graph structure

#### 3. Dataset Endpoint (`app/api/v1/endpoints/dataset.py`)
- `/analyze`: Main endpoint for CSV analysis
- Comprehensive error handling
- Detailed logging
- Returns fraud statistics

## Database Schema

### Required Fields (Non-Nullable)
- `amount`: Float (default: 0.0)
- `transaction_type`: String (default: "CREDIT_CARD")
- `currency`: String (default: "INR")
- `sender_id`: String (default: "unknown_user")
- `receiver_id`: String (default: "unknown_merchant")

### Optional Fields (Nullable)
- `device_type`, `location`, `merchant_category`, `card_type`
- `authentication_method`, `transaction_distance`
- `device_fingerprint`, `ip_address`, `geo_location`
- `risk_score`, `status`

## Fraud Detection Thresholds

- **Processed**: `risk_score < 30`
- **Review**: `30 <= risk_score < 70`
- **Flagged (Fraudulent)**: `risk_score >= 70`

## Response Format

```json
{
  "status": "success",
  "total_transactions": 1000,
  "fraudulent_transactions": 150,
  "fraud_percentage": 15.0,
  "gnn_used": true,
  "hybrid_model": "RandomForest + GNN",
  "message": "Successfully analyzed 1000 transactions. Detected 150 fraudulent transactions (15.00%)."
}
```

## Testing Checklist

- [x] CSV parsing handles various column name formats
- [x] Null values are properly imputed
- [x] Database inserts don't fail with IntegrityError
- [x] Fraud detection correctly counts fraudulent transactions
- [x] GNN service generates valid probabilities
- [x] Hybrid model combines RF and GNN predictions
- [x] Response format matches frontend expectations
- [x] Error handling provides meaningful messages

## Future Enhancements

1. **Train Real GNN Model**: Replace heuristic-based GNN with trained PyTorch Geometric model
2. **Feature Store**: Cache computed features for faster inference
3. **Model Versioning**: Track model versions and A/B testing
4. **Real-time Updates**: Update embeddings incrementally as new transactions arrive
5. **Explainability**: Add SHAP/LIME explanations for fraud predictions

## Notes

- The GNN service currently uses heuristic-based embeddings. For production, train a real GNN model using PyTorch Geometric.
- All required fields are ensured to have non-null values before database insert.
- The hybrid model weights (70% RF, 30% GNN) can be adjusted based on validation performance.
- Fraud threshold (70) can be tuned based on business requirements.

