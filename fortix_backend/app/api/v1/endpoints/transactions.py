from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.scoring import score_transaction
from app.core.db import get_db_session
from app.models.transaction import Transaction as TransactionModel, Alert as AlertModel
from app.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
)
from app.services.fraud_engine import fraud_engine
import uuid
import numpy as np

router = APIRouter()


@router.get("/transactions", response_model=List[TransactionRead])
async def list_transactions(db: AsyncSession = Depends(get_db_session)) -> List[TransactionRead]:
    result = await db.execute(select(TransactionModel).order_by(TransactionModel.created_at.desc()).limit(100))
    transactions = result.scalars().all()
    return [TransactionRead.model_validate(t) for t in transactions]


@router.get("/transactions/{transaction_id}")
async def get_transaction_detail(
    transaction_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    try:
        tx_id = uuid.UUID(transaction_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid transaction ID format")

    result = await db.execute(select(TransactionModel).where(TransactionModel.id == tx_id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Build risk factors based on user history
    risk_factors = []

    # 1) Unusual location compared to user's most common
    if tx.sender_id:
        loc_res = await db.execute(
            select(TransactionModel.location, func.count().label("cnt"))
            .where(TransactionModel.sender_id == tx.sender_id)
            .group_by(TransactionModel.location)
            .order_by(func.count().desc())
            .limit(1)
        )
        top_loc = (loc_res.first() or (None, None))[0]
        if top_loc and tx.location and tx.location != top_loc:
            risk_factors.append(f"Location '{tx.location}' differs from user's common location '{top_loc}'.")

    # 2) New merchant category in last 30 days
    if tx.sender_id and tx.merchant_category:
        from datetime import timedelta
        window_start = (tx.created_at - timedelta(days=30)) if tx.created_at else None
        q = (
            select(func.count(TransactionModel.id))
            .where(TransactionModel.sender_id == tx.sender_id)
            .where(TransactionModel.merchant_category == tx.merchant_category)
        )
        if window_start is not None:
            q = q.where(TransactionModel.created_at >= window_start)
        seen_count = (await db.execute(q)).scalar() or 0
        if seen_count == 0:
            risk_factors.append(f"Merchant category '{tx.merchant_category}' is new for the user in the last 30 days.")

    # 3) Authentication weaker than typical
    if tx.sender_id and tx.authentication_method:
        strength = {"Password": 1, "OTP": 2, "Biometric": 3, "HardwareToken": 4}
        user_strength_res = await db.execute(
            select(func.avg(func.coalesce(func.nullif(0,0), 0)))
        )
        # Compute average strength from historical rows
        hist_res = await db.execute(
            select(TransactionModel.authentication_method)
            .where(TransactionModel.sender_id == tx.sender_id)
            .where(TransactionModel.authentication_method.isnot(None))
        )
        hist_methods = [r[0] for r in hist_res.all()]
        if hist_methods:
            avg_strength = np.mean([strength.get(m, 1) for m in hist_methods])  # type: ignore
            current_strength = strength.get(tx.authentication_method, 1)
            if current_strength < avg_strength:
                risk_factors.append(
                    f"Authentication method '{tx.authentication_method}' is weaker than user's typical method."
                )

    # 4) Transaction distance unusually high
    if tx.transaction_distance is not None and tx.transaction_distance > 1000:
        risk_factors.append(f"Transaction distance ({int(tx.transaction_distance)} km) is unusually high.")

    return {
        **TransactionRead.model_validate(tx).model_dump(),
        "risk_factors": risk_factors,
    }

@router.post("/transactions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionCreate,
    db: AsyncSession = Depends(get_db_session)
) -> TransactionRead:
    # Create transaction (initial values; risk/status will be set below)
    transaction = TransactionModel(
        amount=payload.amount,
        currency=payload.currency,
        transaction_type=payload.transaction_type,
        sender_id=payload.sender_id,
        receiver_id=payload.receiver_id,
        device_fingerprint=payload.device_fingerprint,
        ip_address=payload.ip_address,
        geo_location=payload.geo_location,
        risk_score=payload.risk_score,  # may be None/0 from client; we overwrite
        status=payload.status or "processed",
    )
    db.add(transaction)
    await db.flush()  # Get the ID

    # --- 1) Our scorer (model+rules, or rules-only if model not loaded) ---
    # score_transaction returns [0,1]; convert to 0–100 for your thresholds
    try:
        base_score_01 = score_transaction(payload.model_dump())
        base_score = float(round(base_score_01 * 100, 2))
    except Exception:
        # if anything goes wrong, keep system alive
        base_score = 0.0

    transaction.risk_score = base_score

    # --- 2) (Optional) Blend with fraud_engine if it returns a score ---
    # If your fraud_engine is working, you can choose max/avg; using max is conservative.
    try:
        fe_score = await fraud_engine.get_risk_score(transaction)
        if fe_score is not None:
            # ensure it's a float 0–100
            fe_score = float(fe_score)
            transaction.risk_score = max(transaction.risk_score, fe_score)
    except Exception:
        # don’t break the request if the engine errors
        pass

    # --- 3) Status thresholds (0–100 scale) ---
    rs = transaction.risk_score
    if rs >= 70:
        transaction.status = "flagged"
    elif rs >= 30:
        transaction.status = "review"
    else:
        transaction.status = "processed"

    # --- 4) Alerts (keep your existing engine-based alerts) ---
    try:
        evaluation = await fraud_engine.evaluate_transaction(transaction)
        for alert_data in evaluation.get("alerts", []):
            alert = AlertModel(
                transaction_id=transaction.id,
                severity=alert_data["severity"],
                rule_name=alert_data["rule_name"],
                description=alert_data["description"],
                is_active=True,
            )
            db.add(alert)
    except Exception:
        # Silent failure is okay for now; logs can be added later
        pass

    await db.commit()
    await db.refresh(transaction)
    return TransactionRead.model_validate(transaction)



