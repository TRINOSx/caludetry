import { z } from "zod";
import type { Pool } from "pg";
import type Redis from "ioredis";
import pino from "pino";
import { calibrateReadings, type CalibratedReading } from "./calibration.js";
import { addToBatch } from "./batch-writer.js";

const logger = pino({ name: "mqtt-handler" });

const ReadingSchema = z.object({
  compound: z.string(),
  value_ppm: z.number(),
  raw_adc: z.number(),
});

export const SensorMessageSchema = z.object({
  hardware_id: z.string(),
  timestamp_ms: z.number(),
  temperature_c: z.number(),
  humidity_pct: z.number(),
  readings: z.array(ReadingSchema),
  pm25: z.number().optional(),
  pm10: z.number().optional(),
});

export type SensorMessage = z.infer<typeof SensorMessageSchema>;

export interface ProcessedMessage {
  tenant_id: string;
  tenant_slug: string;
  hardware_id: string;
  timestamp_ms: number;
  temperature_c: number;
  humidity_pct: number;
  calibrated_readings: CalibratedReading[];
  pm25: number | null;
  pm10: number | null;
  parcela_id: string | null;
}

const TENANT_CACHE_TTL_SECONDS = 300; // 5 minutes

/**
 * Parse an MQTT topic of the form voc/{tenant_slug}/{hardware_id}/raw
 * and return the extracted tenant_slug and hardware_id.
 */
export function parseTopic(topic: string): {
  tenant_slug: string;
  hardware_id: string;
} | null {
  const parts = topic.split("/");
  if (parts.length !== 4 || parts[0] !== "voc" || parts[3] !== "raw") {
    return null;
  }
  return { tenant_slug: parts[1], hardware_id: parts[2] };
}

/**
 * Look up tenant_id from Redis cache first, falling back to PostgreSQL.
 * Cache results in Redis with a 5-minute TTL.
 */
async function resolveTenantId(
  tenantSlug: string,
  redis: Redis,
  db: Pool
): Promise<string | null> {
  const cacheKey = `tenant:slug:${tenantSlug}`;

  // Try Redis cache first
  const cached = await redis.get(cacheKey);
  if (cached) {
    return cached;
  }

  // Fall back to DB
  const result = await db.query(
    "SELECT id FROM tenants WHERE slug = $1 LIMIT 1",
    [tenantSlug]
  );

  if (result.rows.length === 0) {
    logger.warn({ tenantSlug }, "Tenant not found in database");
    return null;
  }

  const tenantId = result.rows[0].id as string;

  // Cache the result
  await redis.set(cacheKey, tenantId, "EX", TENANT_CACHE_TTL_SECONDS);

  return tenantId;
}

/**
 * Look up parcela_id for a given hardware_id and tenant_id.
 */
async function resolveParcelaId(
  hardwareId: string,
  tenantId: string,
  redis: Redis,
  db: Pool
): Promise<string | null> {
  const cacheKey = `sensor:parcela:${tenantId}:${hardwareId}`;

  const cached = await redis.get(cacheKey);
  if (cached) {
    return cached;
  }

  const result = await db.query(
    "SELECT parcela_id FROM sensors WHERE hardware_id = $1 AND tenant_id = $2 LIMIT 1",
    [hardwareId, tenantId]
  );

  if (result.rows.length === 0) {
    return null;
  }

  const parcelaId = result.rows[0].parcela_id as string;
  await redis.set(cacheKey, parcelaId, "EX", TENANT_CACHE_TTL_SECONDS);
  return parcelaId;
}

/**
 * Handle an incoming MQTT message on the voc/+/+/raw topic.
 */
export async function handleMessage(
  topic: string,
  payload: Buffer,
  redis: Redis,
  db: Pool
): Promise<void> {
  const startMs = Date.now();

  // Parse topic
  const topicParts = parseTopic(topic);
  if (!topicParts) {
    logger.warn({ topic }, "Ignoring message with unexpected topic format");
    return;
  }

  const { tenant_slug, hardware_id } = topicParts;

  // Parse JSON payload
  let rawPayload: unknown;
  try {
    rawPayload = JSON.parse(payload.toString("utf-8"));
  } catch {
    logger.error({ topic }, "Failed to parse MQTT payload as JSON");
    return;
  }

  // Validate with Zod
  const parseResult = SensorMessageSchema.safeParse(rawPayload);
  if (!parseResult.success) {
    logger.error(
      { topic, errors: parseResult.error.issues },
      "Payload validation failed"
    );
    return;
  }

  const message = parseResult.data;

  // Verify hardware_id matches topic
  if (message.hardware_id !== hardware_id) {
    logger.warn(
      { topic, payloadHwId: message.hardware_id, topicHwId: hardware_id },
      "hardware_id mismatch between topic and payload"
    );
  }

  // Resolve tenant_id
  const tenantId = await resolveTenantId(tenant_slug, redis, db);
  if (!tenantId) {
    logger.error({ tenant_slug }, "Cannot process message: tenant not found");
    return;
  }

  // Resolve parcela_id
  const parcelaId = await resolveParcelaId(hardware_id, tenantId, redis, db);

  // Apply calibration corrections
  const calibratedReadings = calibrateReadings(
    message.readings,
    message.temperature_c
  );

  const processed: ProcessedMessage = {
    tenant_id: tenantId,
    tenant_slug,
    hardware_id,
    timestamp_ms: message.timestamp_ms,
    temperature_c: message.temperature_c,
    humidity_pct: message.humidity_pct,
    calibrated_readings: calibratedReadings,
    pm25: message.pm25 ?? null,
    pm10: message.pm10 ?? null,
    parcela_id: parcelaId,
  };

  // Add to batch buffer
  addToBatch(processed);

  const latencyMs = Date.now() - startMs;
  logger.info(
    {
      tenant_slug,
      sensor_id: hardware_id,
      compound_count: calibratedReadings.length,
      latency_ms: latencyMs,
    },
    "Processed sensor message"
  );
}
