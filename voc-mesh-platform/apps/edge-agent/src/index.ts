import mqtt from "mqtt";
import Redis from "ioredis";
import pg from "pg";
import pino from "pino";
import { handleMessage } from "./mqtt-handler.js";
import { initBatchWriter, shutdownBatchWriter } from "./batch-writer.js";

const logger = pino({ name: "edge-agent" });

const MQTT_BROKER_URL = process.env.MQTT_BROKER_URL ?? "mqtt://localhost:1883";
const MQTT_USERNAME = process.env.MQTT_USERNAME ?? "";
const MQTT_PASSWORD = process.env.MQTT_PASSWORD ?? "";
const REDIS_URL = process.env.REDIS_URL ?? "redis://localhost:6379";
const DATABASE_URL =
  process.env.DATABASE_URL ??
  "postgresql://voc:voc@localhost:5432/voc_mesh";
const LEVELDB_PATH = process.env.LEVELDB_PATH ?? "./data/edge-buffer";
const MQTT_TOPIC = "voc/+/+/raw";

async function main(): Promise<void> {
  logger.info("Starting VOC Mesh Edge Agent");

  // Connect to Redis
  const redis = new Redis(REDIS_URL, {
    maxRetriesPerRequest: 3,
    retryStrategy(times: number) {
      const delay = Math.min(times * 500, 5000);
      return delay;
    },
  });

  redis.on("connect", () => logger.info("Connected to Redis"));
  redis.on("error", (err) => logger.error({ err }, "Redis error"));

  // Connect to PostgreSQL
  const dbPool = new pg.Pool({
    connectionString: DATABASE_URL,
    max: 10,
    idleTimeoutMillis: 30_000,
    connectionTimeoutMillis: 5_000,
  });

  dbPool.on("error", (err) => {
    logger.error({ err }, "Unexpected PostgreSQL pool error");
  });

  // Verify DB connection
  try {
    const client = await dbPool.connect();
    await client.query("SELECT 1");
    client.release();
    logger.info("Connected to PostgreSQL");
  } catch (err) {
    logger.error({ err }, "Failed to connect to PostgreSQL on startup");
  }

  // Initialize batch writer
  await initBatchWriter(dbPool, redis, LEVELDB_PATH);

  // Connect to MQTT broker
  const mqttClient = mqtt.connect(MQTT_BROKER_URL, {
    username: MQTT_USERNAME || undefined,
    password: MQTT_PASSWORD || undefined,
    clientId: `edge-agent-${process.pid}`,
    clean: true,
    reconnectPeriod: 5000,
    connectTimeout: 30_000,
  });

  mqttClient.on("connect", () => {
    logger.info({ broker: MQTT_BROKER_URL }, "Connected to MQTT broker");

    mqttClient.subscribe(MQTT_TOPIC, { qos: 1 }, (err, granted) => {
      if (err) {
        logger.error({ err }, "Failed to subscribe to MQTT topic");
        return;
      }
      logger.info(
        { topic: MQTT_TOPIC, granted },
        "Subscribed to MQTT topic"
      );
    });
  });

  mqttClient.on("error", (err) => {
    logger.error({ err }, "MQTT client error");
  });

  mqttClient.on("reconnect", () => {
    logger.info("Reconnecting to MQTT broker");
  });

  mqttClient.on("offline", () => {
    logger.warn("MQTT client offline");
  });

  mqttClient.on("message", (topic: string, payload: Buffer) => {
    handleMessage(topic, payload, redis, dbPool).catch((err) => {
      logger.error({ err, topic }, "Error handling MQTT message");
    });
  });

  // Graceful shutdown
  const shutdown = async (signal: string): Promise<void> => {
    logger.info({ signal }, "Received shutdown signal");

    mqttClient.end(false, {}, () => {
      logger.info("MQTT client disconnected");
    });

    await shutdownBatchWriter();

    await dbPool.end();
    logger.info("PostgreSQL pool closed");

    redis.disconnect();
    logger.info("Redis disconnected");

    logger.info("Edge agent shut down cleanly");
    process.exit(0);
  };

  process.on("SIGINT", () => shutdown("SIGINT"));
  process.on("SIGTERM", () => shutdown("SIGTERM"));

  process.on("uncaughtException", (err) => {
    logger.fatal({ err }, "Uncaught exception");
    shutdown("uncaughtException").catch(() => process.exit(1));
  });

  process.on("unhandledRejection", (reason) => {
    logger.fatal({ reason }, "Unhandled rejection");
  });

  logger.info("Edge agent running, waiting for sensor messages");
}

main().catch((err) => {
  logger.fatal({ err }, "Fatal error starting edge agent");
  process.exit(1);
});
