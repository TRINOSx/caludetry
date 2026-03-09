import hashlib
import json
from uuid import UUID

import anthropic
import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_tenant
from app.config import Settings, get_settings
from app.database import get_db
from app.models.parcela import Parcela
from app.models.prediction import MLPrediction
from app.models.sensor import Sensor, VOCReading
from app.models.tenant import FeatureFlag

router = APIRouter(prefix="/api/v1/insights", tags=["insights"])

INSIGHT_CACHE_TTL = 3600  # 1 hour


class InsightAction(BaseModel):
    action: str
    priority: str
    details: str


class InsightResponse(BaseModel):
    summary: str
    urgency_level: str
    recommended_actions: list[InsightAction]
    scientific_reasoning: str


SYSTEM_PROMPT = """Eres un agrónomo experto con 20 años de experiencia analizando datos
de Compuestos Orgánicos Volátiles (VOC) en cultivos. Tu tarea es interpretar los datos
de sensores VOC, predicciones de modelos de ML y condiciones ambientales para generar
recomendaciones agronómicas precisas y accionables.

Responde SIEMPRE en español. Tu análisis debe ser científicamente riguroso pero
accesible para agricultores. Estructura tu respuesta como JSON válido con los campos:
- summary: resumen ejecutivo (2-3 oraciones)
- urgency_level: uno de "baja", "media", "alta", "critica"
- recommended_actions: lista de objetos con {action, priority, details}
- scientific_reasoning: explicación técnica del razonamiento
"""


@router.post("/{parcela_id}", response_model=InsightResponse)
async def generate_insights(
    parcela_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    settings: Settings = Depends(get_settings),
):
    # Check feature flag: ai_insights_enabled
    flag_result = await db.execute(
        select(FeatureFlag).where(
            FeatureFlag.tenant_id == tenant_id,
            FeatureFlag.flag_name == "ai_insights_enabled",
        )
    )
    flag = flag_result.scalar_one_or_none()
    if not flag or not flag.enabled:
        raise HTTPException(
            status_code=403,
            detail="AI Insights feature is not enabled for this tenant. "
            "Upgrade to AGRO_ENTERPRISE tier.",
        )

    # Verify parcela belongs to tenant
    parcela_result = await db.execute(
        select(Parcela).where(
            Parcela.id == parcela_id, Parcela.tenant_id == tenant_id
        )
    )
    parcela = parcela_result.scalar_one_or_none()
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela not found")

    # Gather latest readings from sensors in this parcela
    sensors_result = await db.execute(
        select(Sensor).where(
            Sensor.parcela_id == parcela_id, Sensor.tenant_id == tenant_id
        )
    )
    sensors = sensors_result.scalars().all()
    sensor_ids = [s.id for s in sensors]

    readings_data = []
    if sensor_ids:
        readings_result = await db.execute(
            select(VOCReading)
            .where(
                VOCReading.sensor_id.in_(sensor_ids),
                VOCReading.tenant_id == tenant_id,
            )
            .order_by(VOCReading.time.desc())
            .limit(50)
        )
        for r in readings_result.scalars().all():
            readings_data.append(
                {
                    "time": r.time.isoformat(),
                    "compound": r.compound,
                    "value_ppm": r.value_ppm,
                    "temperature_c": r.temperature_c,
                    "humidity_pct": r.humidity_pct,
                }
            )

    # Get latest ML prediction
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
    prediction_data = {}
    if pred:
        prediction_data = {
            "stress_pct": pred.stress_pct,
            "bloom_pct": pred.bloom_pct,
            "pest_zone_detected": pred.pest_zone_detected,
            "pest_type": pred.pest_type,
            "carbon_index": pred.carbon_index,
            "fire_alert": pred.fire_alert,
        }

    # Build user prompt
    user_prompt = f"""Analiza los siguientes datos de la parcela "{parcela.name}"
(cultivo: {parcela.crop_type}, área: {parcela.area_km2} km²):

## Lecturas VOC recientes (últimas 50):
{json.dumps(readings_data, indent=2, default=str)}

## Predicciones del modelo ML:
{json.dumps(prediction_data, indent=2, default=str)}

## Sensores activos: {len(sensors)}

Genera un análisis agronómico completo con recomendaciones accionables.
Responde en JSON válido con los campos: summary, urgency_level, recommended_actions, scientific_reasoning.
"""

    # Check Redis cache
    cache_key = f"insights:{tenant_id}:{parcela_id}"
    content_hash = hashlib.sha256(user_prompt.encode()).hexdigest()[:16]
    cache_key_full = f"{cache_key}:{content_hash}"

    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        cached = await redis_client.get(cache_key_full)
        if cached:
            await redis_client.aclose()
            return InsightResponse(**json.loads(cached))
    except Exception:
        redis_client = None

    # Call Anthropic Claude API
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Anthropic API key not configured",
        )

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # Parse Claude response
    response_text = message.content[0].text
    try:
        # Strip markdown code fences if present
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        insight_data = json.loads(cleaned)
        insight = InsightResponse(**insight_data)
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to parse AI response: {exc}",
        )

    # Cache result in Redis
    try:
        if redis_client:
            await redis_client.setex(
                cache_key_full, INSIGHT_CACHE_TTL, insight.model_dump_json()
            )
            await redis_client.aclose()
    except Exception:
        pass  # Non-fatal: cache miss is acceptable

    return insight
