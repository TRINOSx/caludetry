from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_tenant
from app.database import get_db
from app.models.parcela import Parcela
from app.models.prediction import MLPrediction
from app.models.sensor import Sensor, VOCReading

router = APIRouter(prefix="/api/v1/parcelas", tags=["parcelas"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ParcelaCreate(BaseModel):
    name: str
    crop_type: str
    area_km2: float = 0.0
    geojson: dict | None = None


class ParcelaOut(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    crop_type: str
    area_km2: float
    geojson: dict | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[ParcelaOut])
async def list_parcelas(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
):
    result = await db.execute(
        select(Parcela).where(Parcela.tenant_id == tenant_id)
    )
    return result.scalars().all()


@router.post("/", response_model=ParcelaOut, status_code=201)
async def create_parcela(
    body: ParcelaCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
):
    parcela = Parcela(
        tenant_id=tenant_id,
        name=body.name,
        crop_type=body.crop_type,
        area_km2=body.area_km2,
        geojson=body.geojson,
    )
    db.add(parcela)
    await db.flush()
    await db.refresh(parcela)
    return parcela


@router.get("/{parcela_id}", response_model=ParcelaOut)
async def get_parcela(
    parcela_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
):
    result = await db.execute(
        select(Parcela).where(
            Parcela.id == parcela_id, Parcela.tenant_id == tenant_id
        )
    )
    parcela = result.scalar_one_or_none()
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela not found")
    return parcela


@router.get("/{parcela_id}/live")
async def get_parcela_live(
    parcela_id: UUID,
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Polling endpoint: latest readings + latest prediction for a parcela."""
    # Verify parcela belongs to tenant
    parcela_result = await db.execute(
        select(Parcela).where(
            Parcela.id == parcela_id, Parcela.tenant_id == tenant_id
        )
    )
    parcela = parcela_result.scalar_one_or_none()
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela not found")

    # Get sensors in this parcela
    sensors_result = await db.execute(
        select(Sensor).where(
            Sensor.parcela_id == parcela_id, Sensor.tenant_id == tenant_id
        )
    )
    sensors = sensors_result.scalars().all()
    sensor_ids = [s.id for s in sensors]

    # Latest readings across all sensors in parcela
    readings = []
    if sensor_ids:
        readings_result = await db.execute(
            select(VOCReading)
            .where(
                VOCReading.sensor_id.in_(sensor_ids),
                VOCReading.tenant_id == tenant_id,
            )
            .order_by(VOCReading.time.desc())
            .limit(limit)
        )
        readings = [
            {
                "time": r.time.isoformat(),
                "sensor_id": str(r.sensor_id),
                "compound": r.compound,
                "value_ppm": r.value_ppm,
                "temperature_c": r.temperature_c,
                "humidity_pct": r.humidity_pct,
            }
            for r in readings_result.scalars().all()
        ]

    # Latest prediction
    pred_result = await db.execute(
        select(MLPrediction)
        .where(
            MLPrediction.parcela_id == parcela_id,
            MLPrediction.tenant_id == tenant_id,
        )
        .order_by(MLPrediction.time.desc())
        .limit(1)
    )
    pred = pred_result.scalar_one_or_none()
    prediction = None
    if pred:
        prediction = {
            "time": pred.time.isoformat(),
            "stress_pct": pred.stress_pct,
            "bloom_pct": pred.bloom_pct,
            "pest_zone_detected": pred.pest_zone_detected,
            "pest_type": pred.pest_type,
            "carbon_index": pred.carbon_index,
            "fire_alert": pred.fire_alert,
            "model_version": pred.model_version,
        }

    return {
        "parcela_id": str(parcela_id),
        "sensor_count": len(sensors),
        "latest_readings": readings,
        "latest_prediction": prediction,
    }


@router.get("/{parcela_id}/status")
async def get_parcela_status(
    parcela_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Aggregated plant status metrics for a parcela."""
    parcela_result = await db.execute(
        select(Parcela).where(
            Parcela.id == parcela_id, Parcela.tenant_id == tenant_id
        )
    )
    parcela = parcela_result.scalar_one_or_none()
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela not found")

    # Count active sensors
    sensor_count_result = await db.execute(
        select(func.count(Sensor.id)).where(
            Sensor.parcela_id == parcela_id,
            Sensor.tenant_id == tenant_id,
            Sensor.active.is_(True),
        )
    )
    sensor_count = sensor_count_result.scalar() or 0

    # Latest prediction for status metrics
    pred_result = await db.execute(
        select(MLPrediction)
        .where(
            MLPrediction.parcela_id == parcela_id,
            MLPrediction.tenant_id == tenant_id,
        )
        .order_by(MLPrediction.time.desc())
        .limit(1)
    )
    pred = pred_result.scalar_one_or_none()

    return {
        "parcela_id": str(parcela_id),
        "name": parcela.name,
        "crop_type": parcela.crop_type,
        "area_km2": parcela.area_km2,
        "active_sensors": sensor_count,
        "stress_pct": pred.stress_pct if pred else None,
        "bloom_pct": pred.bloom_pct if pred else None,
        "pest_zone_detected": pred.pest_zone_detected if pred else False,
        "fire_alert": pred.fire_alert if pred else False,
        "carbon_index": pred.carbon_index if pred else None,
    }
