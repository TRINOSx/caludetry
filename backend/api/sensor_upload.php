<?php
/**
 * VOC Field Intelligence - Sensor Upload API
 * Receives data from edge nodes (ESP32/Raspberry Pi)
 * POST endpoint for MQTT bridge or direct HTTP
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-API-Key');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

require_once __DIR__ . '/../config/database.php';

// Parse JSON body
$raw = file_get_contents('php://input');
$data = json_decode($raw, true);

if (!$data) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON body']);
    exit;
}

// Validate required fields
$required = ['parcel_id', 'sensor_id', 'timestamp'];
foreach ($required as $field) {
    if (empty($data[$field])) {
        http_response_code(400);
        echo json_encode(['error' => "Missing required field: $field"]);
        exit;
    }
}

try {
    $db = Database::connect();

    // Insert sensor data
    $stmt = $db->prepare("
        INSERT INTO sensor_data (
            time, parcel_id, sensor_id,
            co2, nh3, methane, ethanol, tvoc,
            humidity, temperature, ph, conductivity,
            hydrogen, carbon_monoxide, formaldehyde, ozone, sulfur,
            soil_moisture, voc, smoke, odor, spo40
        ) VALUES (
            :time, :parcel_id, :sensor_id,
            :co2, :nh3, :methane, :ethanol, :tvoc,
            :humidity, :temperature, :ph, :conductivity,
            :hydrogen, :carbon_monoxide, :formaldehyde, :ozone, :sulfur,
            :soil_moisture, :voc, :smoke, :odor, :spo40
        )
    ");

    $stmt->execute([
        'time' => $data['timestamp'],
        'parcel_id' => $data['parcel_id'],
        'sensor_id' => $data['sensor_id'],
        'co2' => $data['co2'] ?? null,
        'nh3' => $data['nh3'] ?? null,
        'methane' => $data['methane'] ?? null,
        'ethanol' => $data['ethanol'] ?? null,
        'tvoc' => $data['tvoc'] ?? null,
        'humidity' => $data['humidity'] ?? null,
        'temperature' => $data['temp'] ?? $data['temperature'] ?? null,
        'ph' => $data['ph'] ?? null,
        'conductivity' => $data['conductivity'] ?? null,
        'hydrogen' => $data['h2'] ?? $data['hydrogen'] ?? null,
        'carbon_monoxide' => $data['co'] ?? $data['carbon_monoxide'] ?? null,
        'formaldehyde' => $data['formaldehyde'] ?? $data['hcho'] ?? null,
        'ozone' => $data['ozone'] ?? $data['o3'] ?? null,
        'sulfur' => $data['sulfur'] ?? null,
        'soil_moisture' => $data['soil_moisture'] ?? null,
        'voc' => $data['voc'] ?? null,
        'smoke' => $data['smoke'] ?? null,
        'odor' => $data['odor'] ?? null,
        'spo40' => $data['spo40'] ?? null,
    ]);

    // Insert VOC profile if vector provided
    if (!empty($data['voc_vector']) && is_array($data['voc_vector'])) {
        $voc_stmt = $db->prepare("
            INSERT INTO voc_profile (time, parcel_id, compound, value)
            VALUES (:time, :parcel_id, :compound, :value)
        ");

        $compounds = [
            'VOC', 'VOC2', 'TVOC', 'TVOC2', 'CO', 'CO2', 'NO2',
            'C2H5OH', 'H2', 'NH3', 'CH4', 'CH3COOH', 'C2H2',
            'C3H3N', 'C6H6', 'C4H6', 'CS2', 'C2H6S2', 'C2H4',
            'C2H4O', 'HCHO', 'HCOOH', 'HCl', 'HCN', 'C4H8',
            'CH3OH', 'CH4S', 'C2H6S', 'C8H10', 'C8H8', 'C7H8',
        ];

        foreach ($data['voc_vector'] as $i => $value) {
            $compound = $compounds[$i] ?? "VOC_$i";
            $voc_stmt->execute([
                'time' => $data['timestamp'],
                'parcel_id' => $data['parcel_id'],
                'compound' => $compound,
                'value' => $value,
            ]);
        }
    }

    // Run ML prediction (async if available)
    $prediction = run_quick_prediction($data);

    echo json_encode([
        'status' => 'ok',
        'message' => 'Data stored successfully',
        'prediction' => $prediction,
        'timestamp' => date('c'),
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Database error',
        'message' => $e->getMessage(),
    ]);
}

/**
 * Quick prediction based on thresholds and simple rules
 */
function run_quick_prediction($data) {
    $alerts = [];
    $stress = 0;
    $plague_risk = 0;

    // Methane check
    if (($data['methane'] ?? 0) > 500) {
        $alerts[] = 'High methane - soil microbiome issue possible';
        $stress += 10;
    }

    // Ammonia check
    if (($data['nh3'] ?? 0) > 300) {
        $alerts[] = 'Elevated NH3 - nitrogen imbalance';
        $stress += 15;
    }

    // Ethylene check (stress indicator)
    if (($data['ethanol'] ?? 0) > 400) {
        $alerts[] = 'Ethanol elevated - possible root hypoxia';
        $stress += 20;
    }

    // CO2 check
    if (($data['co2'] ?? 0) > 800) {
        $alerts[] = 'CO2 very high - check soil respiration';
        $stress += 5;
    }

    // TVOC check
    if (($data['tvoc'] ?? 0) > 600) {
        $plague_risk += 10;
        $alerts[] = 'TVOC elevated - possible pest defense VOCs';
    }

    return [
        'stress_estimate' => min(100, 10 + $stress),
        'plague_risk' => min(100, $plague_risk),
        'metabolism' => max(0, 80 - $stress * 0.5),
        'alerts' => $alerts,
    ];
}
