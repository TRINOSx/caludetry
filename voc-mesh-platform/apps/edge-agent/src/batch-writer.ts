import type { Pool } from "pg";
import type Redis from "ioredis";
import { Level } from "level";
import pino from "pino";
import type { ProcessedMessage } from "./mqtt-handler.js";

const logger = pino({ name: "batch-writer" });

const FLUSH_INTERVAL_MS = 500;
const MAX_BATCH_SIZE = 100;
const MAX_BACKOFF_MS = 16_000;
const INITIAL_BACKOFF_MS = 1_000;

let buffer: ProcessedMessage[] = [];
let flushTimer: ReturnType<typeof setInterval> | null = null;
let dbPool: Pool | null = null;
let redisClient: Redis | null = null;
let levelDb: Level<string, string> | null = null;
let currentBackoffMs = INITIAL_BACKOFF_MS;
let dbAvailable = true;
let draining = false;

/**
 * Initialize the batch writer with database and Redis connections.
 */
export async function initBatchWriter(
  db: Pool,
  redis: Redis,
  levelDbPath: string = "./data/edge-buffer"
): Promise<void> {
  dbPool = db;
  redisClient = redis;
  levelDb = new Level(levelDbPath, { valueEncoding: "json" });
  await levelDb.open();

  // Start periodic flush
  flushTimer = setInterval(() => {
    flushBuffer().catch((err) => {
      logger.error({ err }, "Flush buffer error");
    });
  }, FLUSH_INTERVAL_MS);

  logger.info("Batch writer initialized");
}

/**
 * Add a processed message to the in-memory batch buffer.
 * Triggers a flush if the buffer reaches MAX_BATCH_SIZE.
 */
export function addToBatch(message: ProcessedMessage): void {
  buffer.push(message);

  if (buffer.length >= MAX_BATCH_SIZE) {
    flushBuffer().catch((err) => {
      logger.error({ err }, "Flush buffer error on max batch size");
    });
  }
}

/**
 * Flush the in-memory buffer to TimescaleDB.
 * On failure, persist to LevelDB for later retry.
 */
async function flushBuffer(): Promise<void> {
  if (buffer.length === 0) {
    return;
  }

  // Swap the buffer so new messages accumulate in a fresh array
  const batch = buffer;
  buffer = [];

  if (dbAvailable && dbPool) {
    try {
      await writeBatchToDb(batch);
      currentBackoffMs = INITIAL_BACKOFF_MS;

      // After successful write, try draining LevelDB backlog
      if (!draining) {
        drainLevelDb().catch((err) => {
          logger.error({ err }, "Error draining LevelDB backlog");
        });
      }
    } catch (err) {
      logger.error({ err }, "Failed to write batch to DB, buffering to LevelDB");
      dbAvailable = false;
      await bufferToLevelDb(batch);
      scheduleReconnect();
    }
  } else {
    await bufferToLevelDb(batch);
  }
}

/**
 * Write a batch of processed messages to TimescaleDB using a multi-row INSERT.
 * Also push events to the Redis inference queue.
 */
async function writeBatchToDb(batch: ProcessedMessage[]): Promise<void> {
  if (!dbPool || !redisClient) {
    throw new Error("Database pool or Redis client not initialized");
  }

  const client = await dbPool.connect();
  try {
    await client.query("BEGIN");

    // Build parameterized multi-row INSERT
    const values: unknown[] = [];
    const placeholders: string[] = [];
    let paramIndex = 1;

    for (const msg of batch) {
      for (const reading of msg.calibrated_readings) {
        placeholders.push(
          `($${paramIndex}, $${paramIndex + 1}, $${paramIndex + 2}, $${paramIndex + 3}, $${paramIndex + 4}, $${paramIndex + 5}, $${paramIndex + 6}, $${paramIndex + 7}, $${paramIndex + 8}, $${paramIndex + 9}, $${paramIndex + 10}, $${paramIndex + 11})`
        );
        values.push(
          new Date(msg.timestamp_ms).toISOString(), // time
          msg.tenant_id,
          msg.hardware_id,
          reading.compound,
          reading.raw_adc,
          reading.corrected_adc,
          reading.value_ppm,
          reading.corrected_ppm,
          msg.temperature_c,
          msg.humidity_pct,
          msg.pm25,
          msg.pm10
        );
        paramIndex += 12;
      }
    }

    if (placeholders.length > 0) {
      const sql = `
        INSERT INTO sensor_readings (
          time, tenant_id, hardware_id, compound,
          raw_adc, corrected_adc, value_ppm, corrected_ppm,
          temperature_c, humidity_pct, pm25, pm10
        ) VALUES ${placeholders.join(", ")}
      `;
      await client.query(sql, values);
    }

    await client.query("COMMIT");

    // Push processed events to Redis inference queue
    const pipeline = redisClient.pipeline();
    for (const msg of batch) {
      const event = JSON.stringify({
        parcela_id: msg.parcela_id,
        tenant_id: msg.tenant_id,
        readings: msg.calibrated_readings,
        timestamp: msg.timestamp_ms,
      });
      pipeline.lpush("voc:inference:queue", event);
    }
    await pipeline.exec();

    logger.info(
      { batchSize: batch.length, readingCount: placeholders.length },
      "Batch flushed to DB and queued for inference"
    );
  } catch (err) {
    await client.query("ROLLBACK");
    throw err;
  } finally {
    client.release();
  }
}

/**
 * Buffer messages to LevelDB when the primary DB is unavailable.
 */
async function bufferToLevelDb(batch: ProcessedMessage[]): Promise<void> {
  if (!levelDb) {
    logger.error("LevelDB not initialized, dropping messages");
    return;
  }

  const ops = batch.map((msg, i) => ({
    type: "put" as const,
    key: `${Date.now()}-${i}-${msg.hardware_id}`,
    value: JSON.stringify(msg),
  }));

  await levelDb.batch(ops);
  logger.warn(
    { count: batch.length },
    "Buffered messages to LevelDB"
  );
}

/**
 * Schedule a DB reconnection attempt with exponential backoff.
 */
function scheduleReconnect(): void {
  const delay = currentBackoffMs;
  currentBackoffMs = Math.min(currentBackoffMs * 2, MAX_BACKOFF_MS);

  logger.info({ delay }, "Scheduling DB reconnect attempt");

  setTimeout(async () => {
    if (!dbPool) return;

    try {
      const client = await dbPool.connect();
      await client.query("SELECT 1");
      client.release();

      dbAvailable = true;
      currentBackoffMs = INITIAL_BACKOFF_MS;
      logger.info("DB connection restored");

      // Drain LevelDB backlog
      drainLevelDb().catch((err) => {
        logger.error({ err }, "Error draining LevelDB after reconnect");
      });
    } catch {
      logger.warn("DB still unavailable, will retry");
      scheduleReconnect();
    }
  }, delay);
}

/**
 * Drain buffered messages from LevelDB back to the primary DB.
 */
async function drainLevelDb(): Promise<void> {
  if (!levelDb || !dbPool || !dbAvailable || draining) {
    return;
  }

  draining = true;
  logger.info("Starting LevelDB drain");

  try {
    const batchToWrite: ProcessedMessage[] = [];
    const keysToDelete: string[] = [];

    for await (const [key, value] of levelDb.iterator()) {
      const msg = JSON.parse(value) as ProcessedMessage;
      batchToWrite.push(msg);
      keysToDelete.push(key);

      if (batchToWrite.length >= MAX_BATCH_SIZE) {
        await writeBatchToDb(batchToWrite);
        await levelDb.batch(
          keysToDelete.map((k) => ({ type: "del" as const, key: k }))
        );
        batchToWrite.length = 0;
        keysToDelete.length = 0;
      }
    }

    // Flush remaining
    if (batchToWrite.length > 0) {
      await writeBatchToDb(batchToWrite);
      await levelDb.batch(
        keysToDelete.map((k) => ({ type: "del" as const, key: k }))
      );
    }

    logger.info("LevelDB drain complete");
  } catch (err) {
    logger.error({ err }, "Error during LevelDB drain, will retry later");
    dbAvailable = false;
    scheduleReconnect();
  } finally {
    draining = false;
  }
}

/**
 * Gracefully shut down the batch writer.
 * Flushes remaining buffer and closes LevelDB.
 */
export async function shutdownBatchWriter(): Promise<void> {
  if (flushTimer) {
    clearInterval(flushTimer);
    flushTimer = null;
  }

  // Final flush
  if (buffer.length > 0) {
    logger.info({ remaining: buffer.length }, "Flushing remaining buffer on shutdown");
    try {
      await flushBuffer();
    } catch (err) {
      logger.error({ err }, "Error during shutdown flush");
    }
  }

  if (levelDb) {
    await levelDb.close();
    levelDb = null;
  }

  logger.info("Batch writer shut down");
}
