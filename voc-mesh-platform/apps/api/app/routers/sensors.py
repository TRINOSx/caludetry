from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_tenant
from app.database import get_db
from app.models.sensor import Sensor, VOCReading

router = APIRouter(prefix="/api/v1/sensors", tags=["sensors"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class SensorCreate(BaseModel):
    parcela_id: UUID | None = None
    hardware_id: str
    sensor_type: str
    lat: float | None = None
    lng: float | None = None
    firmware_version: str | None = None


class SensorOut(BaseModel):
    id: UUID
    tenant_id: UUID
    parcela_id: UUID | None
    hardware_id: str
    sensor_type: str
    lat: float | None
    lng: float | None
    active: bool
    last_seen: datetime | None
    firmware_version: str | None

    model_config = {"from_attributes": True}


class ReadingIn(BaseModel):
    time: datetime | None = None
    compound: str
    value_ppm: float
    raw_adc: int | None = None
    temperature_c: float | None = None
    humidity_pct: float | None = None


class ReadingOut(BaseModel):
    time: datetime
    sensor_id: UUID
    tenant_id: UUID
    compound: str
    value_ppm: float
    raw_adc: int | None
    temperature_c: float | None
    humidity_pct: float | None

    model_config = {"from_attributes": True}


class BatchReadingsRequest(BaseModel):
    readings: list[ReadingIn]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[SensorOut])
async def list_sensors(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
):
    result = await db.execute(
        select(Sensor).where(Sensor.tenant_id == tenant_id, Sensor.active.is_(True))
    )
    return result.scalars().all()


@router.post("/", response_model=SensorOut, status_code=201)
async def register_sensor(
    body: SensorCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
):
    sensor = Sensor(
        tenant_id=tenant_id,
        parcela_id=body.parcela_id,
        hardware_id=body.hardware_id,
        sensor_type=body.sensor_type,
        lat=body.lat,
        lng=body.lng,
        firmware_version=body.firmware_version,
    )
    db.add(sensor)
    await db.flush()
    await db.refresh(sensor)
    return sensor


@router.get("/{sensor_id}", response_model=SensorOut)
async def get_sensor(
    sensor_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
):
    result = await db.execute(
        select(Sensor).where(Sensor.id == sensor_id, Sensor.tenant_id == tenant_id)
    )
    sensor = result.scalar_one_or_none()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor


@router.post("/{sensor_id}/readings", status_code=201)
async def batch_ingest_readings(
    sensor_id: UUID,
    body: BatchReadingsRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
):
    # Verify sensor belongs to tenant
    result = await db.execute(
        select(Sensor).where(Sensor.id == sensor_id, Sensor.tenant_id == tenant_id)
    )
    sensor = result.scalar_one_or_none()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    readings = []
    for r in body.readings:
        reading = VOCReading(
            time=r.time or datetime.utcnow(),
            sensor_id=sensor_id,
            tenant_id=tenant_id,
            compound=r.compound,
            value_ppm=r.value_ppm,
            raw_adc=r.raw_adc,
            temperature_c=r.temperature_c,
            humidity_pct=r.humidity_pct,
        )
        db.add(reading)
        readings.append(reading)

    # Update sensor last_seen
    sensor.last_seen = datetime.utcnow()
    await db.flush()

    return {"ingested": len(readings)}


@router.get("/{sensor_id}/readings", response_model=list[ReadingOut])
async def get_readings(
    sensor_id: UUID,
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
):
    query = select(VOCReading).where(
        VOCReading.sensor_id == sensor_id,
        VOCReading.tenant_id == tenant_id,
    )
    if start:
        query = query.where(VOCReading.time >= start)
    if end:
        query = query.where(VOCReading.time <= end)

    query = query.order_by(VOCReading.time.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
