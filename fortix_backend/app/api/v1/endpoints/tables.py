from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, TEXT
from typing import List, Dict, Any, Optional

from app.core.db import get_db_session
from app.models.transaction import Transaction, Alert

router = APIRouter()


@router.get("/transactions")
async def get_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Get paginated list of all transactions."""
    
    try:
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count
        total_result = await db.execute(select(func.count(Transaction.id)))
        total_transactions = total_result.scalar() or 0
        
        # Get paginated transactions
        result = await db.execute(
            select(Transaction)
            .order_by(Transaction.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        
        transactions = result.scalars().all()
        
        # Format for frontend
        transactions_data = []
        for tx in transactions:
            transactions_data.append({
                "id": str(tx.id),
                "amount": tx.amount,
                "currency": tx.currency,
                "transaction_type": tx.transaction_type,
                "sender_id": tx.sender_id,
                "receiver_id": tx.receiver_id,
                "device_fingerprint": tx.device_fingerprint,
                "ip_address": tx.ip_address,
                "geo_location": tx.geo_location,
                "risk_score": tx.risk_score,
                "status": tx.status,
                "created_at": tx.created_at.isoformat() if tx.created_at else None
            })
        
        return {
            "transactions": transactions_data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_transactions,
                "total_pages": (total_transactions + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching transactions: {str(e)}")


@router.get("/alerts")
async def get_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Get paginated list of flagged transactions (alerts)."""
    
    try:
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count of flagged transactions
        total_result = await db.execute(
            select(func.count(Transaction.id)).where(Transaction.status == "flagged")
        )
        total_alerts = total_result.scalar() or 0
        
        # Get paginated flagged transactions with alert details
        query = text("""
            SELECT 
                t.id,
                t.amount,
                t.currency,
                t.transaction_type,
                t.sender_id,
                t.receiver_id,
                t.device_fingerprint,
                t.ip_address,
                t.geo_location,
                t.risk_score,
                t.status,
                t.created_at,
                a.severity,
                a.rule_name,
                a.description,
                a.is_active
            FROM transactions t
            LEFT JOIN alerts a ON t.id = a.transaction_id
            WHERE t.status = 'flagged'
            ORDER BY t.created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        result = await db.execute(query, {"limit": page_size, "offset": offset})
        rows = result.fetchall()
        
        # Format for frontend
        alerts_data = []
        for row in rows:
            alerts_data.append({
                "transaction_id": str(row[0]),
                "amount": row[1],
                "currency": row[2],
                "transaction_type": row[3],
                "sender_id": row[4],
                "receiver_id": row[5],
                "device_fingerprint": row[6],
                "ip_address": row[7],
                "geo_location": row[8],
                "risk_score": row[9],
                "status": row[10],
                "created_at": row[11].isoformat() if row[11] else None,
                "alert_severity": row[12],
                "alert_rule_name": row[13],
                "alert_description": row[14],
                "alert_is_active": row[15]
            })
        
        return {
            "alerts": alerts_data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_alerts,
                "total_pages": (total_alerts + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")


@router.get("/transactions/search")
async def search_transactions(
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Search transactions by sender_id, receiver_id, or transaction_type."""
    
    try:
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Build search query
        search_query = f"%{query}%"
        
        # Get total count
        total_result = await db.execute(
            select(func.count(Transaction.id)).where(
                TEXT("sender_id ILIKE :query OR receiver_id ILIKE :query OR transaction_type ILIKE :query")
            ),
            {"query": search_query}
        )
        total_results = total_result.scalar() or 0
        
        # Get paginated search results
        result = await db.execute(
            select(Transaction).where(
                TEXT("sender_id ILIKE :query OR receiver_id ILIKE :query OR transaction_type ILIKE :query")
            )
            .order_by(Transaction.created_at.desc())
            .offset(offset)
            .limit(page_size),
            {"query": search_query}
        )
        
        transactions = result.scalars().all()
        
        # Format for frontend
        transactions_data = []
        for tx in transactions:
            transactions_data.append({
                "id": str(tx.id),
                "amount": tx.amount,
                "currency": tx.currency,
                "transaction_type": tx.transaction_type,
                "sender_id": tx.sender_id,
                "receiver_id": tx.receiver_id,
                "device_fingerprint": tx.device_fingerprint,
                "ip_address": tx.ip_address,
                "geo_location": tx.geo_location,
                "risk_score": tx.risk_score,
                "status": tx.status,
                "created_at": tx.created_at.isoformat() if tx.created_at else None
            })
        
        return {
            "transactions": transactions_data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_results,
                "total_pages": (total_results + page_size - 1) // page_size
            },
            "search_query": query
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching transactions: {str(e)}")


@router.get("/transaction/{transaction_id}")
async def get_transaction_details(
    transaction_id: str,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Get detailed information about a specific transaction."""
    
    try:
        # Get transaction
        result = await db.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Get associated alerts
        alerts_result = await db.execute(
            select(Alert).where(Alert.transaction_id == transaction_id)
        )
        alerts = alerts_result.scalars().all()
        
        # Format transaction data
        transaction_data = {
            "id": str(transaction.id),
            "amount": transaction.amount,
            "currency": transaction.currency,
            "transaction_type": transaction.transaction_type,
            "sender_id": transaction.sender_id,
            "receiver_id": transaction.receiver_id,
            "device_fingerprint": transaction.device_fingerprint,
            "ip_address": transaction.ip_address,
            "geo_location": transaction.geo_location,
            "risk_score": transaction.risk_score,
            "status": transaction.status,
            "created_at": transaction.created_at.isoformat() if transaction.created_at else None,
            "alerts": []
        }
        
        # Format alerts data
        for alert in alerts:
            transaction_data["alerts"].append({
                "id": str(alert.id),
                "severity": alert.severity,
                "rule_name": alert.rule_name,
                "description": alert.description,
                "is_active": alert.is_active,
                "created_at": alert.created_at.isoformat() if alert.created_at else None
            })
        
        return transaction_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching transaction details: {str(e)}")
