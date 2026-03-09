import { z } from "zod";

export const ParcelaSchema = z.object({
  id: z.string().uuid(),
  tenant_id: z.string().uuid(),
  name: z.string(),
  crop_type: z.string(),
  area_km2: z.number(),
  geojson: z.record(z.any()),
});
export type Parcela = z.infer<typeof ParcelaSchema>;
