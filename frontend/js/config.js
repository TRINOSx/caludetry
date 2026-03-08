/* ================================
   VOC Field Intelligence - Configuration
   ================================ */

const CONFIG = {
    // API Endpoints (PHP Backend)
    API_BASE: '/backend/api',
    ENDPOINTS: {
        sensorData: '/sensor_data.php',
        vocReadings: '/voc_readings.php',
        parcelStatus: '/parcel_status.php',
        predictions: '/predictions.php',
        alerts: '/alerts.php',
        alphaEarth: '/alpha_earth.php',
        settings: '/settings.php',
        sensorUpload: '/sensor_upload.php',
    },

    // Refresh intervals (ms)
    REFRESH: {
        vocData: 5000,       // 5 seconds
        sensorData: 15000,   // 15 seconds
        predictions: 60000,  // 1 minute
        alerts: 30000,       // 30 seconds
        charts: 10000,       // 10 seconds
        weather: 300000,     // 5 minutes
    },

    // VOC Thresholds (ppb)
    THRESHOLDS: {
        methane: { low: 100, normal: 400, elevated: 600, high: 1000 },
        co2: { low: 300, normal: 500, elevated: 800, high: 1200 },
        nh3: { low: 50, normal: 200, elevated: 400, high: 600 },
        ethanol: { low: 50, normal: 200, elevated: 400, high: 600 },
        co: { low: 100, normal: 300, elevated: 500, high: 800 },
        no2: { low: 50, normal: 150, elevated: 300, high: 500 },
        h2: { low: 50, normal: 200, elevated: 400, high: 600 },
        formaldehyde: { low: 50, normal: 200, elevated: 400, high: 600 },
        ozone: { low: 50, normal: 200, elevated: 400, high: 600 },
        tvoc: { low: 100, normal: 300, elevated: 600, high: 1000 },
    },

    // Plant Status Thresholds
    PLANT_THRESHOLDS: {
        stress: { good: 15, warning: 25, danger: 40 },
        plagues: { good: 5, warning: 15, danger: 30 },
        metabolism: { danger: 40, warning: 60, good: 70 },
        floration: { info: true },
    },

    // Chart Colors
    CHART_COLORS: {
        tvoc: '#06b6d4',
        voc: '#8b5cf6',
        co: '#ef4444',
        h2: '#f59e0b',
        ch4: '#10b981',
        smoke: '#94a3b8',
        odor: '#ec4899',
        spo40: '#3b82f6',
        co2: '#22c55e',
        nh3: '#f97316',
        temperature: '#ef4444',
        humidity: '#3b82f6',
        soilMoisture: '#8b5cf6',
        ph: '#10b981',
    },

    // Parcels
    PARCELS: [
        { id: 'P1', name: 'Parcela 1', crop: 'Corn', area: '10.7 ha', hacienda: 'Hacienda San Joaquin' },
        { id: 'P2', name: 'Parcela 2', crop: 'Wheat', area: '8.3 ha', hacienda: 'Hacienda San Joaquin' },
        { id: 'P3', name: 'Parcela 3', crop: 'Soybean', area: '12.1 ha', hacienda: 'Hacienda San Joaquin' },
        { id: 'P4', name: 'Parcela 4', crop: 'Tomato', area: '5.5 ha', hacienda: 'Hacienda San Joaquin' },
    ],

    // Sensor Nodes
    SENSOR_NODES: [
        { id: 'VOC_NODE_1', type: 'Bosch BME688', location: 'North', status: 'online' },
        { id: 'VOC_NODE_2', type: 'Bosch BME688', location: 'East', status: 'online' },
        { id: 'VOC_NODE_3', type: 'Bosch BME688', location: 'South', status: 'online' },
        { id: 'VOC_NODE_4', type: 'Bosch BME688', location: 'West', status: 'offline' },
        { id: 'SOIL_NODE_1', type: 'NPK Sensor', location: 'Center', status: 'online' },
        { id: 'SOIL_NODE_2', type: 'pH/EC Sensor', location: 'Center', status: 'online' },
        { id: 'WEATHER_1', type: 'Weather Station', location: 'Field Edge', status: 'online' },
        { id: 'CAM_NODE_1', type: 'RGB Camera', location: 'Tower', status: 'online' },
    ],
};
