/* ================================
   API Client - PHP Backend Bridge
   ================================ */

const APIClient = {
    baseURL: CONFIG.API_BASE,

    // Generic fetch with error handling
    async request(endpoint, options = {}) {
        const url = this.baseURL + endpoint;
        const defaults = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
        };

        try {
            const response = await fetch(url, { ...defaults, ...options });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.warn(`API call failed (${endpoint}):`, error.message);
            // Return simulated data when backend is not available
            return this.getSimulatedData(endpoint);
        }
    },

    // GET
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    // POST
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    // === API Methods ===

    // Get sensor data for parcel
    async getSensorData(parcelId) {
        return this.get(`${CONFIG.ENDPOINTS.sensorData}?parcel_id=${parcelId}`);
    },

    // Get VOC readings
    async getVOCReadings(parcelId, timeRange) {
        return this.get(`${CONFIG.ENDPOINTS.vocReadings}?parcel_id=${parcelId}&range=${timeRange}`);
    },

    // Get parcel status (stress, metabolism, etc)
    async getParcelStatus(parcelId) {
        return this.get(`${CONFIG.ENDPOINTS.parcelStatus}?parcel_id=${parcelId}`);
    },

    // Get ML predictions
    async getPredictions(parcelId) {
        return this.get(`${CONFIG.ENDPOINTS.predictions}?parcel_id=${parcelId}`);
    },

    // Get alerts
    async getAlerts() {
        return this.get(CONFIG.ENDPOINTS.alerts);
    },

    // Get AlphaEarth data
    async getAlphaEarthData(lat, lon) {
        return this.get(`${CONFIG.ENDPOINTS.alphaEarth}?lat=${lat}&lon=${lon}`);
    },

    // Upload sensor data (from edge nodes)
    async uploadSensorData(data) {
        return this.post(CONFIG.ENDPOINTS.sensorUpload, data);
    },

    // Save settings
    async saveSettings(settings) {
        return this.post(CONFIG.ENDPOINTS.settings, settings);
    },

    // === Simulated Data (when backend unavailable) ===
    getSimulatedData(endpoint) {
        const now = new Date();

        if (endpoint.includes('sensor_data') || endpoint.includes('voc_readings')) {
            return this.simulateSensorData(now);
        }
        if (endpoint.includes('parcel_status')) {
            return this.simulateParcelStatus();
        }
        if (endpoint.includes('predictions')) {
            return this.simulatePredictions();
        }
        if (endpoint.includes('alerts')) {
            return this.simulateAlerts();
        }
        if (endpoint.includes('alpha_earth')) {
            return this.simulateAlphaEarth();
        }
        return {};
    },

    simulateSensorData(now) {
        const points = [];
        for (let i = 60; i >= 0; i--) {
            const t = new Date(now.getTime() - i * 30000);
            points.push({
                timestamp: t.toISOString(),
                tvoc: 200 + Math.sin(i * 0.1) * 50 + Math.random() * 30,
                voc: 150 + Math.cos(i * 0.08) * 40 + Math.random() * 20,
                co: 100 + Math.sin(i * 0.15) * 30 + Math.random() * 15,
                h2: 80 + Math.cos(i * 0.12) * 25 + Math.random() * 10,
                ch4: 120 + Math.sin(i * 0.09) * 35 + Math.random() * 20,
                smoke: 50 + Math.random() * 20,
                odor: 60 + Math.sin(i * 0.2) * 20 + Math.random() * 10,
                spo40: 90 + Math.cos(i * 0.11) * 30 + Math.random() * 15,
                co2: 400 + Math.sin(i * 0.07) * 50 + Math.random() * 25,
                nh3: 60 + Math.cos(i * 0.13) * 20 + Math.random() * 10,
                temperature: 16 + Math.sin(i * 0.05) * 3 + Math.random(),
                humidity: 74 + Math.cos(i * 0.06) * 5 + Math.random() * 2,
                soil_moisture: 38 + Math.sin(i * 0.04) * 5 + Math.random() * 2,
                ph: 6.5 + Math.sin(i * 0.03) * 0.5,
            });
        }
        return { data: points };
    },

    simulateParcelStatus() {
        return {
            stress: 10 + Math.random() * 5,
            floration: 1 + Math.random() * 2,
            plagues: Math.random() * 2,
            metabolism: 78 + Math.random() * 5,
            oxygen_generate: 500,
            co2_transformate: 200,
        };
    },

    simulatePredictions() {
        return {
            '24h': { stress: 12, plagues: 0.5, metabolism: 78, flowering: 1.5 },
            '72h': { stress: 15, plagues: 1.2, metabolism: 75, flowering: 2.0 },
            '7d': { stress: 18, plagues: 2.1, metabolism: 72, flowering: 3.5 },
            confidence: 0.87,
            model_version: 'v2.1-alpha',
        };
    },

    simulateAlerts() {
        return {
            alerts: [
                {
                    id: 1,
                    type: 'warning',
                    title: 'Methane Level Rising',
                    description: 'CH4 increased 15% in Parcela 1 - possible soil microbiome shift',
                    timestamp: new Date(Date.now() - 300000).toISOString(),
                    parcel: 'P1',
                },
                {
                    id: 2,
                    type: 'info',
                    title: 'Ethylene Spike Detected',
                    description: 'C2H4 elevated in sector NE - monitoring plant stress response',
                    timestamp: new Date(Date.now() - 900000).toISOString(),
                    parcel: 'P1',
                },
                {
                    id: 3,
                    type: 'danger',
                    title: 'NH3 Threshold Alert',
                    description: 'Ammonia levels approaching critical threshold in Parcela 2',
                    timestamp: new Date(Date.now() - 1800000).toISOString(),
                    parcel: 'P2',
                },
            ],
        };
    },

    simulateAlphaEarth() {
        // Simulated geospatial embedding vector (512 dims truncated)
        const embedding = Array.from({ length: 64 }, () => parseFloat((Math.random() * 2 - 1).toFixed(4)));
        return {
            embedding,
            geo_score: 92,
            soil_health: 87,
            ndvi: 0.82,
            ndwi: 0.45,
            evi: 0.71,
            land_use_history: 'Agricultural - Corn rotation since 2018',
            regional_risk: 'Low',
            similar_parcels: 1247,
        };
    },
};
