import { z } from "zod";

export const SensorType = z.enum(["ENOSE", "GROUND", "ATMOSPHERE"]);
export type SensorType = z.infer<typeof SensorType>;

export const SensorSchema = z.object({
  id: z.string().uuid(),
  tenant_id: z.string().uuid(),
  parcela_id: z.string().uuid(),
  hardware_id: z.string(),
  sensor_type: SensorType,
  lat: z.number(),
  lng: z.number(),
  active: z.boolean(),
  last_seen: z.string().optional(),
  battery_pct: z.number().optional(),
  signal_rssi: z.number().optional(),
});
export type Sensor = z.infer<typeof SensorSchema>;

export const VOCReadingSchema = z.object({
  time: z.string(),
  sensor_id: z.string().uuid(),
  tenant_id: z.string().uuid(),
  compound: z.string(),
  value_ppm: z.number(),
  raw_adc: z.number(),
  temperature_c: z.number(),
  humidity_pct: z.number(),
});
export type VOCReading = z.infer<typeof VOCReadingSchema>;

export const SensorMessageSchema = z.object({
  hardware_id: z.string(),
  timestamp_ms: z.number(),
  temperature_c: z.number(),
  humidity_pct: z.number(),
  readings: z.array(
    z.object({
      compound: z.string(),
      value_ppm: z.number(),
      raw_adc: z.number(),
    })
  ),
  pm25: z.number(),
  pm10: z.number(),
});
export type SensorMessage = z.infer<typeof SensorMessageSchema>;
