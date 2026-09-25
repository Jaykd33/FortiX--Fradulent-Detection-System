from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.models.transaction import Transaction, Alert

router = APIRouter()


@router.get("/entities/user/{user_id}")
async def get_user_profile(user_id: str, db: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    try:
        # Average risk
        avg_risk_res = await db.execute(
            select(func.avg(Transaction.risk_score)).where(Transaction.sender_id == user_id)
        )
        avg_risk = avg_risk_res.scalar()

        # Most common attributes
        def top_value(column):
            res = db.execute(
                select(column, func.count().label("cnt"))
                .where(Transaction.sender_id == user_id)
                .group_by(column)
                .order_by(func.count().desc())
                .limit(1)
            )
            return res

        loc_res = await db.execute(
            select(Transaction.location, func.count().label("cnt"))
            .where(Transaction.sender_id == user_id)
            .group_by(Transaction.location)
            .order_by(func.count().desc())
            .limit(1)
        )
        top_location = (loc_res.first() or (None, None))[0]

        cat_res = await db.execute(
            select(Transaction.merchant_category, func.count().label("cnt"))
            .where(Transaction.sender_id == user_id)
            .group_by(Transaction.merchant_category)
            .order_by(func.count().desc())
            .limit(1)
        )
        top_category = (cat_res.first() or (None, None))[0]

        dev_res = await db.execute(
            select(Transaction.device_type, func.count().label("cnt"))
            .where(Transaction.sender_id == user_id)
            .group_by(Transaction.device_type)
            .order_by(func.count().desc())
            .limit(1)
        )
        top_device = (dev_res.first() or (None, None))[0]

        # Recent transactions
        recent_res = await db.execute(
            select(Transaction)
            .where(Transaction.sender_id == user_id)
            .order_by(Transaction.created_at.desc())
            .limit(10)
        )
        recents = [
            {
                "id": str(t.id),
                "amount": t.amount,
                "risk_score": t.risk_score,
                "status": t.status,
                "transaction_type": t.transaction_type,
                "location": t.location,
                "merchant_category": t.merchant_category,
                "device_type": t.device_type,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in recent_res.scalars().all()
        ]

        # Alert count
        alert_res = await db.execute(
            select(func.count(Alert.id)).join(Transaction, Alert.transaction_id == Transaction.id).where(Transaction.sender_id == user_id)
        )
        alert_count = alert_res.scalar() or 0

        return {
            "user_id": user_id,
            "avg_risk_score": round(float(avg_risk), 2) if avg_risk is not None else 0.0,
            "most_common": {
                "location": top_location,
                "merchant_category": top_category,
                "device_type": top_device,
            },
            "recent_transactions": recents,
            "total_alerts": int(alert_count),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building user profile: {str(e)}")


