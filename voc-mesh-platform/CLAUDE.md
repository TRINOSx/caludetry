# VOC Mesh Platform — Claude Code Project Memory

## Project Overview
Multi-tenant SaaS platform for VOC-mesh agrotechnology. Ingests data from distributed eNose sensor arrays (ESP32 + MEMS + TGS + PID 10.6eV), routes through tenant-isolated pipeline, runs ML inference (stress, pest, bloom, carbon), and renders real-time agricultural dashboard.

## Tech Stack
- **Backend**: FastAPI (Python 3.12) + SQLAlchemy async + Pydantic v2
- **Database**: TimescaleDB (PostgreSQL 16) with hypertables + RLS
- **Message Broker**: Eclipse Mosquitto MQTT v2
- **Cache/Queue**: Redis 7 (feature flag cache + ML inference queue)
- **Frontend**: React 18 + Vite + TypeScript + Tailwind CSS + Chart.js + Leaflet
- **Edge**: Node.js MQTT bridge + LevelDB offline buffer
- **Firmware**: ESP32 Arduino/PlatformIO (ADS1115 + SHT31 + SGP40 + SCD40)
- **ML**: scikit-learn + ONNX Runtime (5 models: stress, bloom, pest, fire, carbon)
- **AI Insights**: Anthropic Claude API (claude-sonnet-4-6)
- **Deployment**: Docker Compose + Nginx + GitHub Actions

## Architecture Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Tenant isolation | Row-Level Security (RLS) | Single DB, simpler ops, PostgreSQL native. Schema isolation adds DDL complexity per tenant |
| Time-series DB | TimescaleDB over InfluxDB | Full SQL compatibility, JSONB support, RLS works natively, strong ecosystem |
| Sensor transport | MQTT over WebSocket | Battery-efficient for ESP32, QoS levels, offline buffering, proven IoT standard |
| ML inference | Redis queue + ONNX | Decoupled from API, horizontally scalable workers, fast inference |
| Frontend state | Zustand over Redux | Simpler API, less boilerplate, TypeScript-native |

## Tenant Tiers & Feature Flags
```
AGRO_BASIC ($9/sensor/month, max 50 sensors, 10 parcelas):
  crop_stress_detection, bloom_prediction, pest_detection,
  carbon_sequestration, crop_metabolism_monitor,
  fire_humidity_detection, aerosol_organic_tracking

FORESTRY_BASIC ($5/sensor/month, max 100 sensors, 20 parcelas):
  fire_humidity_detection, bloom_detection, pest_detection,
  carbon_sequestration

AGRO_ENTERPRISE ($25/sensor/month, unlimited):
  ALL features + api_access + white_label + custom_ml_models
```

## Database Patterns
- **ALWAYS** filter by `tenant_id` in every query
- **NEVER** query without tenant scope (RLS is defense-in-depth, not sole protection)
- Use `SET LOCAL app.tenant_id = '{uuid}'` at start of each DB session for RLS
- Hypertables: `voc_readings` (1-day chunks), `ml_predictions` (1-day chunks)
- All IDs are UUID v4

## VOC Compound List (50 Key Agricultural Biomarkers)
```
Stress: ethylene, ethanol, acetaldehyde, hexanal, nonanal, decanal, H2S, methanol
Defense: methyl_salicylate, methyl_jasmonate, cis-3-hexenal, trans-2-hexenal,
         beta-caryophyllene, DMNT, TMTT, farnesene, ocimene, indole
Terpenes: isoprene, alpha-pinene, beta-pinene, limonene, myrcene
Flowering: linalool, geraniol
Atmosphere: CO, CO2, NO2, SO2, O3, TVOC, VOC, PM2.5, PM10
Industrial: benzene, toluene, xylene, styrene, butadiene, formaldehyde
Soil Gas: methane, ammonia, H2, carbon_disulfide, dimethyl_disulfide,
          acetic_acid, formic_acid, trimethylamine, propane
Indices: SGP40_index
```

## Sensor Calibration Equations
```
Temperature compensation:
  value_corrected = raw_adc × (a × temp_c + b)
  where a = -0.012501, b = 1.35347167

PPM conversion:
  ppm = a × (1 - b × value_corrected) + c
  where a = 2.92395047, b = 0.02952922, c = 0.43941621
```

## MQTT Topic Convention
```
Inbound:  voc/{tenant_slug}/{sensor_hardware_id}/raw
Outbound: voc/{tenant_slug}/{parcela_id}/predictions
Commands: voc/{tenant_slug}/{sensor_hardware_id}/commands
```

## ML Model Contracts
```
Input: 128-dim feature vector (50 compounds × {mean, max, delta} + env context)

stress_model  → stress_pct: float (0-100)
bloom_model   → bloom_probability: float (0-1)
pest_model    → {detected: bool, zone_type: str, confidence: float}
fire_model    → {alert: bool, smoke_detected: bool, humidity_critical: bool}
carbon_model  → carbon_index: float (0-100)
```

## API Versioning
- **v1**: Stable, production
- **v2**: In development (satellite fusion, custom ML models)
- All endpoints prefixed: `/api/v1/`

## Commands
```bash
# Development
pnpm dev                    # Start all services in dev mode
pnpm build                  # Build all packages
pnpm test                   # Run all tests
pnpm test:integration       # Integration tests (requires DB)
pnpm test:e2e               # End-to-end tests

# Database
pnpm db:migrate             # Run Alembic migrations
pnpm db:rollback            # Rollback one migration

# Docker
docker compose up -d        # Start full stack
docker compose down          # Stop all
docker compose build         # Rebuild images

# ML
cd packages/ml-pipeline && python train.py  # Train all models
```

## Forbidden Patterns
- **NEVER** store JWT in localStorage (use memory + httpOnly refresh cookie)
- **NEVER** query database without tenant_id filter
- **NEVER** skip RLS policies
- **NEVER** expose raw database errors to client
- **NEVER** hardcode secrets (use environment variables)
- **NEVER** commit .env files
- **NEVER** use `SELECT *` — always specify columns
- **NEVER** run ML inference in the API request cycle (use Redis queue)

## Current Sprint Status
- [x] Phase 0: Project bootstrap (monorepo, env schema)
- [x] Phase 1: Multi-tenant core (DB schema, RLS, tenant provisioning)
- [x] Phase 2: Edge agent (MQTT bridge, ESP32 firmware)
- [x] Phase 3: ML pipeline (5 models, feature engine, worker)
- [x] Phase 4: Dashboard (React shell, charts, sensor map)
- [x] Phase 5: Billing engine
- [x] Phase 6: Deployment (Docker, Nginx, CI/CD)

## Next Priorities
- [ ] Satellite fusion integration (Sentinel-2, Landsat)
- [ ] AlphaEarth geospatial embedding integration
- [ ] Custom ML model upload for AGRO_ENTERPRISE
- [ ] Mobile app (React Native)
- [ ] Webhook notifications (Slack, Teams)
