import secrets
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, get_current_tenant, require_admin
from app.database import get_db
from app.models.tenant import FeatureFlag, Tenant

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])

# ---------------------------------------------------------------------------
# Tier templates
# ---------------------------------------------------------------------------
TIER_TEMPLATES: dict[str, dict] = {
    "AGRO_BASIC": {
        "billing_usd_per_sensor": 9.0,
        "max_sensors": 50,
        "max_parcelas": 10,
        "flags": {
            "ai_insights_enabled": False,
            "pest_detection": True,
            "fire_alerts": False,
            "carbon_tracking": False,
        },
    },
    "FORESTRY_BASIC": {
        "billing_usd_per_sensor": 5.0,
        "max_sensors": 100,
        "max_parcelas": 20,
        "flags": {
            "ai_insights_enabled": False,
            "pest_detection": True,
            "fire_alerts": True,
            "carbon_tracking": True,
        },
    },
    "AGRO_ENTERPRISE": {
        "billing_usd_per_sensor": 25.0,
        "max_sensors": 999_999,
        "max_parcelas": 999_999,
        "flags": {
            "ai_insights_enabled": True,
            "pest_detection": True,
            "fire_alerts": True,
            "carbon_tracking": True,
        },
    },
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class TenantProvisionRequest(BaseModel):
    slug: str
    name: str
    tier: str
    contact_email: EmailStr


class TenantProvisionResponse(BaseModel):
    tenant_id: UUID
    api_key: str
    mqtt_credentials: dict
    dashboard_url: str


class FeatureFlagUpdate(BaseModel):
    flag_name: str
    enabled: bool
    config: dict | None = None


class TenantConfigResponse(BaseModel):
    tenant_id: UUID
    slug: str
    name: str
    tier: str
    max_sensors: int
    max_parcelas: int
    billing_usd_per_sensor: float
    active: bool
    feature_flags: list[dict]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/provision", response_model=TenantProvisionResponse, status_code=201)
async def provision_tenant(
    body: TenantProvisionRequest,
    db: AsyncSession = Depends(get_db),
):
    template = TIER_TEMPLATES.get(body.tier)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown tier '{body.tier}'. Valid: {list(TIER_TEMPLATES.keys())}",
        )

    # Check slug uniqueness
    existing = await db.execute(select(Tenant).where(Tenant.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant slug '{body.slug}' already exists",
        )

    tenant = Tenant(
        slug=body.slug,
        name=body.name,
        tier=body.tier,
        contact_email=body.contact_email,
        billing_usd_per_sensor=template["billing_usd_per_sensor"],
        max_sensors=template["max_sensors"],
        max_parcelas=template["max_parcelas"],
    )
    db.add(tenant)
    await db.flush()

    # Seed feature flags from tier template
    for flag_name, enabled in template["flags"].items():
        flag = FeatureFlag(
            tenant_id=tenant.id,
            flag_name=flag_name,
            enabled=enabled,
        )
        db.add(flag)

    # Generate JWT-based API key for the tenant
    api_key = create_access_token(
        data={"tenant_id": str(tenant.id), "role": "tenant"},
    )

    mqtt_username = f"tenant-{tenant.slug}"
    mqtt_password = secrets.token_urlsafe(32)

    return TenantProvisionResponse(
        tenant_id=tenant.id,
        api_key=api_key,
        mqtt_credentials={"username": mqtt_username, "password": mqtt_password},
        dashboard_url=f"https://app.vocmesh.io/{tenant.slug}/dashboard",
    )


@router.get("/{tenant_id}/config", response_model=TenantConfigResponse)
async def get_tenant_config(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current: UUID = Depends(get_current_tenant),
):
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id, Tenant.active.is_(True))
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    flags_result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.tenant_id == tenant_id)
    )
    flags = flags_result.scalars().all()

    return TenantConfigResponse(
        tenant_id=tenant.id,
        slug=tenant.slug,
        name=tenant.name,
        tier=tenant.tier,
        max_sensors=tenant.max_sensors,
        max_parcelas=tenant.max_parcelas,
        billing_usd_per_sensor=tenant.billing_usd_per_sensor,
        active=tenant.active,
        feature_flags=[
            {
                "id": str(f.id),
                "flag_name": f.flag_name,
                "enabled": f.enabled,
                "config": f.config,
            }
            for f in flags
        ],
    )


@router.patch("/{tenant_id}/feature-flags", status_code=200)
async def update_feature_flag(
    tenant_id: UUID,
    body: FeatureFlagUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: UUID = Depends(require_admin),
):
    result = await db.execute(
        select(FeatureFlag).where(
            FeatureFlag.tenant_id == tenant_id,
            FeatureFlag.flag_name == body.flag_name,
        )
    )
    flag = result.scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    await db.execute(
        update(FeatureFlag)
        .where(FeatureFlag.id == flag.id)
        .values(enabled=body.enabled, config=body.config)
    )
    return {"status": "updated", "flag_name": body.flag_name, "enabled": body.enabled}


@router.delete("/{tenant_id}", status_code=200)
async def soft_delete_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin: UUID = Depends(require_admin),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    await db.execute(
        update(Tenant).where(Tenant.id == tenant_id).values(active=False)
    )
    return {"status": "deactivated", "tenant_id": str(tenant_id)}
