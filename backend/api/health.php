<?php
/**
 * Health check endpoint
 */
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

echo json_encode([
    'status' => 'ok',
    'service' => 'VOC Field Intelligence',
    'version' => '1.0.0',
    'timestamp' => date('c'),
    'php_version' => phpversion(),
]);
