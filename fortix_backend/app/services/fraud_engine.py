"""
Fraud detection engine service.
This module contains the business logic for fraud detection rules and ML scoring.
"""

import joblib
from typing import Dict, Any, Optional, List
from pathlib import Path
import numpy as np
import pandas as pd
from app.models.transaction import Transaction


class FraudEngine:
    """Core fraud detection engine with rule-based and ML-based scoring."""
    
    def __init__(self):
        self.rules = self._initialize_rules()
        # New pipeline-based artifact
        self.ml_pipeline = None
        self.numeric_columns: List[str] = []
        self.categorical_columns: List[str] = []
        # Backward-compat placeholders
        self.ml_model = None
        self.scaler = None
        self.label_encoder = None
        # Cached feature importances for analytics
        self.feature_importances: Optional[List[Dict[str, Any]]] = None
    
    def _initialize_rules(self) -> Dict[str, Any]:
        """Initialize fraud detection rules."""
        return {
            "high_amount_threshold": 100000,  # 1 lakh INR
            "velocity_check_hours": 24,
            "max_transactions_per_hour": 10,
            "suspicious_ip_countries": ["CN", "RU", "KP"],  # Example
        }
    
    async def evaluate_transaction(self, transaction: Transaction) -> Dict[str, Any]:
        """
        Evaluate a transaction for fraud risk.
        
        Args:
            transaction: Transaction model instance
            
        Returns:
            Dict containing risk_score, alerts, and evaluation details
        """
        risk_score = 0
        alerts = []
        
        # Rule 1: High amount check
        if transaction.amount > self.rules["high_amount_threshold"]:
            risk_score += 30
            alerts.append({
                "severity": "High",
                "rule_name": "HIGH_AMOUNT",
                "description": f"Transaction amount {transaction.amount} exceeds threshold"
            })
        
        # Rule 2: Velocity check (simplified - would need historical data)
        # This is a placeholder - in production, query recent transactions
        if transaction.amount > 50000:  # Medium amount
            risk_score += 15
            alerts.append({
                "severity": "Medium",
                "rule_name": "MEDIUM_AMOUNT_VELOCITY",
                "description": "Medium amount transaction requiring velocity check"
            })
        
        # Rule 3: Device fingerprint check
        if not transaction.device_fingerprint:
            risk_score += 10
            alerts.append({
                "severity": "Low",
                "rule_name": "MISSING_DEVICE_FINGERPRINT",
                "description": "No device fingerprint provided"
            })
        
        # Rule 4: IP address validation (simplified)
        if transaction.ip_address and transaction.ip_address.startswith("192.168."):
            risk_score += 5
            alerts.append({
                "severity": "Low",
                "rule_name": "PRIVATE_IP",
                "description": "Transaction from private IP address"
            })
        
        # Normalize risk score to 0-100
        risk_score = min(risk_score, 100)
        
        return {
            "risk_score": risk_score,
            "alerts": alerts,
            "evaluation_timestamp": transaction.created_at,
            "rules_applied": len(alerts)
        }
    
    async def load_model(self, model_path: str) -> None:
        """Load the trained ML model pipeline and metadata (new format compatible)."""
        try:
            artifact = joblib.load(model_path)
            if isinstance(artifact, dict) and 'model' in artifact:
                self.ml_pipeline = artifact['model']
                self.numeric_columns = list(artifact.get('numeric_columns', []))
                self.categorical_columns = list(artifact.get('categorical_columns', []))
            else:
                # If saved as pure pipeline
                self.ml_pipeline = artifact
                self.numeric_columns = []
                self.categorical_columns = []
            print(f"✅ ML model loaded from {model_path}")
        except Exception as e:
            print(f"❌ Failed to load ML model: {e}")
            self.ml_pipeline = None
    
    async def get_ml_score(self, transaction: Transaction) -> int:
        """Get ML-based risk score using the loaded pipeline. Returns integer 0..100."""
        if self.ml_pipeline is None:
            return 0
        try:
            # Build a single-row frame using known columns; default None if missing.
            row: Dict[str, Any] = {}
            # Map common fields (training columns may differ; using best-effort names)
            mapping = {
                'amount': getattr(transaction, 'amount', None),
                'Transaction_Distance': getattr(transaction, 'transaction_distance', None),
                'Transaction_Type': getattr(transaction, 'transaction_type', None),
                'Device_Type': getattr(transaction, 'device_type', None),
                'Merchant_Category': getattr(transaction, 'merchant_category', None),
                'Card_Type': getattr(transaction, 'card_type', None),
                'Authentication_Method': getattr(transaction, 'authentication_method', None),
                'Location': getattr(transaction, 'location', None),
                'User_ID': getattr(transaction, 'sender_id', None),
            }
            # Engineered flags (conservative defaults)
            mapping.update({
                'is_unusual_location': 0,
                'is_unusual_merchant': 0,
                'is_unusual_auth': 0,
            })

            cols = self.numeric_columns + self.categorical_columns
            if cols:
                for c in cols:
                    row[c] = mapping.get(c, None)
            else:
                row = mapping

            X = pd.DataFrame([row])
            # Predict_proba if available else decision_function
            model = self.ml_pipeline
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(X)[0][1]
            else:
                pred = model.predict(X)
                proba = float(pred[0])
            return int(max(0.0, min(1.0, float(proba))) * 100)
        except Exception as e:
            print(f"❌ ML scoring failed: {e}")
            return 0

    async def get_risk_score(self, transaction: Transaction) -> int:
        """Get combined risk score for a transaction."""
        evaluation = await self.evaluate_transaction(transaction)
        rules_score = evaluation["risk_score"]
        
        # Add ML score if model is available
        ml_score = await self.get_ml_score(transaction)
        
        # Combine scores (weighted average: 70% rules, 30% ML)
        combined_score = int(0.7 * rules_score + 0.3 * ml_score)
        return min(combined_score, 100)

    def set_feature_importances(self, items: List[Dict[str, Any]]) -> None:
        self.feature_importances = items


# Global instance
fraud_engine = FraudEngine()
