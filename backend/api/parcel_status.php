<?php
/**
 * VOC Field Intelligence - Parcel Status API
 * Returns current plant state: stress, metabolism, plagues, flowering
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

require_once __DIR__ . '/../config/database.php';

$parcel_id = $_GET['parcel_id'] ?? 'P1';

try {
    $db = Database::connect();

    // Get latest sensor averages (last 30 minutes)
    $stmt = $db->prepare("
        SELECT
            AVG(co2) as avg_co2,
            AVG(nh3) as avg_nh3,
            AVG(methane) as avg_methane,
            AVG(ethanol) as avg_ethanol,
            AVG(tvoc) as avg_tvoc,
            AVG(humidity) as avg_humidity,
            AVG(temperature) as avg_temperature,
            AVG(hydrogen) as avg_h2,
            AVG(carbon_monoxide) as avg_co,
            AVG(formaldehyde) as avg_formaldehyde,
            AVG(ozone) as avg_ozone,
            MAX(tvoc) as max_tvoc,
            MIN(temperature) as min_temp,
            MAX(temperature) as max_temp,
            COUNT(*) as sample_count
        FROM sensor_data
        WHERE parcel_id = :parcel_id
          AND time >= NOW() - INTERVAL '30 MINUTES'
    ");

    $stmt->execute(['parcel_id' => $parcel_id]);
    $averages = $stmt->fetch(PDO::FETCH_ASSOC);

    // Calculate plant status from sensor data
    $status = calculate_plant_status($averages);

    echo json_encode([
        'status' => 'ok',
        'parcel_id' => $parcel_id,
        'timestamp' => date('c'),
        'sample_count' => intval($averages['sample_count'] ?? 0),
        'stress' => $status['stress'],
        'floration' => $status['floration'],
        'plagues' => $status['plagues'],
        'metabolism' => $status['metabolism'],
        'oxygen_generate' => $status['oxygen_generate'],
        'co2_transformate' => $status['co2_transformate'],
        'sensor_averages' => $averages,
    ]);

} catch (Exception $e) {
    // Simulated response
    echo json_encode([
        'status' => 'simulated',
        'parcel_id' => $parcel_id,
        'timestamp' => date('c'),
        'stress' => 10.0,
        'floration' => 1.0,
        'plagues' => 0.5,
        'metabolism' => 80.0,
        'oxygen_generate' => 500,
        'co2_transformate' => 200,
    ]);
}

function calculate_plant_status($data) {
    if (!$data || empty($data['sample_count'])) {
        return [
            'stress' => 10.0,
            'floration' => 1.0,
            'plagues' => 0.0,
            'metabolism' => 80.0,
            'oxygen_generate' => 500,
            'co2_transformate' => 200,
        ];
    }

    $stress = 5.0; // Base stress
    $plague_risk = 0.0;
    $metabolism = 85.0;

    // Stress factors
    $tvoc = floatval($data['avg_tvoc'] ?? 0);
    $nh3 = floatval($data['avg_nh3'] ?? 0);
    $methane = floatval($data['avg_methane'] ?? 0);
    $ethanol = floatval($data['avg_ethanol'] ?? 0);
    $co = floatval($data['avg_co'] ?? 0);
    $temp = floatval($data['avg_temperature'] ?? 20);

    // TVOC stress contribution
    if ($tvoc > 400) $stress += ($tvoc - 400) * 0.05;
    if ($tvoc > 700) $stress += ($tvoc - 700) * 0.1;

    // NH3 stress
    if ($nh3 > 200) $stress += ($nh3 - 200) * 0.03;

    // Temperature stress (optimal 15-30 C)
    if ($temp < 10) $stress += (10 - $temp) * 2;
    if ($temp > 35) $stress += ($temp - 35) * 3;

    // Ethanol = possible hypoxia
    if ($ethanol > 300) $stress += ($ethanol - 300) * 0.04;

    // Plague risk from VOC pattern
    if ($tvoc > 500 && $ethanol > 200) $plague_risk += 5;
    if ($methane > 400 && $nh3 > 200) $plague_risk += 3;

    // Metabolism decreases with stress
    $metabolism = max(20, 85 - $stress * 0.5);

    // CO2 transformation estimate (simplified)
    $co2_transform = max(50, 200 - $stress * 2);
    $o2_generate = max(100, 500 - $stress * 5);

    return [
        'stress' => round(min(100, $stress), 1),
        'floration' => round(max(0, 5 - $stress * 0.1), 1),
        'plagues' => round(min(100, $plague_risk), 1),
        'metabolism' => round($metabolism, 1),
        'oxygen_generate' => round($o2_generate),
        'co2_transformate' => round($co2_transform),
    ];
}
