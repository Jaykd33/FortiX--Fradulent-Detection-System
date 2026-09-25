# app/api/v1/endpoints/dataset.py

from __future__ import annotations

import asyncio
import io
from typing import Optional, Dict, Any, List
import logging

import pandas as pd
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import delete, select, func
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError, SQLAlchemyError, IntegrityError

from app.core.db import get_db_session
from app.models.transaction import Transaction, Alert
from app.services.fraud_engine import fraud_engine
from app.services.feature_engineering import engineer_features
from app.services.preprocessing import (
    normalize_column_names,
    clean_and_impute,
    prepare_for_database,
)
from app.services.gnn_service import gnn_service

router = APIRouter()
logger = logging.getLogger("fortix.dataset")

# Serialize uploads so only one writer at a time
_UPLOAD_LOCK = asyncio.Lock()


async def _flush_with_retry(db: AsyncSession, tries: int = 3, base_delay: float = 0.1):
    """Flush database session with retry logic."""
    delay = base_delay
    for attempt in range(tries):
        try:
            await db.flush()
            return
        except OperationalError:
            await db.rollback()
            if attempt == tries - 1:
                raise
            await asyncio.sleep(delay)
            delay *= 2


async def _commit_with_retry(db: AsyncSession, tries: int = 3, base_delay: float = 0.1):
    """Commit database transaction with retry logic."""
    delay = base_delay
    for attempt in range(tries):
        try:
            await db.commit()
            return
        except OperationalError:
            await db.rollback()
            if attempt == tries - 1:
                raise
            await asyncio.sleep(delay)
            delay *= 2


def _augment_advanced_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add advanced feature engineering:
    - Rolling averages (7d, 30d)
    - Transaction frequency
    - Mean distance per user
    - Temporal risk index
    """
    out = df.copy()
    
    # Ensure timestamp column
    ts_col = None
    for col in ("Transaction_Timestamp", "Timestamp", "created_at"):
        if col in out.columns:
            ts_col = col
            break
    
    if ts_col:
        out[ts_col] = pd.to_datetime(out[ts_col], errors='coerce')
    else:
        # Create synthetic timestamps
        out["Transaction_Timestamp"] = pd.to_datetime(pd.Series(range(len(out))), unit="s")
        ts_col = "Transaction_Timestamp"
    
    # Ensure User_ID exists
    user_col = None
    for col in ("User_ID", "sender_id", "user_id"):
        if col in out.columns:
            user_col = col
            break
    
    if not user_col:
        out["User_ID"] = [f"user_{i}" for i in range(len(out))]
        user_col = "User_ID"
    
    # Ensure amount column exists
    amount_col = None
    for col in ("Transaction_Amount", "amount", "Amount"):
        if col in out.columns:
            amount_col = col
            break
    
    if not amount_col:
        out["Transaction_Amount"] = 0.0
        amount_col = "Transaction_Amount"
    
    # Sort by user and timestamp
    out = out.sort_values([user_col, ts_col]).reset_index(drop=True)
    
    # Rolling average amounts (7 days)
    if amount_col in out.columns:
        out["avg_amount_user_7d"] = (
            out.groupby(user_col)[amount_col]
            .transform(lambda s: s.rolling(window=min(50, max(2, len(s))), min_periods=1).mean())
        )
        out["avg_amount_user_30d"] = (
            out.groupby(user_col)[amount_col]
            .transform(lambda s: s.rolling(window=min(200, max(10, len(s))), min_periods=1).mean())
        )
    
    # Transaction frequency
    out["transaction_frequency_user"] = out.groupby(user_col).cumcount() + 1
    
    # Mean distance per user
    distance_col = None
    for col in ("Transaction_Distance", "distance", "transaction_distance"):
        if col in out.columns:
            distance_col = col
            break
    
    if distance_col:
        out["mean_distance_user"] = (
            out.groupby(user_col)[distance_col]
            .transform(lambda s: s.expanding().mean())
        )
    else:
        out["mean_distance_user"] = 0.0
    
    # Time since last transaction
    out["time_since_last_transaction"] = (
        out.groupby(user_col)[ts_col].diff().dt.total_seconds().fillna(0.0)
    )
    
    # Temporal risk index (higher risk for frequent transactions in short time)
    out["temporal_risk_index"] = (
        out["transaction_frequency_user"] / (1.0 + out["time_since_last_transaction"] / 3600.0)
    )
    
    # Failed transaction count (if Fraud_Label exists)
    if "Fraud_Label" in out.columns:
        out["failed_transaction_count_7d"] = (
            out.groupby(user_col)["Fraud_Label"]
            .transform(lambda s: s.rolling(window=min(50, max(2, len(s))), min_periods=1).sum())
        )
        out["previous_fraud_rate_user"] = (
            out.groupby(user_col)["Fraud_Label"]
            .transform(lambda s: s.shift().expanding().mean().fillna(0.0))
        )
    else:
        out["failed_transaction_count_7d"] = 0.0
        out["previous_fraud_rate_user"] = 0.0
    
    return out


@router.post("/analyze")
async def analyze_dataset(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Analyze uploaded CSV dataset for fraud detection.
    
    Steps:
    1. Parse and normalize CSV columns
    2. Clean and impute missing values
    3. Apply feature engineering
    4. Run hybrid GNN + Random Forest model
    5. Store results in database
    6. Return fraud statistics
    """
    if not (file and file.filename and file.filename.lower().endswith('.csv')):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    async with _UPLOAD_LOCK:
        try:
            logger.info("=" * 60)
            logger.info("Starting dataset analysis")
            logger.info("=" * 60)
            
            # Clear existing data
            logger.info("Clearing previous transactions and alerts...")
            await db.execute(delete(Alert))
            await db.execute(delete(Transaction))
            await _commit_with_retry(db)
            
            # Step 1: Read CSV
            logger.info("Step 1: Reading CSV file...")
            try:
                contents = await file.read()
            except Exception as e:
                logger.exception("Failed to read file")
                raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")
            
            try:
                df = pd.read_csv(io.BytesIO(contents))
            except Exception as e:
                logger.exception("Failed to parse CSV")
                raise HTTPException(status_code=400, detail=f"Invalid CSV format: {e}")
            
            logger.info(f"✅ Loaded {len(df)} rows with {len(df.columns)} columns")
            logger.info(f"Columns: {list(df.columns)}")
            
            # Step 2: Normalize column names
            logger.info("Step 2: Normalizing column names...")
            df, col_mapping = normalize_column_names(df)
            logger.info(f"✅ Normalized {len(col_mapping)} columns")
            
            # Step 3: Clean and impute missing values
            logger.info("Step 3: Cleaning and imputing missing values...")
            df = clean_and_impute(df)
            logger.info(f"✅ Cleaned data: {len(df)} rows")
            
            # Step 4: Feature engineering
            logger.info("Step 4: Applying feature engineering...")
            df_fe = engineer_features(df)
            df_fe = _augment_advanced_features(df_fe)
            logger.info(f"✅ Feature engineering complete: {df_fe.shape}")
            
            # Step 5: Prepare features for model
            logger.info("Step 5: Preparing features for ML model...")
            # Drop non-feature columns
            drop_cols = [
                "Fraud_Label", "Risk_Score", "Transaction_ID", "User_ID",
                "Timestamp", "Transaction_Timestamp"
            ]
            X = df_fe.drop(columns=drop_cols, errors='ignore').copy()
            
            # Align with model's expected features
            model = getattr(fraud_engine, "ml_pipeline", None) or getattr(fraud_engine, "model", None)
            if model is not None and hasattr(model, "feature_names_in_"):
                expected_features = list(model.feature_names_in_)
                missing = [f for f in expected_features if f not in X.columns]
                extra = [f for f in X.columns if f not in expected_features]
                
                if missing:
                    logger.warning(f"Missing {len(missing)} model features: {missing[:10]}")
                    for feat in missing:
                        X[feat] = 0.0  # Fill with 0 instead of NaN
                
                if extra:
                    logger.info(f"Extra features not in model: {extra[:10]}")
                
                # Reorder to match model
                X = X[[f for f in expected_features if f in X.columns]]
            
            logger.info(f"✅ Prepared features: {X.shape}")
            
            # Step 6: Run Random Forest model
            logger.info("Step 6: Running Random Forest model...")
            rf_prob = np.zeros((len(X),), dtype=float)
            
            if model is not None and hasattr(model, "predict_proba") and len(X) > 0:
                try:
                    rf_prob = model.predict_proba(X)[:, 1]
                    logger.info(f"✅ RF predictions: mean={rf_prob.mean():.3f}, max={rf_prob.max():.3f}")
                except Exception as e:
                    logger.exception(f"RF prediction failed: {e}")
                    rf_prob = np.zeros((len(X),), dtype=float)
            else:
                logger.warning("ML model not available; using zero probabilities")
            
            # Step 7: Run GNN model
            logger.info("Step 7: Running GNN model...")
            gnn_prob = np.zeros((len(X),), dtype=float)
            gnn_used = False
            
            try:
                gnn_prob = gnn_service.infer_probabilities(df_fe)
                gnn_used = True
                logger.info(f"✅ GNN predictions: mean={gnn_prob.mean():.3f}, max={gnn_prob.max():.3f}")
            except Exception as e:
                logger.exception(f"GNN inference failed: {e}")
                gnn_prob = np.zeros((len(X),), dtype=float)
            
            # Ensure same length
            if len(gnn_prob) != len(rf_prob):
                logger.warning(f"Length mismatch: RF={len(rf_prob)}, GNN={len(gnn_prob)}")
                if len(gnn_prob) < len(rf_prob):
                    gnn_prob = np.pad(gnn_prob, (0, len(rf_prob) - len(gnn_prob)), mode='constant')
                else:
                    gnn_prob = gnn_prob[:len(rf_prob)]
            
            # Step 8: Combine predictions (hybrid model)
            logger.info("Step 8: Combining predictions (hybrid model)...")
            final_prob = 0.7 * rf_prob + 0.3 * gnn_prob
            risk_scores = np.clip(np.round(final_prob * 100).astype(int), 0, 100)
            
            # Determine fraud status (threshold: >= 70 is fraudulent)
            fraud_threshold = 70
            fraudulent_count = int((risk_scores >= fraud_threshold).sum())
            
            logger.info(f"✅ Hybrid scores: mean={risk_scores.mean():.1f}, fraudulent={fraudulent_count} (threshold={fraud_threshold})")
            
            # Step 9: Prepare data for database
            logger.info("Step 9: Preparing data for database...")
            df_for_db = prepare_for_database(df_fe)
            
            # Add risk scores and status
            df_for_db["risk_score"] = risk_scores
            df_for_db["status"] = "processed"
            df_for_db.loc[df_for_db["risk_score"] >= 30, "status"] = "review"
            df_for_db.loc[df_for_db["risk_score"] >= fraud_threshold, "status"] = "flagged"
            
            # Step 10: Insert into database
            logger.info("Step 10: Inserting transactions into database...")
            
            # Get valid database columns
            valid_columns = {c.name for c in Transaction.__table__.columns}
            
            # Prepare rows with required fields
            rows = []
            for idx, row in df_for_db.iterrows():
                transaction_dict = {}
                
                # Map all valid columns
                for col in valid_columns:
                    if col in df_for_db.columns:
                        value = row[col]
                        # Handle None values for required fields
                        if value is None or (isinstance(value, float) and pd.isna(value)):
                            # Set defaults for required fields
                            if col == "amount":
                                value = 0.0
                            elif col == "transaction_type":
                                value = "CREDIT_CARD"
                            elif col == "currency":
                                value = "INR"
                            elif col == "sender_id":
                                value = "unknown_user"
                            elif col == "receiver_id":
                                value = "unknown_merchant"
                            elif col in ("risk_score", "status"):
                                # These should already be set
                                continue
                        transaction_dict[col] = value
                
                # Ensure required fields are present
                transaction_dict.setdefault("amount", float(row.get("amount", 0.0) or 0.0))
                transaction_dict.setdefault("transaction_type", str(row.get("transaction_type", "CREDIT_CARD")))
                transaction_dict.setdefault("currency", "INR")
                transaction_dict.setdefault("sender_id", str(row.get("sender_id", f"user_{idx}")))
                transaction_dict.setdefault("receiver_id", str(row.get("receiver_id", "unknown_merchant")))
                transaction_dict.setdefault("risk_score", int(risk_scores[idx]))
                transaction_dict.setdefault("status", str(row.get("status", "processed")))
                
                # Ensure non-null for required fields
                if transaction_dict["amount"] is None or pd.isna(transaction_dict["amount"]):
                    transaction_dict["amount"] = 0.0
                if transaction_dict["transaction_type"] is None or pd.isna(transaction_dict["transaction_type"]):
                    transaction_dict["transaction_type"] = "CREDIT_CARD"
                
                rows.append(transaction_dict)
            
            # Bulk insert
            total_inserted = 0
            if rows:
                try:
                    # Insert in batches to avoid SQLite limits
                    batch_size = 500
                    for i in range(0, len(rows), batch_size):
                        batch = rows[i:i + batch_size]
                        await db.execute(insert(Transaction), batch)
                        await _commit_with_retry(db)
                        total_inserted += len(batch)
                        logger.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} transactions")
                    
                    logger.info(f"✅ Successfully inserted {total_inserted} transactions")
                except IntegrityError as e:
                    logger.exception(f"Integrity error during insert: {e}")
                    await db.rollback()
                    raise HTTPException(
                        status_code=500,
                        detail=f"Database integrity error: {str(e)}. Check that all required fields have valid values."
                    )
                except Exception as e:
                    logger.exception(f"Error during insert: {e}")
                    await db.rollback()
                    raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
            
            # Step 11: Calculate final statistics
            logger.info("Step 11: Calculating statistics...")
            
            # Count fraudulent transactions
            flagged_count = (
                await db.execute(
                    select(func.count(Transaction.id)).where(Transaction.status == "flagged")
                )
            ).scalar() or 0
            
            total_transactions = total_inserted
            fraud_percentage = (flagged_count / total_transactions * 100) if total_transactions > 0 else 0.0
            
            logger.info("=" * 60)
            logger.info(f"Analysis complete!")
            logger.info(f"Total transactions: {total_transactions}")
            logger.info(f"Fraudulent transactions: {flagged_count}")
            logger.info(f"Fraud percentage: {fraud_percentage:.2f}%")
            logger.info("=" * 60)
            
            # Return response
            return {
                "status": "success",
                "total_transactions": int(total_transactions),
                "fraudulent_transactions": int(flagged_count),
                "fraud_percentage": round(fraud_percentage, 2),
                "gnn_used": gnn_used,
                "hybrid_model": "RandomForest + GNN",
                "message": f"Successfully analyzed {total_transactions} transactions. "
                          f"Detected {flagged_count} fraudulent transactions ({fraud_percentage:.2f}%)."
            }
            
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.exception(f"Unhandled error in analyze: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing file: {str(e)}. Check logs for details."
            )


# Keep the upload-dataset endpoint for backward compatibility
@router.post("/upload-dataset")
async def upload_dataset(
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Backward-compatible endpoint for dataset upload.
    Delegates to analyze endpoint.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    return await analyze_dataset(file=file, db=db)


@router.get("/dataset-info")
async def get_dataset_info(db: AsyncSession = Depends(get_db_session)):
    """Get dataset statistics."""
    total_transactions = (await db.execute(select(func.count(Transaction.id)))).scalar() or 0
    flagged_transactions = (
        await db.execute(
            select(func.count(Transaction.id)).where(Transaction.status == "flagged")
        )
    ).scalar() or 0
    total_alerts = (await db.execute(select(func.count(Alert.id)))).scalar() or 0

    return {
        "total_transactions": total_transactions,
        "flagged_transactions": flagged_transactions,
        "total_alerts": total_alerts,
        "fraud_rate": (flagged_transactions / total_transactions * 100) if total_transactions else 0,
    }
