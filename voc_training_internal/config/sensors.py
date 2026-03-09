"""
Hardware sensor definitions for the VOC eNose training array.

Physical hardware:
  - 8x DFRobot MEMS gas sensors (HCHO, H2S, NO2, VOC, CH4, CO, EtOH, H2)
  - 4x Figaro TGS MOx sensors
  - 1x Particle size sensor (PM2.5/PM10)
  - 1x Bosch BME688 e-nose (temp, humidity, pressure, gas resistance)
  - 1x NPKPHCTH-S 7-in-1 soil sensor (RS485)
  - ESP32 + LoRa transport
"""

# ============================================================
# DFRobot MEMS Gas Sensor Array (8 channels)
# ============================================================
DFROBOT_MEMS = {
    "HCHO": {
        "model": "DFRobot SEN0466",
        "type": "MEMS electrochemical",
        "gas": "formaldehyde",
        "formula": "HCHO",
        "range_ppm": (0, 5),
        "resolution_ppm": 0.01,
        "response_time_s": 30,
        "interface": "I2C",
        "address": 0x77,
        "channel": 0,
    },
    "H2S": {
        "model": "DFRobot SEN0467",
        "type": "MEMS electrochemical",
        "gas": "hydrogen_sulfide",
        "formula": "H2S",
        "range_ppm": (0, 100),
        "resolution_ppm": 0.1,
        "response_time_s": 30,
        "interface": "I2C",
        "address": 0x76,
        "channel": 1,
    },
    "NO2": {
        "model": "DFRobot SEN0468",
        "type": "MEMS electrochemical",
        "gas": "nitrogen_dioxide",
        "formula": "NO2",
        "range_ppm": (0, 20),
        "resolution_ppm": 0.02,
        "response_time_s": 30,
        "interface": "I2C",
        "address": 0x75,
        "channel": 2,
    },
    "VOC": {
        "model": "DFRobot SEN0469",
        "type": "MEMS MOx",
        "gas": "total_voc",
        "formula": "TVOC",
        "range_ppb": (0, 30000),
        "resolution_ppb": 1,
        "response_time_s": 10,
        "interface": "I2C",
        "address": 0x74,
        "channel": 3,
    },
    "CH4": {
        "model": "DFRobot SEN0470",
        "type": "MEMS catalytic",
        "gas": "methane",
        "formula": "CH4",
        "range_ppm": (0, 1000),
        "resolution_ppm": 1,
        "response_time_s": 15,
        "interface": "I2C",
        "address": 0x73,
        "channel": 4,
    },
    "CO": {
        "model": "DFRobot SEN0471",
        "type": "MEMS electrochemical",
        "gas": "carbon_monoxide",
        "formula": "CO",
        "range_ppm": (0, 1000),
        "resolution_ppm": 0.5,
        "response_time_s": 30,
        "interface": "I2C",
        "address": 0x72,
        "channel": 5,
    },
    "EtOH": {
        "model": "DFRobot SEN0472",
        "type": "MEMS MOx",
        "gas": "ethanol",
        "formula": "C2H5OH",
        "range_ppm": (0, 500),
        "resolution_ppm": 0.1,
        "response_time_s": 10,
        "interface": "I2C",
        "address": 0x71,
        "channel": 6,
    },
    "H2": {
        "model": "DFRobot SEN0473",
        "type": "MEMS thermal conductivity",
        "gas": "hydrogen",
        "formula": "H2",
        "range_ppm": (0, 1000),
        "resolution_ppm": 1,
        "response_time_s": 15,
        "interface": "I2C",
        "address": 0x70,
        "channel": 7,
    },
}

# ============================================================
# Figaro TGS MOx Sensors (4 channels via ADS1115 ADC)
# ============================================================
FIGARO_TGS = {
    "TGS2600": {
        "model": "Figaro TGS2600",
        "type": "MOx (SnO2)",
        "target_gases": ["H2", "C2H5OH", "isobutane"],
        "range_ppm": (1, 100),
        "heater_voltage": 5.0,
        "circuit_voltage": 5.0,
        "load_resistance_ohm": 10000,
        "adc_channel": 0,
        "cross_sensitivity": {
            "H2": 1.0, "C2H5OH": 0.7, "CH4": 0.3, "CO": 0.2, "isobutane": 0.5,
        },
    },
    "TGS2602": {
        "model": "Figaro TGS2602",
        "type": "MOx (SnO2)",
        "target_gases": ["H2S", "NH3", "C2H5OH", "toluene"],
        "range_ppm": (1, 30),
        "heater_voltage": 5.0,
        "circuit_voltage": 5.0,
        "load_resistance_ohm": 10000,
        "adc_channel": 1,
        "cross_sensitivity": {
            "H2S": 1.0, "NH3": 0.6, "C2H5OH": 0.8, "toluene": 0.5,
            "HCHO": 0.3, "CH4": 0.1,
        },
    },
    "TGS2611": {
        "model": "Figaro TGS2611",
        "type": "MOx (SnO2)",
        "target_gases": ["CH4", "natural_gas"],
        "range_ppm": (500, 10000),
        "heater_voltage": 5.0,
        "circuit_voltage": 5.0,
        "load_resistance_ohm": 10000,
        "adc_channel": 2,
        "cross_sensitivity": {
            "CH4": 1.0, "C2H5OH": 0.6, "H2": 0.5, "CO": 0.1, "isobutane": 0.4,
        },
    },
    "TGS2620": {
        "model": "Figaro TGS2620",
        "type": "MOx (SnO2)",
        "target_gases": ["C2H5OH", "organic_solvents"],
        "range_ppm": (50, 5000),
        "heater_voltage": 5.0,
        "circuit_voltage": 5.0,
        "load_resistance_ohm": 10000,
        "adc_channel": 3,
        "cross_sensitivity": {
            "C2H5OH": 1.0, "H2": 0.7, "CH4": 0.4, "CO": 0.3, "isobutane": 0.6,
        },
    },
}

# ============================================================
# Bosch BME688 Environmental + eNose
# ============================================================
BOSCH_BME688 = {
    "model": "Bosch BME688",
    "type": "MEMS environmental + gas",
    "interface": "I2C",
    "address": 0x76,
    "outputs": {
        "temperature": {"unit": "C", "range": (-40, 85), "resolution": 0.01},
        "humidity": {"unit": "%RH", "range": (0, 100), "resolution": 0.008},
        "pressure": {"unit": "hPa", "range": (300, 1100), "resolution": 0.18},
        "gas_resistance": {"unit": "ohm", "range": (0, 1e7), "description": "MOx gas resistance"},
    },
    # BME688 AI mode: heater profiles for VOC classification
    "heater_profiles": {
        "default": [320, 100, 100, 100, 200, 200, 200, 320, 320, 320],  # temps in C
        "durations_ms": [150, 150, 150, 150, 150, 150, 150, 150, 150, 150],
    },
}

# ============================================================
# Particle Size Sensor (PM2.5 / PM10)
# ============================================================
PARTICLE_SENSOR = {
    "model": "PMS5003",  # Plantower
    "type": "laser scattering",
    "interface": "UART",
    "baud_rate": 9600,
    "outputs": {
        "PM1_0": {"unit": "ug/m3", "range": (0, 500)},
        "PM2_5": {"unit": "ug/m3", "range": (0, 500)},
        "PM10": {"unit": "ug/m3", "range": (0, 500)},
        "particles_0_3um": {"unit": "count/0.1L", "range": (0, 65535)},
        "particles_0_5um": {"unit": "count/0.1L", "range": (0, 65535)},
        "particles_1_0um": {"unit": "count/0.1L", "range": (0, 65535)},
        "particles_2_5um": {"unit": "count/0.1L", "range": (0, 65535)},
        "particles_5_0um": {"unit": "count/0.1L", "range": (0, 65535)},
        "particles_10um": {"unit": "count/0.1L", "range": (0, 65535)},
    },
}

# ============================================================
# NPKPHCTH-S 7-in-1 Soil Sensor (RS485 Modbus)
# ============================================================
SOIL_SENSOR = {
    "model": "NPKPHCTH-S",
    "type": "multi-parameter soil probe",
    "interface": "RS485",
    "protocol": "Modbus RTU",
    "baud_rate": 4800,
    "slave_address": 0x01,
    "outputs": {
        "nitrogen": {"unit": "mg/kg", "range": (0, 1999), "register": 0x001E},
        "phosphorus": {"unit": "mg/kg", "range": (0, 1999), "register": 0x001F},
        "potassium": {"unit": "mg/kg", "range": (0, 1999), "register": 0x0020},
        "pH": {"unit": "pH", "range": (3.0, 9.0), "register": 0x0006, "scale": 0.1},
        "conductivity": {"unit": "uS/cm", "range": (0, 20000), "register": 0x0015},
        "temperature": {"unit": "C", "range": (-40, 80), "register": 0x0013, "scale": 0.1},
        "moisture": {"unit": "%", "range": (0, 100), "register": 0x0012, "scale": 0.1},
    },
}

# ============================================================
# Transport: ESP32 + LoRa
# ============================================================
TRANSPORT = {
    "mcu": "ESP32-S3",
    "lora_module": "SX1276",
    "lora_frequency_mhz": 915,  # US ISM band (adjust per region)
    "lora_spreading_factor": 7,
    "lora_bandwidth_khz": 125,
    "adc": "ADS1115",  # 16-bit ADC for TGS analog sensors
    "adc_address": 0x48,
    "adc_gain": 1,      # ±4.096V
    "sample_interval_s": 30,
    "transmit_interval_s": 60,
}

# ============================================================
# Unified sensor channel map
# All channels that produce a reading per sample
# ============================================================
ALL_SENSOR_CHANNELS = []

# DFRobot MEMS: 8 gas channels
for name, spec in DFROBOT_MEMS.items():
    ALL_SENSOR_CHANNELS.append({
        "id": f"dfrobot_{name.lower()}",
        "sensor_group": "dfrobot_mems",
        "gas": spec["formula"],
        "unit": "ppm" if "range_ppm" in spec else "ppb",
    })

# Figaro TGS: 4 resistance ratio channels
for name, spec in FIGARO_TGS.items():
    ALL_SENSOR_CHANNELS.append({
        "id": f"tgs_{name.lower()}",
        "sensor_group": "figaro_tgs",
        "gas": spec["target_gases"][0],
        "unit": "Rs/R0",
    })

# BME688: 4 environmental channels
for param in BOSCH_BME688["outputs"]:
    ALL_SENSOR_CHANNELS.append({
        "id": f"bme688_{param}",
        "sensor_group": "bosch_bme688",
        "gas": param,
        "unit": BOSCH_BME688["outputs"][param]["unit"],
    })

# Particle sensor: 3 main PM channels
for pm in ["PM1_0", "PM2_5", "PM10"]:
    ALL_SENSOR_CHANNELS.append({
        "id": f"pm_{pm.lower()}",
        "sensor_group": "particle",
        "gas": pm,
        "unit": "ug/m3",
    })

# Soil sensor: 7 channels
for param in SOIL_SENSOR["outputs"]:
    ALL_SENSOR_CHANNELS.append({
        "id": f"soil_{param}",
        "sensor_group": "soil_npk",
        "gas": param,
        "unit": SOIL_SENSOR["outputs"][param]["unit"],
    })

# Total: 8 + 4 + 4 + 3 + 7 = 26 sensor channels per sample
TOTAL_CHANNELS = len(ALL_SENSOR_CHANNELS)
