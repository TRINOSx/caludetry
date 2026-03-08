<?php
/**
 * VOC Field Intelligence - AlphaEarth Integration API
 * Geospatial embedding and regional analysis
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$lat = floatval($_GET['lat'] ?? 20.6597);
$lon = floatval($_GET['lon'] ?? -103.3496);
$parcel_id = $_GET['parcel_id'] ?? 'P1';

try {
    // In production, this would call AlphaEarth API or local model
    // For now, generate geospatial embedding based on coordinates

    $embedding = generate_geo_embedding($lat, $lon);
    $analysis = analyze_geospatial($lat, $lon, $parcel_id);

    echo json_encode([
        'status' => 'ok',
        'coordinates' => ['lat' => $lat, 'lon' => $lon],
        'embedding' => $embedding,
        'embedding_dim' => count($embedding),
        'geo_score' => $analysis['geo_score'],
        'soil_health' => $analysis['soil_health'],
        'ndvi' => $analysis['ndvi'],
        'ndwi' => $analysis['ndwi'],
        'evi' => $analysis['evi'],
        'land_use_history' => $analysis['land_use_history'],
        'regional_risk' => $analysis['regional_risk'],
        'similar_parcels' => $analysis['similar_parcels'],
        'climate_zone' => $analysis['climate_zone'],
        'soil_type' => $analysis['soil_type'],
        'elevation_m' => $analysis['elevation'],
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}

/**
 * Generate geospatial embedding vector
 * In production: AlphaEarth model inference
 */
function generate_geo_embedding($lat, $lon) {
    $dim = 64; // Reduced from 512 for demo
    $embedding = [];

    // Deterministic pseudo-random based on coordinates
    $seed = intval(($lat * 1000 + $lon * 1000) % 10000);
    mt_srand($seed);

    for ($i = 0; $i < $dim; $i++) {
        // Fourier features of coordinates
        $freq = ($i + 1) * 0.1;
        $val = sin($lat * $freq) * cos($lon * $freq) + (mt_rand() / mt_getrandmax() - 0.5) * 0.1;
        $embedding[] = round($val, 4);
    }

    return $embedding;
}

/**
 * Geospatial analysis based on location
 */
function analyze_geospatial($lat, $lon, $parcel_id) {
    // Determine climate zone from latitude
    $abs_lat = abs($lat);
    if ($abs_lat < 23.5) $climate = 'Tropical';
    elseif ($abs_lat < 35) $climate = 'Subtropical';
    elseif ($abs_lat < 55) $climate = 'Temperate';
    else $climate = 'Continental';

    // Simulated NDVI from location
    $ndvi = round(0.6 + sin($lat * 0.1) * 0.15 + cos($lon * 0.05) * 0.1, 2);
    $ndvi = max(0.1, min(0.95, $ndvi));

    return [
        'geo_score' => round(70 + $ndvi * 30, 0),
        'soil_health' => round(60 + $ndvi * 35, 0),
        'ndvi' => $ndvi,
        'ndwi' => round($ndvi * 0.55, 2),
        'evi' => round($ndvi * 0.87, 2),
        'land_use_history' => 'Agricultural - Corn/Wheat rotation since 2018',
        'regional_risk' => $ndvi > 0.7 ? 'Low' : ($ndvi > 0.5 ? 'Medium' : 'High'),
        'similar_parcels' => rand(800, 2000),
        'climate_zone' => $climate,
        'soil_type' => 'Vertisol - Clay rich',
        'elevation' => round(1500 + sin($lat) * 300, 0),
    ];
}
