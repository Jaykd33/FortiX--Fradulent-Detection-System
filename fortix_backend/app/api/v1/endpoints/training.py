from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, func
import pandas as pd
import io
import asyncio
import os
from pathlib import Path
from typing import Dict, Any
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import numpy as np

from app.core.db import get_db_session
from app.models.transaction import Transaction, Alert
from app.services.fraud_engine import fraud_engine

router = APIRouter()

# Global training status
training_status = {
    "is_training": False,
    "progress": 0,
    "status": "idle",
    "message": "",
    "metrics": None
}

async def train_model_async(file_path: str, db: AsyncSession):
    """Async function to train the model on large dataset."""
    global training_status
    
    try:
        training_status.update({
            "is_training": True,
            "progress": 0,
            "status": "loading_data",
            "message": "Loading and processing dataset..."
        })
        
        # Load data in chunks to handle large files
        chunk_size = 10000  # Process 10k rows at a time
        chunks = []
        total_rows = 0
        
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            chunks.append(chunk)
            total_rows += len(chunk)
            training_status["progress"] = min(10, (total_rows / 100000) * 10)  # First 10% for loading
        
        # Combine all chunks
        df = pd.concat(chunks, ignore_index=True)
        training_status.update({
            "progress": 15,
            "status": "preprocessing",
            "message": f"Loaded {total_rows:,} records. Preprocessing data..."
        })
        
        # Data preprocessing
        # Create features for ML model
        df['amount_log'] = np.log1p(df['amount'])
        df['has_device'] = df['device_fingerprint'].notna().astype(int)
        df['is_private_ip'] = df['ip_address'].str.startswith('192.168.').astype(int)
        df['is_india'] = df['geo_location'].str.contains('India', na=False).astype(int)
        
        # Create target variable (1 for flagged transactions, 0 for others)
        df['is_fraud'] = (df['status'] == 'flagged').astype(int)
        
        # Select features for training
        feature_columns = ['amount_log', 'has_device', 'is_private_ip', 'is_india']
        X = df[feature_columns].fillna(0)
        y = df['is_fraud']
        
        training_status.update({
            "progress": 25,
            "status": "splitting_data",
            "message": "Splitting data into train/test sets..."
        })
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        training_status.update({
            "progress": 35,
            "status": "scaling_features",
            "message": "Scaling features..."
        })
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        training_status.update({
            "progress": 45,
            "status": "training_model",
            "message": "Training Random Forest model..."
        })
        
        # Train Random Forest with optimized parameters for large dataset
        model = RandomForestClassifier(
            n_estimators=200,  # More trees for better performance
            max_depth=20,      # Deeper trees for complex patterns
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,         # Use all CPU cores
            verbose=1
        )
        
        model.fit(X_train_scaled, y_train)
        
        training_status.update({
            "progress": 80,
            "status": "evaluating_model",
            "message": "Evaluating model performance..."
        })
        
        # Make predictions
        y_pred = model.predict(X_test_scaled)
        y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
        
        # Calculate metrics
        accuracy = model.score(X_test_scaled, y_test)
        auc_score = roc_auc_score(y_test, y_pred_proba)
        
        # Generate classification report
        class_report = classification_report(y_test, y_pred, output_dict=True)
        conf_matrix = confusion_matrix(y_test, y_pred)
        
        training_status.update({
            "progress": 90,
            "status": "saving_model",
            "message": "Saving trained model..."
        })
        
        # Create model directory if it doesn't exist
        model_dir = Path("ml_models")
        model_dir.mkdir(exist_ok=True)
        
        # Save model with all components
        model_data = {
            'model': model,
            'scaler': scaler,
            'label_encoder': None,  # Not needed for this simple case
            'feature_columns': feature_columns,
            'metrics': {
                'accuracy': accuracy,
                'auc_score': auc_score,
                'classification_report': class_report,
                'confusion_matrix': conf_matrix.tolist()
            }
        }
        
        model_path = model_dir / "fraud_model.joblib"
        joblib.dump(model_data, model_path)
        
        # Update fraud engine with new model
        await fraud_engine.load_model(str(model_path))
        
        training_status.update({
            "progress": 100,
            "status": "completed",
            "message": f"Training completed successfully! Accuracy: {accuracy:.4f}, AUC: {auc_score:.4f}",
            "metrics": {
                'accuracy': accuracy,
                'auc_score': auc_score,
                'classification_report': class_report,
                'confusion_matrix': conf_matrix.tolist(),
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'feature_importance': dict(zip(feature_columns, model.feature_importances_))
            }
        })
        
    except Exception as e:
        training_status.update({
            "is_training": False,
            "status": "error",
            "message": f"Training failed: {str(e)}",
            "progress": 0
        })
        raise e
    finally:
        training_status["is_training"] = False

@router.post("/train-large-dataset")
async def train_large_dataset(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session)
):
    """Train model on large dataset (1M+ records)."""
    
    if training_status["is_training"]:
        raise HTTPException(status_code=400, detail="Training is already in progress")
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    try:
        # Save uploaded file temporarily
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        
        file_path = temp_dir / file.filename
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Start training in background using asyncio
        asyncio.create_task(train_model_async(str(file_path), db))
        
        return {
            "status": "started",
            "message": "Training started in background. Use /training/status to check progress.",
            "filename": file.filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting training: {str(e)}")

@router.get("/training/status")
async def get_training_status():
    """Get current training status and progress."""
    return training_status

@router.get("/training/metrics")
async def get_training_metrics():
    """Get training metrics after completion."""
    if training_status["status"] != "completed":
        raise HTTPException(status_code=400, detail="Training not completed yet")
    
    return {
        "metrics": training_status["metrics"],
        "status": training_status["status"]
    }

@router.post("/training/stop")
async def stop_training():
    """Stop ongoing training (if possible)."""
    if not training_status["is_training"]:
        raise HTTPException(status_code=400, detail="No training in progress")
    
    training_status.update({
        "is_training": False,
        "status": "stopped",
        "message": "Training stopped by user"
    })
    
    return {"status": "stopped", "message": "Training stopped"}
