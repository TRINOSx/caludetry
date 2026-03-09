import { z } from "zod";
import { TenantTier } from "./tenant";

export const BillingEventSchema = z.object({
  id: z.string().uuid(),
  tenant_id: z.string().uuid(),
  period_start: z.string().datetime(),
  period_end: z.string().datetime(),
  sensor_count: z.number(),
  km2_covered: z.number(),
  amount_usd: z.number(),
  tier: TenantTier,
  paid: z.boolean(),
});
export type BillingEvent = z.infer<typeof BillingEventSchema>;
