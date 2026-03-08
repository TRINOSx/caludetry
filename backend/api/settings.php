<?php
/**
 * VOC Field Intelligence - Settings API
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$settings_file = __DIR__ . '/../config/settings.json';

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    if (file_exists($settings_file)) {
        echo file_get_contents($settings_file);
    } else {
        echo json_encode(get_default_settings());
    }
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $data = json_decode(file_get_contents('php://input'), true);
    if (!$data) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid JSON']);
        exit;
    }

    // Merge with defaults
    $current = file_exists($settings_file) ? json_decode(file_get_contents($settings_file), true) : get_default_settings();
    $merged = array_replace_recursive($current, $data);

    file_put_contents($settings_file, json_encode($merged, JSON_PRETTY_PRINT));

    echo json_encode(['status' => 'ok', 'settings' => $merged]);
    exit;
}

function get_default_settings() {
    return [
        'sampling' => [
            'voc_rate' => '15s',
            'soil_rate' => '5min',
            'climate_rate' => '1min',
        ],
        'thresholds' => [
            'methane' => 500,
            'nh3' => 300,
            'tvoc' => 600,
            'ethanol' => 400,
            'co' => 500,
            'stress_alert' => 25,
        ],
        'api' => [
            'backend_url' => 'http://localhost:8080/api',
            'mqtt_broker' => 'mqtt://localhost:1883',
        ],
        'parcels' => [
            ['id' => 'P1', 'name' => 'Parcela 1', 'crop' => 'Corn', 'lat' => 20.6597, 'lon' => -103.3496],
            ['id' => 'P2', 'name' => 'Parcela 2', 'crop' => 'Wheat', 'lat' => 20.6610, 'lon' => -103.3480],
        ],
    ];
}
