#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_ADS1X15.h>
#include <SensirionI2cSht3x.h>
#include <SensirionI2CSgp40.h>
#include <GasIndexAlgorithm.h>
#include <SparkFun_SCD4x_Arduino_Library.h>
#include <ArduinoJson.h>
#include <ArduinoOTA.h>
#include <SPIFFS.h>
#include <time.h>

// ──────────────────────── Pin Definitions ────────────────────────
#define LED_STATUS_PIN   2
#define PM_SERIAL_RX    16
#define PM_SERIAL_TX    17
#define I2C_SDA         21
#define I2C_SCL         22

// ──────────────────────── Config Struct ────────────────────────
struct Config {
  char tenant_slug[64];
  char wifi_ssid[64];
  char wifi_pass[64];
  char mqtt_host[128];
  uint16_t mqtt_port;
  char mqtt_user[64];
  char mqtt_pass[64];
  uint32_t sleep_seconds;
  uint32_t read_interval_ms;
};

// ──────────────────────── Globals ────────────────────────
static Config config;
static char hardwareId[18];  // MAC address as string

static WiFiClient wifiClient;
static PubSubClient mqttClient(wifiClient);

static Adafruit_ADS1115 ads;
static SensirionI2cSht3x sht3x;
static SensirionI2CSgp40 sgp40;
static GasIndexAlgorithm vocAlgorithm(GasIndexAlgorithm::ALGORITHM_TYPE_VOC);
static SCD4x scd4x;

static bool adsReady = false;
static bool sht3xReady = false;
static bool sgp40Ready = false;
static bool scd4xReady = false;
static bool pmReady = false;

static uint32_t lastReadMillis = 0;
static uint32_t wifiBackoffMs = 1000;
static uint32_t lastWifiAttempt = 0;

// PM2.5 sensor data
static uint16_t pm25Value = 0;
static uint16_t pm10Value = 0;

// NTP
static const char* ntpServer = "pool.ntp.org";
static const long gmtOffsetSec = 0;
static const int daylightOffsetSec = 0;

// ──────────────────────── LED Status ────────────────────────
enum LedState { LED_OFF, LED_BLINK, LED_SOLID };
static LedState ledState = LED_OFF;
static uint32_t lastLedToggle = 0;
static bool ledOn = false;

void updateLed() {
  switch (ledState) {
    case LED_SOLID:
      digitalWrite(LED_STATUS_PIN, HIGH);
      break;
    case LED_BLINK:
      if (millis() - lastLedToggle > 500) {
        ledOn = !ledOn;
        digitalWrite(LED_STATUS_PIN, ledOn ? HIGH : LOW);
        lastLedToggle = millis();
      }
      break;
    case LED_OFF:
      digitalWrite(LED_STATUS_PIN, LOW);
      break;
  }
}

// ──────────────────────── Config Loading ────────────────────────
bool loadConfig() {
  if (!SPIFFS.begin(true)) {
    Serial.println("SPIFFS mount failed");
    return false;
  }

  File file = SPIFFS.open("/config.json", "r");
  if (!file) {
    Serial.println("Config file not found");
    return false;
  }

  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, file);
  file.close();

  if (err) {
    Serial.printf("Config parse error: %s\n", err.c_str());
    return false;
  }

  strlcpy(config.tenant_slug, doc["tenant_slug"] | "default", sizeof(config.tenant_slug));
  strlcpy(config.wifi_ssid, doc["wifi_ssid"] | "", sizeof(config.wifi_ssid));
  strlcpy(config.wifi_pass, doc["wifi_pass"] | "", sizeof(config.wifi_pass));
  strlcpy(config.mqtt_host, doc["mqtt_host"] | "192.168.1.100", sizeof(config.mqtt_host));
  config.mqtt_port = doc["mqtt_port"] | 1883;
  strlcpy(config.mqtt_user, doc["mqtt_user"] | "", sizeof(config.mqtt_user));
  strlcpy(config.mqtt_pass, doc["mqtt_pass"] | "", sizeof(config.mqtt_pass));
  config.sleep_seconds = doc["sleep_seconds"] | 0;
  config.read_interval_ms = doc["read_interval_ms"] | 10000;

  Serial.printf("Config loaded: tenant=%s, mqtt=%s:%d\n",
    config.tenant_slug, config.mqtt_host, config.mqtt_port);
  return true;
}

// ──────────────────────── Hardware ID ────────────────────────
void buildHardwareId() {
  uint8_t mac[6];
  esp_read_mac(mac, ESP_MAC_WIFI_STA);
  snprintf(hardwareId, sizeof(hardwareId),
    "%02X%02X%02X%02X%02X%02X",
    mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  Serial.printf("Hardware ID: %s\n", hardwareId);
}

// ──────────────────────── WiFi ────────────────────────
void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    wifiBackoffMs = 1000;
    return;
  }

  uint32_t now = millis();
  if (now - lastWifiAttempt < wifiBackoffMs) {
    return;
  }
  lastWifiAttempt = now;

  Serial.printf("Connecting to WiFi '%s' (backoff %dms)...\n",
    config.wifi_ssid, wifiBackoffMs);
  ledState = LED_BLINK;

  WiFi.mode(WIFI_STA);
  WiFi.begin(config.wifi_ssid, config.wifi_pass);

  uint32_t startAttempt = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 10000) {
    delay(100);
    updateLed();
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("WiFi connected. IP: %s\n", WiFi.localIP().toString().c_str());
    ledState = LED_SOLID;
    wifiBackoffMs = 1000;
  } else {
    Serial.println("WiFi connection failed");
    wifiBackoffMs = min(wifiBackoffMs * 2, (uint32_t)60000);
  }
}

// ──────────────────────── MQTT ────────────────────────
void connectMqtt() {
  if (mqttClient.connected()) {
    return;
  }

  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  Serial.printf("Connecting to MQTT %s:%d...\n", config.mqtt_host, config.mqtt_port);

  mqttClient.setServer(config.mqtt_host, config.mqtt_port);
  mqttClient.setBufferSize(2048);

  char clientId[32];
  snprintf(clientId, sizeof(clientId), "esp32-%s", hardwareId);

  bool connected;
  if (strlen(config.mqtt_user) > 0) {
    connected = mqttClient.connect(clientId, config.mqtt_user, config.mqtt_pass);
  } else {
    connected = mqttClient.connect(clientId);
  }

  if (connected) {
    Serial.println("MQTT connected");
    ledState = LED_SOLID;
  } else {
    Serial.printf("MQTT connection failed, rc=%d\n", mqttClient.state());
    ledState = LED_BLINK;
  }
}

// ──────────────────────── NTP ────────────────────────
void syncTime() {
  configTime(gmtOffsetSec, daylightOffsetSec, ntpServer);
  Serial.println("NTP time sync requested");

  struct tm timeinfo;
  int retries = 0;
  while (!getLocalTime(&timeinfo) && retries < 10) {
    delay(500);
    retries++;
  }

  if (retries < 10) {
    Serial.printf("NTP synced: %04d-%02d-%02d %02d:%02d:%02d\n",
      timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
      timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
  } else {
    Serial.println("NTP sync failed, using millis() fallback");
  }
}

uint64_t getTimestampMs() {
  struct timeval tv;
  gettimeofday(&tv, NULL);
  return (uint64_t)tv.tv_sec * 1000ULL + (uint64_t)tv.tv_usec / 1000ULL;
}

// ──────────────────────── Sensor Init ────────────────────────
void initSensors() {
  Wire.begin(I2C_SDA, I2C_SCL);
  Wire.setClock(100000);

  // ADS1115 at 0x48
  if (ads.begin(0x48)) {
    ads.setGain(GAIN_ONE);  // +/-4.096V range
    adsReady = true;
    Serial.println("ADS1115 initialized");
  } else {
    Serial.println("ADS1115 not found");
  }

  // SHT31 at 0x44
  sht3x.begin(Wire, 0x44);
  uint16_t sht_status = 0;
  int16_t sht_err = sht3x.readStatusRegister(sht_status);
  if (sht_err == 0) {
    sht3xReady = true;
    Serial.println("SHT31 initialized");
  } else {
    Serial.println("SHT31 not found");
  }

  // SGP40 at 0x59
  sgp40.begin(Wire);
  uint16_t sgpSerial[3];
  int16_t sgp_err = sgp40.getSerialNumber(sgpSerial);
  if (sgp_err == 0) {
    sgp40Ready = true;
    Serial.println("SGP40 initialized");
  } else {
    Serial.println("SGP40 not found");
  }

  // SCD40 at 0x62
  if (scd4x.begin() == true) {
    scd4x.startPeriodicMeasurement();
    scd4xReady = true;
    Serial.println("SCD40 initialized");
  } else {
    Serial.println("SCD40 not found");
  }

  // PM2.5 sensor on UART2
  Serial2.begin(9600, SERIAL_8N1, PM_SERIAL_RX, PM_SERIAL_TX);
  pmReady = true;
  Serial.println("PM sensor UART initialized");
}

// ──────────────────────── PM Sensor Reading ────────────────────────
// Reads PMS5003-style sensor (32-byte frames starting with 0x42 0x4D)
bool readPmSensor() {
  if (!pmReady || Serial2.available() < 32) {
    return false;
  }

  // Find start bytes
  while (Serial2.available() >= 32) {
    if (Serial2.peek() != 0x42) {
      Serial2.read();
      continue;
    }

    uint8_t buf[32];
    Serial2.readBytes(buf, 32);

    if (buf[0] != 0x42 || buf[1] != 0x4D) {
      continue;
    }

    // Verify checksum
    uint16_t checksum = 0;
    for (int i = 0; i < 30; i++) {
      checksum += buf[i];
    }
    uint16_t expected = (buf[30] << 8) | buf[31];
    if (checksum != expected) {
      continue;
    }

    // Extract PM2.5 and PM10 (atmospheric environment, bytes 10-13)
    pm25Value = (buf[10] << 8) | buf[11];
    pm10Value = (buf[12] << 8) | buf[13];
    return true;
  }

  return false;
}

// ──────────────────────── Sensor Reading & Publish ────────────────────────
void readAndPublish() {
  float temperature = 0.0;
  float humidity = 0.0;
  int16_t adcValues[4] = {0, 0, 0, 0};
  uint16_t sgpRaw = 0;
  int32_t vocIndex = 0;
  uint16_t co2 = 0;

  // Read SHT31 (temperature + humidity)
  if (sht3xReady) {
    int16_t err = sht3x.measureSingleShot(
      REPEATABILITY_HIGH, false, temperature, humidity);
    if (err != 0) {
      Serial.printf("SHT31 read error: %d\n", err);
      temperature = 25.0;  // fallback
      humidity = 50.0;
    }
  }

  // Read ADS1115 channels (MiCS-4514, MiCS-5524, TGS2620, TGS2600)
  if (adsReady) {
    for (int ch = 0; ch < 4; ch++) {
      adcValues[ch] = ads.readADC_SingleEnded(ch);
    }
  }

  // Read SGP40 (TVOC)
  if (sgp40Ready) {
    uint16_t defaultRh = 0x8000;  // 50% RH
    uint16_t defaultT = 0x6666;   // 25C
    if (sht3xReady) {
      defaultRh = (uint16_t)((humidity / 100.0) * 65535);
      defaultT = (uint16_t)(((temperature + 45.0) / 175.0) * 65535);
    }
    int16_t err = sgp40.measureRawSignal(defaultRh, defaultT, sgpRaw);
    if (err == 0) {
      vocIndex = vocAlgorithm.process(sgpRaw);
    } else {
      Serial.printf("SGP40 read error: %d\n", err);
    }
  }

  // Read SCD40 (CO2)
  if (scd4xReady && scd4x.readMeasurement()) {
    co2 = scd4x.getCO2();
  }

  // Read PM sensor
  readPmSensor();

  // Build JSON payload
  JsonDocument doc;
  doc["hardware_id"] = hardwareId;
  doc["timestamp_ms"] = getTimestampMs();
  doc["temperature_c"] = serialized(String(temperature, 2));
  doc["humidity_pct"] = serialized(String(humidity, 2));

  JsonArray readings = doc["readings"].to<JsonArray>();

  // MiCS-4514 (NO2 sensor) - channel 0
  JsonObject r0 = readings.add<JsonObject>();
  r0["compound"] = "NO2";
  r0["value_ppm"] = 0;
  r0["raw_adc"] = adcValues[0];

  // MiCS-5524 (CO, VOC sensor) - channel 1
  JsonObject r1 = readings.add<JsonObject>();
  r1["compound"] = "CO";
  r1["value_ppm"] = 0;
  r1["raw_adc"] = adcValues[1];

  // TGS2620 (ethanol, organic solvents) - channel 2
  JsonObject r2 = readings.add<JsonObject>();
  r2["compound"] = "C2H5OH";
  r2["value_ppm"] = 0;
  r2["raw_adc"] = adcValues[2];

  // TGS2600 (general air quality) - channel 3
  JsonObject r3 = readings.add<JsonObject>();
  r3["compound"] = "VOC";
  r3["value_ppm"] = 0;
  r3["raw_adc"] = adcValues[3];

  // SGP40 TVOC index
  JsonObject r4 = readings.add<JsonObject>();
  r4["compound"] = "TVOC";
  r4["value_ppm"] = vocIndex;
  r4["raw_adc"] = sgpRaw;

  // SCD40 CO2
  JsonObject r5 = readings.add<JsonObject>();
  r5["compound"] = "CO2";
  r5["value_ppm"] = co2;
  r5["raw_adc"] = co2;

  doc["pm25"] = pm25Value;
  doc["pm10"] = pm10Value;

  // Serialize
  char payload[1024];
  size_t len = serializeJson(doc, payload, sizeof(payload));

  // Build topic: voc/{tenant_slug}/{hardware_id}/raw
  char topic[128];
  snprintf(topic, sizeof(topic), "voc/%s/%s/raw",
    config.tenant_slug, hardwareId);

  // Publish
  if (mqttClient.connected()) {
    bool ok = mqttClient.publish(topic, payload, len);
    if (ok) {
      Serial.printf("Published %d bytes to %s\n", (int)len, topic);
    } else {
      Serial.println("MQTT publish failed");
    }
  } else {
    Serial.println("MQTT not connected, skipping publish");
  }
}

// ──────────────────────── OTA Setup ────────────────────────
void setupOTA() {
  char hostname[32];
  snprintf(hostname, sizeof(hostname), "voc-esp32-%s", hardwareId);
  ArduinoOTA.setHostname(hostname);

  ArduinoOTA.onStart([]() {
    String type = (ArduinoOTA.getCommand() == U_FLASH) ? "sketch" : "filesystem";
    Serial.printf("OTA Start: %s\n", type.c_str());
  });

  ArduinoOTA.onEnd([]() {
    Serial.println("\nOTA End");
  });

  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("OTA Progress: %u%%\r", (progress / (total / 100)));
  });

  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("OTA Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) Serial.println("Auth Failed");
    else if (error == OTA_BEGIN_ERROR) Serial.println("Begin Failed");
    else if (error == OTA_CONNECT_ERROR) Serial.println("Connect Failed");
    else if (error == OTA_RECEIVE_ERROR) Serial.println("Receive Failed");
    else if (error == OTA_END_ERROR) Serial.println("End Failed");
  });

  ArduinoOTA.begin();
  Serial.println("OTA ready");
}

// ──────────────────────── Deep Sleep ────────────────────────
void enterDeepSleep() {
  if (config.sleep_seconds == 0) {
    return;  // Deep sleep disabled
  }

  Serial.printf("Entering deep sleep for %d seconds\n", config.sleep_seconds);
  ledState = LED_OFF;
  updateLed();

  mqttClient.disconnect();
  WiFi.disconnect(true);

  esp_sleep_enable_timer_wakeup((uint64_t)config.sleep_seconds * 1000000ULL);
  esp_deep_sleep_start();
}

// ──────────────────────── Arduino Setup ────────────────────────
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== VOC Mesh Sensor Node ===");

  pinMode(LED_STATUS_PIN, OUTPUT);
  ledState = LED_BLINK;

  buildHardwareId();

  if (!loadConfig()) {
    Serial.println("Using default config values");
    strlcpy(config.tenant_slug, "default", sizeof(config.tenant_slug));
    strlcpy(config.wifi_ssid, "VOC-Mesh", sizeof(config.wifi_ssid));
    strlcpy(config.wifi_pass, "", sizeof(config.wifi_pass));
    strlcpy(config.mqtt_host, "192.168.1.100", sizeof(config.mqtt_host));
    config.mqtt_port = 1883;
    config.mqtt_user[0] = '\0';
    config.mqtt_pass[0] = '\0';
    config.sleep_seconds = 0;
    config.read_interval_ms = 10000;
  }

  initSensors();
  connectWiFi();

  if (WiFi.status() == WL_CONNECTED) {
    syncTime();
    setupOTA();
  }

  connectMqtt();

  Serial.printf("Read interval: %d ms\n", config.read_interval_ms);
  Serial.printf("Deep sleep: %s (%d s)\n",
    config.sleep_seconds > 0 ? "enabled" : "disabled",
    config.sleep_seconds);
  Serial.println("Setup complete\n");
}

// ──────────────────────── Arduino Loop ────────────────────────
void loop() {
  updateLed();
  connectWiFi();
  connectMqtt();
  mqttClient.loop();
  ArduinoOTA.handle();

  uint32_t now = millis();
  if (now - lastReadMillis >= config.read_interval_ms) {
    lastReadMillis = now;
    readAndPublish();

    // Enter deep sleep if configured
    enterDeepSleep();
  }
}
