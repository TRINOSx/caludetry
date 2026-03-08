<?php
/**
 * VOC Field Intelligence - VOC Readings API
 * Returns detailed VOC compound readings
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

require_once __DIR__ . '/../config/database.php';

$parcel_id = $_GET['parcel_id'] ?? 'P1';
$range = $_GET['range'] ?? '1h';

try {
    $db = Database::connect();

    $range_map = ['1h' => '1 HOUR', '6h' => '6 HOURS', '24h' => '24 HOURS', '7d' => '7 DAYS'];
    $sql_range = $range_map[$range] ?? '1 HOUR';

    // Get VOC profile data
    $stmt = $db->prepare("
        SELECT compound, AVG(value) as avg_value, MAX(value) as max_value,
               MIN(value) as min_value, COUNT(*) as samples
        FROM voc_profile
        WHERE parcel_id = :parcel_id
          AND time >= NOW() - INTERVAL $sql_range
        GROUP BY compound
        ORDER BY avg_value DESC
    ");
    $stmt->execute(['parcel_id' => $parcel_id]);
    $compounds = $stmt->fetchAll(PDO::FETCH_ASSOC);

    echo json_encode([
        'status' => 'ok',
        'parcel_id' => $parcel_id,
        'range' => $range,
        'compounds' => $compounds,
    ]);

} catch (Exception $e) {
    // Simulated VOC readings
    $compounds = [];
    $voc_list = [
        'VOC', 'TVOC', 'CO', 'CO2', 'NO2', 'C2H5OH', 'H2', 'NH3', 'CH4',
        'HCHO', 'O3', 'H2S', 'C2H4', 'C6H6', 'C7H8', 'C8H10', 'C8H8',
        'CS2', 'C2H6S2', 'CH3OH', 'C3H8', 'C4H10',
    ];

    foreach ($voc_list as $voc) {
        $avg = rand(10, 500);
        $compounds[] = [
            'compound' => $voc,
            'avg_value' => $avg,
            'max_value' => $avg + rand(50, 200),
            'min_value' => max(0, $avg - rand(30, 100)),
            'samples' => rand(50, 200),
        ];
    }

    echo json_encode([
        'status' => 'simulated',
        'parcel_id' => $parcel_id,
        'range' => $range,
        'compounds' => $compounds,
    ]);
}
