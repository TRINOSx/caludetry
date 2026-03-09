import { z } from "zod";

export const MLPredictionSchema = z.object({
  time: z.string(),
  parcela_id: z.string().uuid(),
  tenant_id: z.string().uuid(),
  stress_pct: z.number().min(0).max(100),
  bloom_pct: z.number().min(0).max(1),
  pest_zone_detected: z.boolean(),
  pest_type: z.string().optional(),
  carbon_index: z.number(),
  fire_alert: z.boolean(),
  model_version: z.string(),
});
export type MLPrediction = z.infer<typeof MLPredictionSchema>;
