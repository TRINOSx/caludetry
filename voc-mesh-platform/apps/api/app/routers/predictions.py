from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_tenant
from app.database import get_db
from app.models.prediction import MLPrediction

router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])


class PredictionOut(BaseModel):
    time: datetime
    parcela_id: UUID
    tenant_id: UUID
    stress_pct: float | None
    bloom_pct: float | None
    pest_zone_detected: bool
    pest_type: str | None
    carbon_index: float | None
    fire_alert: bool
    model_version: str | None

    model_config = {"from_attributes": True}


@router.get("/{parcela_id}", response_model=PredictionOut | None)
async def get_latest_prediction(
    parcela_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
):
    result = await db.execute(
        select(MLPrediction)
        .where(
            MLPrediction.parcela_id == parcela_id,
            MLPrediction.tenant_id == tenant_id,
        )
        .order_by(MLPrediction.time.desc())
        .limit(1)
    )
    pred = result.scalar_one_or_none()
    if not pred:
        raise HTTPException(status_code=404, detail="No predictions found")
    return pred


@router.get("/{parcela_id}/history", response_model=list[PredictionOut])
async def get_prediction_history(
    parcela_id: UUID,
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    limit: int = Query(50, le=500),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
):
    query = select(MLPrediction).where(
        MLPrediction.parcela_id == parcela_id,
        MLPrediction.tenant_id == tenant_id,
    )
    if start:
        query = query.where(MLPrediction.time >= start)
    if end:
        query = query.where(MLPrediction.time <= end)

    query = query.order_by(MLPrediction.time.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
