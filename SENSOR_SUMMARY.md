# LASEM VOC Mesh AgriTech — Resumen Técnico del Sistema de Sensores

## 1. Arquitectura General

```
ESP32 (6 sensores)  →  MQTT  →  Edge Agent (Node.js)  →  TimescaleDB  →  ML Worker  →  Dashboard
                                  ↑ calibración                          ↑ 5 modelos      ↑ React
                                  ↑ batch insert                         ↑ ONNX Runtime    ↑ Recharts
```

---

## 2. Hardware: Nodo ESP32

Cada nodo de campo integra **6 sensores** conectados por I2C y UART:

| Sensor     | Bus        | Medición                         | Precisión          |
|------------|------------|----------------------------------|---------------------|
| ADS1115    | I2C 0x48   | ADC 16-bit, 4 canales analógicos | 16-bit resolución  |
| → MiCS-4514 | Canal 0   | NO₂                              | ppb                |
| → MiCS-5524 | Canal 1   | CO / VOC                         | ppm                |
| → TGS2620  | Canal 2    | Etanol, solventes orgánicos      | ppm                |
| → TGS2600  | Canal 3    | Calidad general del aire         | ppm                |
| SHT31      | I2C 0x44   | Temperatura + Humedad            | ±0.2°C, ±2% RH    |
| SGP40      | I2C 0x59   | TVOC index (0-500)               | VOC index          |
| SCD40      | I2C 0x62   | CO₂ atmosférico                  | ±40 ppm            |
| PMS5003    | UART2      | PM2.5, PM10 (µg/m³)             | partículas         |

**Protocolo MQTT:** `voc/{tenant_slug}/{hardware_id}/raw`

**Payload JSON de ejemplo:**
```json
{
  "hardware_id": "AA:BB:CC:DD:EE:FF",
  "timestamp_ms": 1718488640000,
  "temperature_c": 25.3,
  "humidity_pct": 55.2,
  "readings": [
    {"compound": "NO2",    "value_ppm": 0.05, "raw_adc": 2048},
    {"compound": "CO",     "value_ppm": 1.2,  "raw_adc": 2096},
    {"compound": "C2H5OH", "value_ppm": 0.8,  "raw_adc": 1900},
    {"compound": "VOC",    "value_ppm": 3.5,  "raw_adc": 2200},
    {"compound": "TVOC",   "value_ppm": 145,  "raw_adc": 32567},
    {"compound": "CO2",    "value_ppm": 420,  "raw_adc": 420}
  ],
  "pm25": 12,
  "pm10": 25
}
```

---

## 3. Tipos de Sensor en Base de Datos

| Tipo          | Descripción                                | Ubicación típica       |
|---------------|--------------------------------------------|------------------------|
| **ENOSE**     | Nariz electrónica (array VOC especializado)| Canopy / entre plantas |
| **GROUND**    | Sensor de suelo (gases, respiración)       | A nivel de suelo       |
| **ATMOSPHERE**| Medición atmosférica sobre el dosel        | Sobre el cultivo       |

---

## 4. Compuestos VOC Monitoreados (50 biomarcadores)

### Indicadores de Estrés
etileno, etanol, acetaldehído, hexanal, nonanal, isopreno, cis-3-hexenal, ácido acético, ácido fórmico, metanol, acetona

### Respuesta de Defensa / Patógenos
metil salicilato (MeSA), metil jasmonato (MeJA), α-pineno, β-pineno, limoneno, mirceno, β-cariofileno, DMNT, TMTT, farneseno, ocimeno

### Indicadores de Floración
linalool, geraniol, indol

### Suelo / Atmósfera
CO₂, CO, H₂, H₂S, CH₄, NH₃, NO₂, SO₂

### Contaminantes Industriales
benceno, tolueno, xileno, estireno, formaldehído, butadieno, propano, butano

### Índices y Partículas
PM2.5, PM10, TVOC, VOC genérico, SGP40_index

---

## 5. Edge Agent — Calibración y Procesamiento

El agente de borde (Node.js) aplica corrección por temperatura antes de almacenar:

```
# Compensación por temperatura
corrected_adc = raw_adc × (-0.012501 × temperature_c + 1.35347167)

# Conversión a PPM
corrected_ppm = 2.92395047 × (1 - 0.02952922 × corrected_adc) + 0.43941621
```

**Flujo:** MQTT → Validación Zod → Resolución tenant (Redis cache) → Calibración → Batch INSERT a TimescaleDB

---

## 6. Pipeline de ML — 5 Modelos de Producción

### Vector de Características: 128 dimensiones

| Rango       | Contenido                                       |
|-------------|--------------------------------------------------|
| 0–149       | 50 compuestos × {media, máximo, delta}           |
| 150–154     | Contexto ambiental: PM2.5, PM10, CO₂, humedad, temp |
| 155–167     | Top 13 compuestos normalizados por temperatura   |
| Truncado a  | **128 dimensiones finales**                      |

---

### Modelo 1: Estrés del Cultivo (`STRESS_MODEL`)

| Propiedad     | Valor                                     |
|---------------|-------------------------------------------|
| Algoritmo     | RandomForestRegressor (200 árboles, depth=16) |
| Entrada       | Vector 128-dim                            |
| Salida        | `stress_pct` (0–100%)                     |
| Drivers clave | Etileno, metil jasmonato, humedad inversa |
| MAE objetivo  | < 3 puntos porcentuales                   |

---

### Modelo 2: Predicción de Floración (`BLOOM_MODEL`)

| Propiedad     | Valor                                     |
|---------------|-------------------------------------------|
| Algoritmo     | GradientBoostingClassifier (200, depth=6) |
| Entrada       | Vector 128-dim                            |
| Salida        | `bloom_probability` (0.0–1.0)            |
| Drivers clave | Limoneno, linalool, geraniol              |

---

### Modelo 3: Detección de Plagas (`PEST_MODEL`)

| Propiedad     | Valor                                     |
|---------------|-------------------------------------------|
| Algoritmo     | RandomForestClassifier (250, depth=14, balanced) |
| Entrada       | Vector 128-dim                            |
| Salida        | `detected` (bool), `zone_type`, `confidence` |

**Tipos de plaga detectados:**

| Tipo              | Señales VOC principales                    |
|-------------------|--------------------------------------------|
| **Fúngica**       | Metil salicilato elevado                   |
| **Bacteriana**    | Metil jasmonato + dimetil disulfuro        |
| **Insecto áfido** | Isopreno + α-pineno                        |
| **Insecto ácaro** | cis-3-Hexenal + DMNT                       |
| **Nematodo**      | Nonanal + disulfuro de carbono             |

---

### Modelo 4: Alerta de Incendio (`FIRE_MODEL`)

| Propiedad     | Valor                                     |
|---------------|-------------------------------------------|
| Algoritmo     | Híbrido: Reglas + RandomForest (150)      |
| Entrada       | Vector 128-dim + humedad                  |
| Salida        | `fire_alert`, `smoke_detected`, `humidity_critical` |

**Reglas de decisión:**
```
SI (CO > 1.5 ppm  Y  benceno > 1.2  Y  tolueno > 1.2) → smoke = True
SI (humedad < 30%) → humidity_critical = True
SI (smoke AND humidity_critical) → fire_alert = True
```

---

### Modelo 5: Índice de Carbono (`CARBON_MODEL`)

| Propiedad     | Valor                                     |
|---------------|-------------------------------------------|
| Algoritmo     | LinearRegression (128 + 6 features)       |
| Entrada       | 134 dimensiones (128 + 6 interacciones)   |
| Salida        | `carbon_index` (0–100)                    |

**Features de interacción adicionales:**
1. Proxy absorción CO₂ = −delta_CO₂ (negativo = absorción)
2. Proxy NDVI = isopreno + 0.5 × α-pineno
3. Respiración del suelo = metano + 0.3 × H₂S
4. Absorción × dosel
5. Nivel CO₂ medio (inverso)
6. Diversidad terpénica = |isopreno − α-pineno|

---

## 7. Sistema de Alertas

| Métrica           | Rango    | Nivel Alerta        | Trigger          |
|-------------------|----------|----------------------|------------------|
| Estrés            | 0–100%   | >70% = crítico       | ML predictions   |
| Floración         | 0–1      | >0.6 = alto          | ML predictions   |
| Confianza plaga   | 0–1      | >0.5 = detectada     | ML predictions   |
| Índice carbono    | 0–100    | Informativo          | ML predictions   |
| Alerta incendio   | bool     | True = **CRÍTICO**   | Reglas + ML      |
| Humedad crítica   | <30%     | Warning              | Fire model       |
| CO                | ppm      | >1.5 = alerta humo   | Fire model rule  |
| Benceno           | ppm      | >1.2 = alerta humo   | Fire model rule  |
| Tolueno           | ppm      | >1.2 = alerta humo   | Fire model rule  |

---

## 8. Tiers Multi-Tenant

| Tier                | Precio/sensor/mes | Max Sensores | Max Parcelas | Features                                     |
|---------------------|-------------------|-------------|-------------|----------------------------------------------|
| **AGRO_BASIC**      | $9 USD            | 50          | 10          | Estrés, floración, plagas, carbono, metabolismo, incendio |
| **FORESTRY_BASIC**  | $5 USD            | 100         | 20          | Incendio, floración, plagas, carbono         |
| **AGRO_ENTERPRISE** | $25 USD           | Ilimitado   | Ilimitado   | TODO + API access + white label              |

---

## 9. Diagrama de Flujo Completo

```
┌───────────────────────────┐
│      ESP32 Nodo Campo     │
│  ADS1115 · SHT31 · SGP40 │
│  SCD40 · PMS5003          │
│  WiFi + deep sleep        │
└───────────┬───────────────┘
            │ MQTT (voc/{tenant}/{hwid}/raw)
            ▼
┌───────────────────────────┐
│     Mosquitto MQTT        │
│  :1883 (TCP) :9001 (WS)  │
└───────────┬───────────────┘
            ▼
┌───────────────────────────┐     ┌─────────────────┐
│   Edge Agent (Node.js)    │────▶│   Redis Cache    │
│  Calibración + Validación │     │  Tenant lookup   │
│  Batch writer             │     │  Inference queue │
└───────────┬───────────────┘     └────────┬────────┘
            │ INSERT batch                  │
            ▼                               ▼
┌───────────────────────────┐     ┌──────────────────┐
│  TimescaleDB/PostgreSQL   │     │  ML Worker (Py)  │
│  ├─ tenants               │◀───│  Feature Engine  │
│  ├─ parcelas              │     │  128-dim vector  │
│  ├─ sensors               │     │                  │
│  ├─ voc_readings (hyper)  │     │  5 Modelos ONNX  │
│  ├─ ml_predictions (hyper)│◀───│  stress·bloom·   │
│  ├─ alerts                │     │  pest·fire·carbon│
│  └─ insight_logs          │     └──────────────────┘
└───────────┬───────────────┘
            │
     ┌──────┴──────┐
     ▼             ▼
┌──────────┐ ┌──────────────────────────┐
│ FastAPI  │ │  React Dashboard         │
│ REST API │ │  ├─ Mapa sensores        │
│ :8000    │ │  ├─ Gráficas VOC real-time│
│          │ │  ├─ Radar compuestos     │
│ /sensors │ │  ├─ Timeline predicciones│
│ /parcelas│ │  ├─ Panel metabolismo    │
│ /alerts  │ │  ├─ Alertas activas      │
│ /insights│ │  └─ Billing / Settings   │
└──────────┘ └──────────────────────────┘
```
