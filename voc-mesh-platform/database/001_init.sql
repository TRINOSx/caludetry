-- ================================
-- VOC Mesh Platform - TimescaleDB Schema
-- Multi-Tenant with Row-Level Security
-- ================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ================================
-- 1. TENANTS
-- ================================
CREATE TABLE tenants (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug            VARCHAR(63) UNIQUE NOT NULL,
    name            VARCHAR(255) NOT NULL,
    tier            VARCHAR(30) NOT NULL CHECK (tier IN ('AGRO_BASIC', 'FORESTRY_BASIC', 'AGRO_ENTERPRISE')),
    contact_email   VARCHAR(255),
    billing_usd_per_sensor DECIMAL(10,2) NOT NULL DEFAULT 9.00,
    max_sensors     INTEGER NOT NULL DEFAULT 50,
    max_parcelas    INTEGER NOT NULL DEFAULT 10,
    jwt_secret      VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    active          BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_tenants_slug ON tenants (slug);

-- ================================
-- 2. FEATURE FLAGS
-- ================================
CREATE TABLE feature_flags (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    flag_name   VARCHAR(100) NOT NULL,
    enabled     BOOLEAN NOT NULL DEFAULT FALSE,
    config      JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, flag_name)
);

CREATE INDEX idx_feature_flags_tenant ON feature_flags (tenant_id);

-- ================================
-- 3. PARCELAS
-- ================================
CREATE TABLE parcelas (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    crop_type   VARCHAR(100),
    area_km2    DECIMAL(12,4),
    geojson     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_parcelas_tenant ON parcelas (tenant_id);

-- ================================
-- 4. SENSORS
-- ================================
CREATE TABLE sensors (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    parcela_id      UUID REFERENCES parcelas(id) ON DELETE SET NULL,
    hardware_id     VARCHAR(50) UNIQUE NOT NULL,
    sensor_type     VARCHAR(20) NOT NULL CHECK (sensor_type IN ('ENOSE', 'GROUND', 'ATMOSPHERE')),
    lat             DECIMAL(10,7),
    lng             DECIMAL(10,7),
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    last_seen       TIMESTAMPTZ,
    battery_pct     DECIMAL(5,2),
    signal_rssi     INTEGER,
    firmware_version VARCHAR(50),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sensors_tenant ON sensors (tenant_id);
CREATE INDEX idx_sensors_parcela ON sensors (parcela_id);
CREATE INDEX idx_sensors_hardware ON sensors (hardware_id);

-- ================================
-- 5. VOC READINGS (TimescaleDB hypertable)
-- ================================
CREATE TABLE voc_readings (
    time            TIMESTAMPTZ NOT NULL,
    sensor_id       UUID NOT NULL,
    tenant_id       UUID NOT NULL,
    compound        VARCHAR(50) NOT NULL,
    value_ppm       DECIMAL(12,6),
    raw_adc         INTEGER,
    temperature_c   DECIMAL(6,2),
    humidity_pct    DECIMAL(6,2),
    pm25            DECIMAL(8,2),
    pm10            DECIMAL(8,2)
);

-- Convert to hypertable (uncomment when TimescaleDB is available)
-- SELECT create_hypertable('voc_readings', 'time', chunk_time_interval => INTERVAL '1 day');

CREATE INDEX idx_voc_readings_sensor_time ON voc_readings (sensor_id, time DESC);
CREATE INDEX idx_voc_readings_tenant_time ON voc_readings (tenant_id, time DESC);
CREATE INDEX idx_voc_readings_compound ON voc_readings (compound, time DESC);

-- ================================
-- 6. ML PREDICTIONS (TimescaleDB hypertable)
-- ================================
CREATE TABLE ml_predictions (
    time                TIMESTAMPTZ NOT NULL,
    parcela_id          UUID NOT NULL,
    tenant_id           UUID NOT NULL,
    stress_pct          DECIMAL(6,2),
    bloom_pct           DECIMAL(6,4),
    pest_zone_detected  BOOLEAN DEFAULT FALSE,
    pest_type           VARCHAR(50),
    pest_confidence     DECIMAL(6,4),
    carbon_index        DECIMAL(8,4),
    fire_alert          BOOLEAN DEFAULT FALSE,
    smoke_detected      BOOLEAN DEFAULT FALSE,
    humidity_critical   BOOLEAN DEFAULT FALSE,
    model_version       VARCHAR(50)
);

-- SELECT create_hypertable('ml_predictions', 'time', chunk_time_interval => INTERVAL '1 day');

CREATE INDEX idx_ml_predictions_parcela_time ON ml_predictions (parcela_id, time DESC);
CREATE INDEX idx_ml_predictions_tenant_time ON ml_predictions (tenant_id, time DESC);

-- ================================
-- 7. BILLING EVENTS
-- ================================
CREATE TABLE billing_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    sensor_count    INTEGER NOT NULL DEFAULT 0,
    km2_covered     DECIMAL(12,4) DEFAULT 0,
    readings_count  BIGINT DEFAULT 0,
    api_calls       INTEGER DEFAULT 0,
    amount_usd      DECIMAL(12,2) NOT NULL DEFAULT 0,
    tier            VARCHAR(30) NOT NULL,
    paid            BOOLEAN NOT NULL DEFAULT FALSE,
    invoice_url     VARCHAR(500),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_billing_tenant ON billing_events (tenant_id, period_start DESC);

-- ================================
-- 8. ALERTS
-- ================================
CREATE TABLE alerts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    parcela_id      UUID REFERENCES parcelas(id),
    sensor_id       UUID REFERENCES sensors(id),
    alert_type      VARCHAR(30) NOT NULL CHECK (alert_type IN ('warning', 'danger', 'info', 'critical')),
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    compound        VARCHAR(50),
    value           DECIMAL(12,6),
    threshold       DECIMAL(12,6),
    acknowledged    BOOLEAN NOT NULL DEFAULT FALSE,
    resolved        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ,
    resolved_at     TIMESTAMPTZ
);

CREATE INDEX idx_alerts_tenant ON alerts (tenant_id, created_at DESC);
CREATE INDEX idx_alerts_active ON alerts (tenant_id, acknowledged, resolved);

-- ================================
-- 9. INSIGHT LOG (Claude API)
-- ================================
CREATE TABLE insight_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    parcela_id      UUID REFERENCES parcelas(id),
    summary         TEXT,
    urgency_level   VARCHAR(20),
    recommended_actions JSONB,
    scientific_reasoning TEXT,
    model_used      VARCHAR(100),
    tokens_used     INTEGER,
    cached          BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_insights_tenant ON insight_logs (tenant_id, created_at DESC);

-- ================================
-- ROW-LEVEL SECURITY
-- ================================

-- Enable RLS on all tenant-scoped tables
ALTER TABLE feature_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE parcelas ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensors ENABLE ROW LEVEL SECURITY;
ALTER TABLE voc_readings ENABLE ROW LEVEL SECURITY;
ALTER TABLE ml_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE insight_logs ENABLE ROW LEVEL SECURITY;

-- Create application role
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'voc_app') THEN
        CREATE ROLE voc_app LOGIN;
    END IF;
END
$$;

-- RLS policies: app sets current_setting('app.tenant_id') per request
CREATE POLICY tenant_isolation_feature_flags ON feature_flags
    USING (tenant_id::text = current_setting('app.tenant_id', true));

CREATE POLICY tenant_isolation_parcelas ON parcelas
    USING (tenant_id::text = current_setting('app.tenant_id', true));

CREATE POLICY tenant_isolation_sensors ON sensors
    USING (tenant_id::text = current_setting('app.tenant_id', true));

CREATE POLICY tenant_isolation_voc_readings ON voc_readings
    USING (tenant_id::text = current_setting('app.tenant_id', true));

CREATE POLICY tenant_isolation_ml_predictions ON ml_predictions
    USING (tenant_id::text = current_setting('app.tenant_id', true));

CREATE POLICY tenant_isolation_billing ON billing_events
    USING (tenant_id::text = current_setting('app.tenant_id', true));

CREATE POLICY tenant_isolation_alerts ON alerts
    USING (tenant_id::text = current_setting('app.tenant_id', true));

CREATE POLICY tenant_isolation_insights ON insight_logs
    USING (tenant_id::text = current_setting('app.tenant_id', true));

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO voc_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO voc_app;
