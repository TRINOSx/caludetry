<?php
/**
 * VOC Field Intelligence - Alerts API
 * Monitors thresholds and returns active alerts
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

require_once __DIR__ . '/../config/database.php';

try {
    $db = Database::connect();

    // Check for threshold violations in the last hour
    $alerts = [];

    // Methane alerts
    $stmt = $db->prepare("
        SELECT parcel_id, sensor_id, MAX(methane) as max_val, MAX(time) as last_time
        FROM sensor_data
        WHERE time >= NOW() - INTERVAL '1 HOUR'
          AND methane > 500
        GROUP BY parcel_id, sensor_id
    ");
    $stmt->execute();
    foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $row) {
        $alerts[] = [
            'id' => count($alerts) + 1,
            'type' => 'warning',
            'title' => 'High Methane Detected',
            'description' => "CH4 peak {$row['max_val']} ppb at {$row['sensor_id']} - soil microbiome activity",
            'timestamp' => $row['last_time'],
            'parcel' => $row['parcel_id'],
            'compound' => 'CH4',
            'value' => floatval($row['max_val']),
        ];
    }

    // NH3 alerts
    $stmt = $db->prepare("
        SELECT parcel_id, sensor_id, MAX(nh3) as max_val, MAX(time) as last_time
        FROM sensor_data
        WHERE time >= NOW() - INTERVAL '1 HOUR'
          AND nh3 > 300
        GROUP BY parcel_id, sensor_id
    ");
    $stmt->execute();
    foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $row) {
        $alerts[] = [
            'id' => count($alerts) + 1,
            'type' => 'danger',
            'title' => 'NH3 Threshold Exceeded',
            'description' => "Ammonia at {$row['max_val']} ppb - nitrogen imbalance risk",
            'timestamp' => $row['last_time'],
            'parcel' => $row['parcel_id'],
            'compound' => 'NH3',
            'value' => floatval($row['max_val']),
        ];
    }

    // TVOC alerts
    $stmt = $db->prepare("
        SELECT parcel_id, sensor_id, MAX(tvoc) as max_val, MAX(time) as last_time
        FROM sensor_data
        WHERE time >= NOW() - INTERVAL '1 HOUR'
          AND tvoc > 600
        GROUP BY parcel_id, sensor_id
    ");
    $stmt->execute();
    foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $row) {
        $alerts[] = [
            'id' => count($alerts) + 1,
            'type' => 'warning',
            'title' => 'TVOC Elevated',
            'description' => "Total VOC at {$row['max_val']} ppb - plant defense compounds active",
            'timestamp' => $row['last_time'],
            'parcel' => $row['parcel_id'],
            'compound' => 'TVOC',
            'value' => floatval($row['max_val']),
        ];
    }

    // Ethylene/ethanol alerts (root stress)
    $stmt = $db->prepare("
        SELECT parcel_id, MAX(ethanol) as max_val, MAX(time) as last_time
        FROM sensor_data
        WHERE time >= NOW() - INTERVAL '1 HOUR'
          AND ethanol > 400
        GROUP BY parcel_id
    ");
    $stmt->execute();
    foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $row) {
        $alerts[] = [
            'id' => count($alerts) + 1,
            'type' => 'danger',
            'title' => 'Root Hypoxia Risk',
            'description' => "Ethanol {$row['max_val']} ppb - possible anaerobic root conditions",
            'timestamp' => $row['last_time'],
            'parcel' => $row['parcel_id'],
            'compound' => 'C2H5OH',
            'value' => floatval($row['max_val']),
        ];
    }

    // Sort by timestamp descending
    usort($alerts, function($a, $b) {
        return strtotime($b['timestamp']) - strtotime($a['timestamp']);
    });

    echo json_encode([
        'status' => 'ok',
        'count' => count($alerts),
        'alerts' => $alerts,
    ]);

} catch (Exception $e) {
    // Simulated alerts
    echo json_encode([
        'status' => 'simulated',
        'alerts' => [
            [
                'id' => 1, 'type' => 'warning',
                'title' => 'Methane Level Rising',
                'description' => 'CH4 increased 15% in Parcela 1 - possible soil microbiome shift',
                'timestamp' => date('c', time() - 300), 'parcel' => 'P1',
            ],
            [
                'id' => 2, 'type' => 'info',
                'title' => 'Ethylene Spike Detected',
                'description' => 'C2H4 elevated in sector NE - monitoring plant stress response',
                'timestamp' => date('c', time() - 900), 'parcel' => 'P1',
            ],
            [
                'id' => 3, 'type' => 'danger',
                'title' => 'NH3 Threshold Alert',
                'description' => 'Ammonia levels approaching critical threshold in Parcela 2',
                'timestamp' => date('c', time() - 1800), 'parcel' => 'P2',
            ],
        ],
    ]);
}
