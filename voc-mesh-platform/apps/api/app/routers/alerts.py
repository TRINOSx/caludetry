from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_tenant
from app.database import get_db
from app.models.prediction import MLPrediction

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("/")
async def list_active_alerts(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """
    Active alerts are derived from ML predictions that have
    pest_zone_detected=True or fire_alert=True.
    Returns the most recent alert-triggering predictions.
    """
    result = await db.execute(
        select(MLPrediction)
        .where(
            MLPrediction.tenant_id == tenant_id,
            (MLPrediction.pest_zone_detected.is_(True))
            | (MLPrediction.fire_alert.is_(True)),
        )
        .order_by(MLPrediction.time.desc())
        .limit(50)
    )
    predictions = result.scalars().all()

    alerts = []
    for p in predictions:
        alert_types = []
        if p.pest_zone_detected:
            alert_types.append("pest")
        if p.fire_alert:
            alert_types.append("fire")

        alerts.append(
            {
                "id": f"{p.parcela_id}-{p.time.isoformat()}",
                "parcela_id": str(p.parcela_id),
                "time": p.time.isoformat(),
                "alert_types": alert_types,
                "pest_type": p.pest_type,
                "stress_pct": p.stress_pct,
                "acknowledged": False,
            }
        )

    return {"alerts": alerts, "total": len(alerts)}


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    _tenant_id: UUID = Depends(get_current_tenant),
):
    """
    Acknowledge an alert. In a production system this would persist
    the acknowledgment; here we return a confirmation.
    """
    return {"alert_id": alert_id, "acknowledged": True}
