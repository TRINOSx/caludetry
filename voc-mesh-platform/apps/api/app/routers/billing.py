from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_tenant
from app.database import get_db
from app.models.billing import BillingEvent
from app.models.parcela import Parcela
from app.models.sensor import Sensor, VOCReading
from app.models.tenant import Tenant

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


class BillingEstimate(BaseModel):
    tenant_id: UUID
    tier: str
    sensor_count: int
    km2_covered: float
    base_amount_usd: float
    overage_usd: float
    total_usd: float
    period_start: datetime
    period_end: datetime


class BillingEventOut(BaseModel):
    id: UUID
    tenant_id: UUID
    period_start: datetime
    period_end: datetime
    sensor_count: int
    km2_covered: float
    amount_usd: float
    tier: str
    paid: bool

    model_config = {"from_attributes": True}


class UsageOut(BaseModel):
    sensor_count: int
    km2_covered: float
    readings_count: int
    api_calls: int


# ---------------------------------------------------------------------------
# Tier base km2 included (for overage calculation)
# ---------------------------------------------------------------------------
TIER_INCLUDED_KM2 = {
    "AGRO_BASIC": 50.0,
    "FORESTRY_BASIC": 200.0,
    "AGRO_ENTERPRISE": 999_999.0,
}
OVERAGE_RATE_PER_KM2 = 0.50  # USD per extra km²


async def calculate_monthly_billing(
    tenant_id: UUID, db: AsyncSession
) -> BillingEstimate:
    """Calculate current-month billing estimate for a tenant."""
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    now = datetime.now(timezone.utc)
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Count active sensors
    sensor_count_result = await db.execute(
        select(func.count(Sensor.id)).where(
            Sensor.tenant_id == tenant_id, Sensor.active.is_(True)
        )
    )
    sensor_count = sensor_count_result.scalar() or 0

    # Sum km² covered
    km2_result = await db.execute(
        select(func.coalesce(func.sum(Parcela.area_km2), 0.0)).where(
            Parcela.tenant_id == tenant_id
        )
    )
    km2_covered = float(km2_result.scalar() or 0.0)

    base_amount = sensor_count * tenant.billing_usd_per_sensor
    included_km2 = TIER_INCLUDED_KM2.get(tenant.tier, 50.0)
    overage_km2 = max(0.0, km2_covered - included_km2)
    overage_usd = overage_km2 * OVERAGE_RATE_PER_KM2

    return BillingEstimate(
        tenant_id=tenant_id,
        tier=tenant.tier,
        sensor_count=sensor_count,
        km2_covered=km2_covered,
        base_amount_usd=base_amount,
        overage_usd=overage_usd,
        total_usd=base_amount + overage_usd,
        period_start=period_start,
        period_end=now,
    )


@router.get("/current", response_model=BillingEstimate)
async def get_current_billing(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
):
    return await calculate_monthly_billing(tenant_id, db)


@router.get("/history", response_model=list[BillingEventOut])
async def get_billing_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, le=50),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
):
    offset = (page - 1) * page_size
    result = await db.execute(
        select(BillingEvent)
        .where(BillingEvent.tenant_id == tenant_id)
        .order_by(BillingEvent.period_start.desc())
        .offset(offset)
        .limit(page_size)
    )
    return result.scalars().all()


@router.get("/usage", response_model=UsageOut)
async def get_usage(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
):
    sensor_count_result = await db.execute(
        select(func.count(Sensor.id)).where(
            Sensor.tenant_id == tenant_id, Sensor.active.is_(True)
        )
    )
    sensor_count = sensor_count_result.scalar() or 0

    km2_result = await db.execute(
        select(func.coalesce(func.sum(Parcela.area_km2), 0.0)).where(
            Parcela.tenant_id == tenant_id
        )
    )
    km2_covered = float(km2_result.scalar() or 0.0)

    readings_count_result = await db.execute(
        select(func.count()).select_from(VOCReading).where(
            VOCReading.tenant_id == tenant_id
        )
    )
    readings_count = readings_count_result.scalar() or 0

    return UsageOut(
        sensor_count=sensor_count,
        km2_covered=km2_covered,
        readings_count=readings_count,
        api_calls=0,  # Would be tracked via middleware in production
    )
