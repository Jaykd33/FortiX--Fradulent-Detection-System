from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from app.core.db import get_db_session
from app.models.transaction import Transaction, Alert
from app.services.fraud_engine import fraud_engine

router = APIRouter()


@router.get("/kpis")
async def get_kpis(db: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """Get key performance indicators for the analytics dashboard."""
    
    try:
        # Total transactions
        total_result = await db.execute(select(func.count(Transaction.id)))
        total_transactions = total_result.scalar() or 0
        
        # Total alerts (high-risk transactions)
        alerts_result = await db.execute(select(func.count(Alert.id)))
        total_alerts = alerts_result.scalar() or 0
        
        # Flagged transactions
        flagged_result = await db.execute(
            select(func.count(Transaction.id)).where(Transaction.status == "flagged")
        )
        flagged_transactions = flagged_result.scalar() or 0
        
        # Calculate protection rate (percentage of transactions NOT flagged)
        protection_rate = ((total_transactions - flagged_transactions) / total_transactions * 100) if total_transactions > 0 else 0
        
        # Average risk score
        avg_risk_result = await db.execute(
            select(func.avg(Transaction.risk_score)).where(Transaction.risk_score.isnot(None))
        )
        avg_risk_score = avg_risk_result.scalar() or 0
        
        return {
            "total_transactions": total_transactions,
            "total_alerts": total_alerts,
            "flagged_transactions": flagged_transactions,
            "protection_rate": round(protection_rate, 2),
            "avg_risk_score": round(avg_risk_score, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching KPIs: {str(e)}")


@router.get("/risk_distribution")
async def get_risk_distribution(db: AsyncSession = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """Get risk score distribution for histogram chart."""
    
    try:
        # Query risk score distribution using SQL CASE statements
        query = text("""
            SELECT 
                CASE 
                    WHEN risk_score IS NULL OR risk_score < 10 THEN '0-10'
                    WHEN risk_score < 20 THEN '10-20'
                    WHEN risk_score < 30 THEN '20-30'
                    WHEN risk_score < 40 THEN '30-40'
                    WHEN risk_score < 50 THEN '40-50'
                    WHEN risk_score < 60 THEN '50-60'
                    WHEN risk_score < 70 THEN '60-70'
                    WHEN risk_score < 80 THEN '70-80'
                    WHEN risk_score < 90 THEN '80-90'
                    ELSE '90-100'
                END as risk_range,
                COUNT(*) as count
            FROM transactions 
            GROUP BY risk_range
            ORDER BY MIN(risk_score)
        """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        # Format for chart
        distribution = []
        for row in rows:
            distribution.append({
                "name": row[0],
                "count": row[1]
            })
        
        return distribution
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching risk distribution: {str(e)}")


@router.get("/fraud_by_type")
async def get_fraud_by_type(db: AsyncSession = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """Get fraud distribution by transaction type for pie chart."""
    
    try:
        # Query fraud by transaction type (only flagged transactions)
        query = text("""
            SELECT 
                transaction_type,
                COUNT(*) as count
            FROM transactions 
            WHERE status = 'flagged'
            GROUP BY transaction_type
            ORDER BY count DESC
        """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        # Format for chart
        fraud_by_type = []
        for row in rows:
            fraud_by_type.append({
                "type": row[0],
                "count": row[1]
            })
        
        return fraud_by_type
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching fraud by type: {str(e)}")


@router.get("/fraud_over_time")
async def get_fraud_over_time(db: AsyncSession = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """Group flagged (risk_score > 70) counts by date(created_at)."""
    try:
        stmt = (
            select(
                func.date(Transaction.created_at).label('date'),
                func.count(Transaction.id).label('fraud_count')
            )
            .where(Transaction.risk_score.isnot(None))
            .where(Transaction.risk_score > 70)
            .group_by(func.date(Transaction.created_at))
            .order_by(func.date(Transaction.created_at))
        )
        result = await db.execute(stmt)
        mappings = result.mappings().all()
        return [
            {"date": str(m['date']), "fraud_count": int(m['fraud_count'])}
            for m in mappings
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching fraud over time: {str(e)}")


@router.get("/top_risk_transactions")
async def get_top_risk_transactions(
    limit: int = 10,
    db: AsyncSession = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """Get top risk transactions for detailed analysis."""
    
    try:
        # Query top risk transactions
        result = await db.execute(
            select(Transaction)
            .where(Transaction.risk_score.isnot(None))
            .order_by(Transaction.risk_score.desc())
            .limit(limit)
        )
        
        transactions = result.scalars().all()
        
        # Format for frontend
        top_risk = []
        for tx in transactions:
            top_risk.append({
                "id": str(tx.id),
                "amount": tx.amount,
                "currency": tx.currency,
                "transaction_type": tx.transaction_type,
                "sender_id": tx.sender_id,
                "receiver_id": tx.receiver_id,
                "risk_score": tx.risk_score,
                "status": tx.status,
                "created_at": tx.created_at.isoformat() if tx.created_at else None
            })
        
        return top_risk
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching top risk transactions: {str(e)}")


@router.get("/locations")
async def get_transaction_locations(db: AsyncSession = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """Return transaction coordinates and risk for geo map.
    Expects Transaction.geo_location as "lat,lon" string or similar; skips invalid rows.
    """
    try:
        result = await db.execute(
            select(Transaction.id, Transaction.geo_location, Transaction.risk_score, Transaction.status)
            .where(Transaction.geo_location.isnot(None))
        )
        rows = result.all()
        data: List[Dict[str, Any]] = []
        for (tx_id, geo, risk, status) in rows:
            if not geo:
                continue
            lat, lon = None, None
            try:
                # common format: "lat,lon"
                parts = str(geo).split(",")
                if len(parts) >= 2:
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
            except Exception:
                continue
            if lat is None or lon is None:
                continue
            data.append({
                "id": str(tx_id),
                "lat": lat,
                "lon": lon,
                "risk_score": int(risk) if risk is not None else 0,
                "status": status,
            })
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching locations: {str(e)}")


@router.get("/fraud_map")
async def get_fraud_map(db: AsyncSession = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """High-risk transactions for map visualization (risk_score > 70)."""
    try:
        result = await db.execute(
            select(Transaction.location, Transaction.risk_score)
            .where(Transaction.risk_score.isnot(None))
            .where(Transaction.risk_score > 70)
            .where(Transaction.location.isnot(None))
        )
        rows = result.all()
        return [
            {"location": r[0], "risk_score": int(r[1]) if r[1] is not None else 0}
            for r in rows
            if r[0]
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching fraud map: {str(e)}")


@router.get("/risk_drivers")
async def get_risk_drivers() -> List[Dict[str, Any]]:
    """Return preloaded feature importance from fraud_engine (loaded on startup)."""
    try:
        items = getattr(fraud_engine, 'feature_importances', None)
        if items is None:
            return []
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error returning risk drivers: {str(e)}")


@router.get("/fraud_by_merchant_category")
async def fraud_by_merchant_category(db: AsyncSession = Depends(get_db_session)) -> List[Dict[str, Any]]:
    try:
        q = text(
            """
            SELECT merchant_category, COUNT(*) as count
            FROM transactions
            WHERE status = 'flagged' AND merchant_category IS NOT NULL AND merchant_category != ''
            GROUP BY merchant_category
            ORDER BY count DESC
            """
        )
        res = await db.execute(q)
        return [{"merchant_category": r[0], "count": r[1]} for r in res.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching fraud by merchant category: {str(e)}")


@router.get("/fraud_by_auth_method")
async def fraud_by_auth_method(db: AsyncSession = Depends(get_db_session)) -> List[Dict[str, Any]]:
    try:
        q = text(
            """
            SELECT authentication_method, COUNT(*) as count
            FROM transactions
            WHERE status = 'flagged' AND authentication_method IS NOT NULL AND authentication_method != ''
            GROUP BY authentication_method
            ORDER BY count DESC
            """
        )
        res = await db.execute(q)
        return [{"method": r[0], "count": r[1]} for r in res.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching fraud by authentication method: {str(e)}")


@router.get("/top_entities")
async def get_top_entities(
    role: str = "sender",
    limit: int = 5,
    db: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """Top entities (senders or receivers) by flagged transactions."""
    try:
        if role not in ("sender", "receiver"):
            raise HTTPException(status_code=400, detail="role must be 'sender' or 'receiver'")

        column = "sender_id" if role == "sender" else "receiver_id"
        query = text(
            f"""
            SELECT {column} AS entity, COUNT(*) AS count
            FROM transactions
            WHERE status = 'flagged' AND {column} IS NOT NULL AND {column} != ''
            GROUP BY {column}
            ORDER BY count DESC
            LIMIT :limit
            """
        )
        result = await db.execute(query, {"limit": limit})
        rows = result.fetchall()
        return [{"entity": r[0], "count": r[1]} for r in rows]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching top entities: {str(e)}")