-- ================================
-- VOC Field Intelligence - Database Schema
-- TimescaleDB (PostgreSQL) recommended
-- ================================

-- Enable TimescaleDB extension (if available)
-- CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ================================
-- Main sensor data table
-- ================================
CREATE TABLE IF NOT EXISTS sensor_data (
    time            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    parcel_id       TEXT NOT NULL,
    sensor_id       TEXT NOT NULL,

    -- Atmospheric gases (ppb)
    co2             FLOAT,
    nh3             FLOAT,
    methane         FLOAT,
    ethanol         FLOAT,
    tvoc            FLOAT,
    voc             FLOAT,
    hydrogen        FLOAT,
    carbon_monoxide FLOAT,
    formaldehyde    FLOAT,
    ozone           FLOAT,
    sulfur          FLOAT,
    no2             FLOAT,
    smoke           FLOAT,
    odor            FLOAT,
    spo40           FLOAT,

    -- Climate
    humidity        FLOAT,
    temperature     FLOAT,
    pressure        FLOAT,
    wind_speed      FLOAT,
    wind_direction  FLOAT,
    solar_radiation FLOAT,
    uv_index        FLOAT,
    precipitation   FLOAT,

    -- Soil
    soil_moisture   FLOAT,
    soil_temp       FLOAT,
    ph              FLOAT,
    conductivity    FLOAT,
    nitrogen        FLOAT,
    phosphorus      FLOAT,
    potassium       FLOAT,

    PRIMARY KEY (time, parcel_id, sensor_id)
);

-- Convert to hypertable (TimescaleDB)
-- SELECT create_hypertable('sensor_data', 'time', if_not_exists => TRUE);

-- ================================
-- VOC compound profile (300+ compounds)
-- ================================
CREATE TABLE IF NOT EXISTS voc_profile (
    time        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    parcel_id   TEXT NOT NULL,
    compound    TEXT NOT NULL,
    value       FLOAT NOT NULL,
    unit        TEXT DEFAULT 'ppb',

    PRIMARY KEY (time, parcel_id, compound)
);

-- SELECT create_hypertable('voc_profile', 'time', if_not_exists => TRUE);

-- ================================
-- Plant status (ML predictions stored)
-- ================================
CREATE TABLE IF NOT EXISTS plant_status (
    time            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    parcel_id       TEXT NOT NULL,
    stress          FLOAT,
    plagues         FLOAT,
    metabolism      FLOAT,
    flowering       FLOAT,
    nutrition       FLOAT,
    hydration       FLOAT,
    oxygen_generate FLOAT,
    co2_transform   FLOAT,
    model_version   TEXT,
    confidence      FLOAT,

    PRIMARY KEY (time, parcel_id)
);

-- SELECT create_hypertable('plant_status', 'time', if_not_exists => TRUE);

-- ================================
-- Alerts
-- ================================
CREATE TABLE IF NOT EXISTS alerts (
    id          SERIAL PRIMARY KEY,
    time        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    parcel_id   TEXT NOT NULL,
    sensor_id   TEXT,
    type        TEXT NOT NULL,  -- 'warning', 'danger', 'info'
    title       TEXT NOT NULL,
    description TEXT,
    compound    TEXT,
    value       FLOAT,
    threshold   FLOAT,
    acknowledged BOOLEAN DEFAULT FALSE,
    resolved    BOOLEAN DEFAULT FALSE
);

-- ================================
-- Parcels configuration
-- ================================
CREATE TABLE IF NOT EXISTS parcels (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    hacienda    TEXT,
    crop        TEXT,
    area_ha     FLOAT,
    lat         FLOAT,
    lon         FLOAT,
    altitude    FLOAT,
    soil_type   TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ================================
-- Sensor nodes configuration
-- ================================
CREATE TABLE IF NOT EXISTS sensor_nodes (
    id          TEXT PRIMARY KEY,
    parcel_id   TEXT REFERENCES parcels(id),
    type        TEXT NOT NULL,
    location    TEXT,
    lat         FLOAT,
    lon         FLOAT,
    status      TEXT DEFAULT 'offline',
    last_seen   TIMESTAMPTZ,
    firmware    TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ================================
-- AlphaEarth embeddings cache
-- ================================
CREATE TABLE IF NOT EXISTS alpha_earth_cache (
    lat         FLOAT NOT NULL,
    lon         FLOAT NOT NULL,
    date        DATE NOT NULL,
    embedding   FLOAT[] NOT NULL,
    ndvi        FLOAT,
    ndwi        FLOAT,
    evi         FLOAT,
    geo_score   FLOAT,
    soil_health FLOAT,
    climate_zone TEXT,
    soil_type   TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (lat, lon, date)
);

-- ================================
-- ML model predictions log
-- ================================
CREATE TABLE IF NOT EXISTS ml_predictions (
    id              SERIAL PRIMARY KEY,
    time            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    parcel_id       TEXT NOT NULL,
    model_name      TEXT NOT NULL,
    model_version   TEXT,
    horizon         TEXT,  -- '24h', '72h', '7d'
    input_features  JSONB,
    predictions     JSONB,
    confidence      FLOAT,
    actual_values   JSONB  -- filled later for model validation
);

-- ================================
-- Indexes
-- ================================
CREATE INDEX IF NOT EXISTS idx_sensor_parcel_time ON sensor_data (parcel_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_voc_parcel_time ON voc_profile (parcel_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_parcel ON alerts (parcel_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_plant_status_parcel ON plant_status (parcel_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_ml_predictions_parcel ON ml_predictions (parcel_id, time DESC);

-- ================================
-- Insert sample parcels
-- ================================
INSERT INTO parcels (id, name, hacienda, crop, area_ha, lat, lon, altitude, soil_type) VALUES
    ('P1', 'Parcela 1', 'Hacienda San Joaquin', 'Corn', 10.7, 20.6597, -103.3496, 1540, 'Vertisol'),
    ('P2', 'Parcela 2', 'Hacienda San Joaquin', 'Wheat', 8.3, 20.6610, -103.3480, 1535, 'Vertisol'),
    ('P3', 'Parcela 3', 'Hacienda San Joaquin', 'Soybean', 12.1, 20.6585, -103.3510, 1545, 'Luvisol'),
    ('P4', 'Parcela 4', 'Hacienda San Joaquin', 'Tomato', 5.5, 20.6575, -103.3470, 1530, 'Cambisol')
ON CONFLICT (id) DO NOTHING;

-- ================================
-- Insert sample sensor nodes
-- ================================
INSERT INTO sensor_nodes (id, parcel_id, type, location, status) VALUES
    ('VOC_NODE_1', 'P1', 'Bosch BME688', 'North', 'online'),
    ('VOC_NODE_2', 'P1', 'Bosch BME688', 'East', 'online'),
    ('VOC_NODE_3', 'P1', 'Bosch BME688', 'South', 'online'),
    ('VOC_NODE_4', 'P1', 'Bosch BME688', 'West', 'offline'),
    ('SOIL_NODE_1', 'P1', 'NPK Sensor', 'Center', 'online'),
    ('SOIL_NODE_2', 'P1', 'pH/EC Sensor', 'Center', 'online'),
    ('WEATHER_1', 'P1', 'Weather Station', 'Field Edge', 'online'),
    ('CAM_NODE_1', 'P1', 'RGB Camera', 'Tower', 'online')
ON CONFLICT (id) DO NOTHING;
