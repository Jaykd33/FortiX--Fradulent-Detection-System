# app/core/scoring.py
from __future__ import annotations

from typing import Dict, List
import logging

from app.services.fraud_engine import fraud_engine  # exposes .model once loaded

logger = logging.getLogger("fortix.scoring")

# ---------------------------
# Simple rule configuration
# ---------------------------
HIGH_RISK_GEOS = {
    "Lagos, Nigeria", "Moscow, Russia", "Sofia, Bulgaria", "Bogota, Colombia",
    "Kyiv, Ukraine", "Karachi, Pakistan", "Beijing, China", "Manila, Philippines",
    "Nairobi, Kenya", "Warsaw, Poland", "Istanbul, Turkey", "Dubai, UAE",
}

TXN_TYPES = ["UPI", "WALLET", "CREDIT_CARD"]  # keep in a fixed order


def _one_hot_txn_type(txn_type: str) -> List[int]:
    t = (txn_type or "").strip().upper()
    return [1 if t == k else 0 for k in TXN_TYPES]


def _rule_score(p: Dict) -> float:
    """
    Very lightweight rules so your UI lights up even without the model.
    Tune thresholds as you like.
    """
    try:
        amt = float(p.get("amount", 0) or 0)
    except Exception:
        amt = 0.0

    geo = (p.get("geo_location") or "").strip()

    score = 0.0
    if amt >= 25000:           # high amount
        score += 0.25
    if geo in HIGH_RISK_GEOS:  # unusual geos
        score += 0.35

    # Clamp to [0,1]
    return 1.0 if score > 1.0 else (0.0 if score < 0.0 else score)


def build_features(p: Dict) -> List[float]:
    """
    Build the exact feature vector your model expects.
    This default assumes the model was trained on:
      [ amount, is_UPI, is_WALLET, is_CREDIT_CARD ]

    If your model needs more (e.g., encodings for geo/device/ip), extend here.
    """
    try:
        amt = float(p.get("amount", 0) or 0)
    except Exception:
        amt = 0.0

    txn_oh = _one_hot_txn_type(p.get("transaction_type", ""))
    return [amt] + txn_oh


def _predict_proba01(model, X: List[List[float]]) -> float:
    """
    Returns probability of the positive class in [0,1].
    Supports models with predict_proba or decision_function/predict fallback.
    """
    # Common case
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)
        # proba shape: (n_samples, 2) -> take [:, 1]
        return float(proba[0][1])

    # Some sklearn pipelines expose decision_function
    if hasattr(model, "decision_function"):
        import numpy as np

        df = float(model.decision_function(X)[0])
        # squish to [0,1] (not perfect, but avoids crashes)
        return float(1 / (1 + np.exp(-df)))

    # Fallback to predict (0/1)
    if hasattr(model, "predict"):
        pred = int(model.predict(X)[0])
        return float(pred)

    # No supported interface
    logger.error("Model has no predict_proba/decision_function/predict; returning 0.0")
    return 0.0


def score_transaction(payload: Dict) -> float:
    """
    Compute the final risk score in [0,1] by blending model probability with rules.
    If the model isn't loaded or fails, return rule-only.

    Returns: float in [0,1]
    """
    # Always compute rules so the app shows signal even without model
    rules = _rule_score(payload)

    model = getattr(fraud_engine, "model", None)
    if model is None:
        logger.warning("Model not loaded; returning rule-only score: %.3f", rules)
        return rules

    try:
        X = [build_features(payload)]
        proba = _predict_proba01(model, X)
    except Exception:
        logger.exception("Model scoring failed; using rule-only")
        return rules

    # Blend (tune weights to your preference)
    final = 0.7 * proba + 0.3 * rules
    # Clamp
    if final < 0.0:
        final = 0.0
    elif final > 1.0:
        final = 1.0
    return final
