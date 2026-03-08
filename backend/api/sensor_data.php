<?php
/**
 * VOC Field Intelligence - Sensor Data API
 * Returns time-series sensor data for a parcel
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

require_once __DIR__ . '/../config/database.php';

$parcel_id = $_GET['parcel_id'] ?? 'P1';
$range = $_GET['range'] ?? '1h';

// Calculate time range
$range_map = [
    '1h' => '1 HOUR',
    '6h' => '6 HOURS',
    '24h' => '24 HOURS',
    '7d' => '7 DAYS',
];
$sql_range = $range_map[$range] ?? '1 HOUR';

try {
    $db = Database::connect();

    $stmt = $db->prepare("
        SELECT
            time AS timestamp,
            co2, nh3, methane AS ch4, ethanol, tvoc,
            humidity, temperature, ph, conductivity,
            hydrogen AS h2, carbon_monoxide AS co,
            formaldehyde, ozone, sulfur,
            soil_moisture, voc, smoke, odor, spo40
        FROM sensor_data
        WHERE parcel_id = :parcel_id
          AND time >= NOW() - INTERVAL $sql_range
        ORDER BY time ASC
    ");

    $stmt->execute(['parcel_id' => $parcel_id]);
    $data = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Cast numeric fields
    $data = array_map(function($row) {
        foreach ($row as $key => $val) {
            if ($key !== 'timestamp') {
                $row[$key] = floatval($val);
            }
        }
        return $row;
    }, $data);

    echo json_encode([
        'status' => 'ok',
        'parcel_id' => $parcel_id,
        'range' => $range,
        'count' => count($data),
        'data' => $data,
    ]);

} catch (Exception $e) {
    // Return simulated data if DB is not available
    $data = generate_simulated_data($range);
    echo json_encode([
        'status' => 'simulated',
        'parcel_id' => $parcel_id,
        'range' => $range,
        'count' => count($data),
        'data' => $data,
    ]);
}

function generate_simulated_data($range) {
    $points = [];
    $count = ['1h' => 60, '6h' => 120, '24h' => 288, '7d' => 672][$range] ?? 60;
    $interval = ['1h' => 60, '6h' => 180, '24h' => 300, '7d' => 900][$range] ?? 60;
    $now = time();

    for ($i = $count; $i >= 0; $i--) {
        $t = $now - ($i * $interval);
        $points[] = [
            'timestamp' => date('c', $t),
            'tvoc' => round(200 + sin($i * 0.1) * 50 + rand(0, 30), 1),
            'voc' => round(150 + cos($i * 0.08) * 40 + rand(0, 20), 1),
            'co' => round(100 + sin($i * 0.15) * 30 + rand(0, 15), 1),
            'h2' => round(80 + cos($i * 0.12) * 25 + rand(0, 10), 1),
            'ch4' => round(120 + sin($i * 0.09) * 35 + rand(0, 20), 1),
            'smoke' => round(50 + rand(0, 20), 1),
            'odor' => round(60 + sin($i * 0.2) * 20 + rand(0, 10), 1),
            'spo40' => round(90 + cos($i * 0.11) * 30 + rand(0, 15), 1),
            'co2' => round(400 + sin($i * 0.07) * 50 + rand(0, 25), 1),
            'nh3' => round(60 + cos($i * 0.13) * 20 + rand(0, 10), 1),
            'temperature' => round(16 + sin($i * 0.05) * 3 + rand(0, 10) / 10, 1),
            'humidity' => round(74 + cos($i * 0.06) * 5 + rand(0, 20) / 10, 1),
            'soil_moisture' => round(38 + sin($i * 0.04) * 5, 1),
            'ph' => round(6.5 + sin($i * 0.03) * 0.5, 2),
        ];
    }

    return $points;
}
