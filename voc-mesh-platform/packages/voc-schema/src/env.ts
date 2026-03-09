import { z } from "zod";

export const EnvSchema = z.object({
  DATABASE_URL: z.string().url(),
  MQTT_BROKER_URL: z.string(),
  MQTT_USERNAME: z.string(),
  MQTT_PASSWORD: z.string(),
  JWT_SECRET: z.string().min(32),
  JWT_EXPIRY: z.coerce.number(),
  TENANT_ISOLATION_MODE: z.enum(["row_level", "schema_level"]),
  ANTHROPIC_API_KEY: z.string().startsWith("sk-ant-"),
  REDIS_URL: z.string(),
  BILLING_WEBHOOK_URL: z.string().url(),
  ML_MODEL_PATH: z.string(),
});

export type Env = z.infer<typeof EnvSchema>;
