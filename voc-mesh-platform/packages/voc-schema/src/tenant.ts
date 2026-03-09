import { z } from "zod";

export const TenantTier = z.enum([
  "AGRO_BASIC",
  "FORESTRY_BASIC",
  "AGRO_ENTERPRISE",
]);
export type TenantTier = z.infer<typeof TenantTier>;

export const TenantSchema = z.object({
  id: z.string().uuid(),
  slug: z.string(),
  tier: TenantTier,
  billing_usd_per_sensor: z.number(),
  max_sensors: z.number(),
  max_parcelas: z.number(),
  created_at: z.string().datetime(),
  active: z.boolean(),
});
export type Tenant = z.infer<typeof TenantSchema>;

export const CreateTenantSchema = z.object({
  name: z.string(),
  slug: z.string(),
  tier: TenantTier,
  contact_email: z.string().email(),
  billing_plan: z.string(),
});
export type CreateTenant = z.infer<typeof CreateTenantSchema>;

export const FeatureFlagSchema = z.object({
  id: z.string().uuid(),
  tenant_id: z.string().uuid(),
  flag_name: z.string(),
  enabled: z.boolean(),
  config: z.record(z.unknown()),
});
export type FeatureFlag = z.infer<typeof FeatureFlagSchema>;

export const TIER_TEMPLATES = {
  AGRO_BASIC: {
    crop_stress_detection: true,
    bloom_prediction: true,
    pest_detection: true,
    carbon_sequestration: true,
    crop_metabolism_monitor: true,
    fire_humidity_detection: true,
    aerosol_organic_tracking: true,
    pollen_detection: false,
    satellite_fusion: false,
    api_access: false,
    billing_usd: 9,
    max_sensors: 50,
    max_parcelas: 10,
  },
  FORESTRY_BASIC: {
    crop_stress_detection: true,
    bloom_prediction: false,
    pest_detection: true,
    carbon_sequestration: true,
    crop_metabolism_monitor: false,
    fire_humidity_detection: true,
    aerosol_organic_tracking: true,
    pollen_detection: false,
    satellite_fusion: false,
    api_access: false,
    billing_usd: 12,
    max_sensors: 100,
    max_parcelas: 20,
  },
  AGRO_ENTERPRISE: {
    crop_stress_detection: true,
    bloom_prediction: true,
    pest_detection: true,
    carbon_sequestration: true,
    crop_metabolism_monitor: true,
    fire_humidity_detection: true,
    aerosol_organic_tracking: true,
    pollen_detection: true,
    satellite_fusion: true,
    api_access: true,
    billing_usd: 49,
    max_sensors: 10000,
    max_parcelas: 500,
  },
} as const;
