#!/usr/bin/env python3
"""VOC inference queue consumer.

Runs an infinite loop that:
  1. BRPOP messages from ``voc:inference:queue`` in Redis
  2. Extracts 128-dim features from the sensor readings
  3. Runs applicable ML models (based on tenant feature flags)
  4. Writes predictions to the ``ml_predictions`` table via asyncpg
  5. Publishes results to MQTT topic ``voc/{tenant_slug}/{parcela_id}/predictions``
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

import asyncpg
import numpy as np
import redis

from feature_engine import extract_features
from models import ModelRegistry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-20s  %(levelname)-7s  %(message)s",
)
logger = logging.getLogger("worker")

# ---------------------------------------------------------------------------
# Configuration (env vars with sensible defaults)
# ---------------------------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://voc:voc@localhost:5432/voc")
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

INFERENCE_QUEUE = "voc:inference:queue"
BRPOP_TIMEOUT = 1  # seconds

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
registry = ModelRegistry()
_pg_pool: asyncpg.Pool | None = None
_mqtt_client: Any = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_redis() -> redis.Redis:
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


async def _get_pg_pool() -> asyncpg.Pool:
    global _pg_pool
    if _pg_pool is None:
        _pg_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    return _pg_pool


def _get_mqtt():
    """Lazy-init a paho-mqtt client (best-effort; MQTT is optional)."""
    global _mqtt_client
    if _mqtt_client is not None:
        return _mqtt_client
    try:
        import paho.mqtt.client as mqtt

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        client.loop_start()
        _mqtt_client = client
        logger.info("MQTT connected to %s:%s", MQTT_HOST, MQTT_PORT)
    except Exception as exc:
        logger.warning("MQTT unavailable (%s); predictions will not be published", exc)
        _mqtt_client = None
    return _mqtt_client


def _publish_mqtt(tenant_slug: str, parcela_id: str, payload: dict) -> None:
    client = _get_mqtt()
    if client is None:
        return
    topic = f"voc/{tenant_slug}/{parcela_id}/predictions"
    try:
        client.publish(topic, json.dumps(payload), qos=1)
    except Exception as exc:
        logger.warning("MQTT publish failed: %s", exc)


# ---------------------------------------------------------------------------
# Tenant feature flags
# ---------------------------------------------------------------------------

def _get_tenant_flags(r: redis.Redis, tenant_id: str) -> dict:
    """Look up tenant feature_flags from Redis (fall back to defaults)."""
    key = f"tenant:{tenant_id}:feature_flags"
    raw = r.get(key)
    if raw:
        return json.loads(raw)
    # Default: all models enabled
    return {
        "stress": True,
        "bloom": True,
        "pest": True,
        "fire": True,
        "carbon": True,
    }


def _get_tenant_slug(r: redis.Redis, tenant_id: str) -> str:
    slug = r.get(f"tenant:{tenant_id}:slug")
    return slug or tenant_id


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def run_models(features: np.ndarray, flags: dict) -> dict:
    """Run all enabled models and return a combined predictions dict."""
    results: dict[str, Any] = {}

    if flags.get("stress"):
        try:
            model = registry.get_model("stress")
            results["stress_pct"] = round(model.predict(features), 2)
        except Exception as exc:
            logger.error("stress model error: %s", exc)

    if flags.get("bloom"):
        try:
            model = registry.get_model("bloom")
            results["bloom_probability"] = round(model.predict(features), 4)
        except Exception as exc:
            logger.error("bloom model error: %s", exc)

    if flags.get("pest"):
        try:
            model = registry.get_model("pest")
            results["pest"] = model.predict(features)
        except Exception as exc:
            logger.error("pest model error: %s", exc)

    if flags.get("fire"):
        try:
            model = registry.get_model("fire")
            results["fire"] = model.predict(features)
        except Exception as exc:
            logger.error("fire model error: %s", exc)

    if flags.get("carbon"):
        try:
            model = registry.get_model("carbon")
            results["carbon_index"] = round(model.predict(features), 2)
        except Exception as exc:
            logger.error("carbon model error: %s", exc)

    return results


async def store_predictions(
    parcela_id: str,
    tenant_id: str,
    predictions: dict,
    ts: str,
) -> None:
    """Insert predictions into the ``ml_predictions`` table."""
    pool = await _get_pg_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO ml_predictions
                (parcela_id, tenant_id, predictions, inferred_at, created_at)
            VALUES ($1, $2, $3::jsonb, $4, NOW())
            """,
            parcela_id,
            tenant_id,
            json.dumps(predictions),
            datetime.fromisoformat(ts) if ts else datetime.now(timezone.utc),
        )


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

async def process_message(r: redis.Redis, raw_message: str) -> None:
    """Parse, infer, store, publish."""
    try:
        msg = json.loads(raw_message)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in queue: %s", raw_message[:200])
        return

    parcela_id = msg.get("parcela_id", "unknown")
    tenant_id = msg.get("tenant_id", "unknown")
    readings = msg.get("readings", [])
    timestamp = msg.get("timestamp", datetime.now(timezone.utc).isoformat())

    if not readings:
        logger.warning("Empty readings for parcela=%s tenant=%s", parcela_id, tenant_id)
        return

    logger.info(
        "Processing parcela=%s  tenant=%s  readings=%d",
        parcela_id, tenant_id, len(readings),
    )

    # Feature extraction
    features = extract_features(readings)

    # Tenant flags
    flags = _get_tenant_flags(r, tenant_id)
    tenant_slug = _get_tenant_slug(r, tenant_id)

    # Inference
    predictions = run_models(features, flags)
    predictions["timestamp"] = timestamp

    # Persist
    try:
        await store_predictions(parcela_id, tenant_id, predictions, timestamp)
    except Exception as exc:
        logger.error("DB write failed: %s", exc)

    # Publish
    _publish_mqtt(tenant_slug, parcela_id, predictions)

    logger.info("Predictions for parcela=%s: %s", parcela_id, json.dumps(predictions))


async def main() -> None:
    logger.info("Loading model registry...")
    registry.load_all(onnx_dir=os.path.join(os.path.dirname(__file__), "models"))
    logger.info("Models available: %s", registry.available)

    r = _get_redis()
    logger.info("Worker started  |  queue=%s  redis=%s", INFERENCE_QUEUE, REDIS_URL)

    while True:
        try:
            result = r.brpop(INFERENCE_QUEUE, timeout=BRPOP_TIMEOUT)
            if result is None:
                continue  # timeout, loop again
            _queue_name, raw_message = result
            await process_message(r, raw_message)
        except redis.ConnectionError as exc:
            logger.error("Redis connection lost: %s  — retrying in 5s", exc)
            await asyncio.sleep(5)
            r = _get_redis()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as exc:
            logger.exception("Unexpected error: %s", exc)
            await asyncio.sleep(1)

    # Cleanup
    if _pg_pool:
        await _pg_pool.close()
    if _mqtt_client:
        _mqtt_client.loop_stop()
        _mqtt_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
