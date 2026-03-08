<?php
/**
 * VOC Field Intelligence - ML Predictions API
 * Returns predictions for +24h, +72h, +7d
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

require_once __DIR__ . '/../config/database.php';

$parcel_id = $_GET['parcel_id'] ?? 'P1';

try {
    $db = Database::connect();

    // Get historical trend (last 24h averages by hour)
    $stmt = $db->prepare("
        SELECT
            date_trunc('hour', time) as hour,
            AVG(tvoc) as tvoc,
            AVG(co2) as co2,
            AVG(nh3) as nh3,
            AVG(methane) as methane,
            AVG(temperature) as temperature,
            AVG(humidity) as humidity
        FROM sensor_data
        WHERE parcel_id = :parcel_id
          AND time >= NOW() - INTERVAL '24 HOURS'
        GROUP BY date_trunc('hour', time)
        ORDER BY hour ASC
    ");

    $stmt->execute(['parcel_id' => $parcel_id]);
    $history = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Simple trend-based prediction
    $predictions = predict_from_trend($history);

    echo json_encode([
        'status' => 'ok',
        'parcel_id' => $parcel_id,
        'model_version' => 'v2.1-rule-based',
        'confidence' => $predictions['confidence'],
        '24h' => $predictions['24h'],
        '72h' => $predictions['72h'],
        '7d' => $predictions['7d'],
        'history_points' => count($history),
    ]);

} catch (Exception $e) {
    echo json_encode([
        'status' => 'simulated',
        'parcel_id' => $parcel_id,
        'model_version' => 'v2.1-simulated',
        'confidence' => 0.75,
        '24h' => ['stress' => 12, 'plagues' => 0.5, 'metabolism' => 78, 'flowering' => 1.5],
        '72h' => ['stress' => 15, 'plagues' => 1.2, 'metabolism' => 75, 'flowering' => 2.0],
        '7d'  => ['stress' => 18, 'plagues' => 2.1, 'metabolism' => 72, 'flowering' => 3.5],
    ]);
}

function predict_from_trend($history) {
    if (count($history) < 3) {
        return [
            'confidence' => 0.5,
            '24h' => ['stress' => 12, 'plagues' => 0.5, 'metabolism' => 78, 'flowering' => 1.5],
            '72h' => ['stress' => 15, 'plagues' => 1.2, 'metabolism' => 75, 'flowering' => 2.0],
            '7d'  => ['stress' => 18, 'plagues' => 2.1, 'metabolism' => 72, 'flowering' => 3.5],
        ];
    }

    // Calculate trend (linear regression on TVOC)
    $n = count($history);
    $tvoc_values = array_column($history, 'tvoc');
    $last_tvoc = floatval(end($tvoc_values));
    $first_tvoc = floatval(reset($tvoc_values));
    $trend = ($last_tvoc - $first_tvoc) / max(1, $n);

    // Base current state
    $current_stress = 10;
    $current_metabolism = 80;

    if ($last_tvoc > 400) $current_stress += ($last_tvoc - 400) * 0.03;

    // Project forward
    $predictions = [];
    $horizons = ['24h' => 24, '72h' => 72, '7d' => 168];

    foreach ($horizons as $label => $hours) {
        $projected_tvoc = $last_tvoc + $trend * $hours;
        $stress_delta = max(0, ($projected_tvoc - 400) * 0.03);
        $stress = min(100, $current_stress + $stress_delta);
        $metabolism = max(20, $current_metabolism - $stress_delta * 0.5);

        $predictions[$label] = [
            'stress' => round($stress, 1),
            'plagues' => round(min(50, $stress * 0.15), 1),
            'metabolism' => round($metabolism, 1),
            'flowering' => round(max(0, 5 - $stress * 0.1), 1),
        ];
    }

    $predictions['confidence'] = min(0.95, 0.5 + $n * 0.02);

    return $predictions;
}
