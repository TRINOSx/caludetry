import { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, GeoJSON, useMap } from 'react-leaflet';
import L from 'leaflet';
import type { SensorData, Parcela } from '../store/api';

const DARK_TILES = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const DARK_TILES_ATTR =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>';

function createSensorIcon(status: string, type: string): L.DivIcon {
  const color =
    status === 'online'
      ? '#00FF9C'
      : status === 'offline'
        ? '#FF3B30'
        : '#FFD93D';

  const shape = type === 'voc' ? 'rounded-full' : 'rounded-sm';

  return L.divIcon({
    className: 'custom-marker',
    html: `<div class="w-4 h-4 ${shape} border-2 flex items-center justify-center" style="border-color: ${color}; background: ${color}33;">
      <div class="w-1.5 h-1.5 rounded-full" style="background: ${color};"></div>
    </div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
    popupAnchor: [0, -10],
  });
}

function MapAutoFit({ sensors }: { sensors: SensorData[] }) {
  const map = useMap();

  useEffect(() => {
    if (sensors.length > 0) {
      const bounds = L.latLngBounds(sensors.map((s) => [s.lat, s.lng]));
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [sensors, map]);

  return null;
}

interface SensorMeshMapProps {
  sensors: SensorData[];
  parcelas: Parcela[];
  center?: [number, number];
  zoom?: number;
  className?: string;
}

export default function SensorMeshMap({
  sensors,
  parcelas,
  center = [40.0, -3.7],
  zoom = 10,
  className,
}: SensorMeshMapProps) {
  const parcelasWithBoundary = parcelas.filter((p) => p.boundary_geojson);

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      className={className ?? 'h-[400px] w-full rounded-lg'}
      style={{ background: '#0A0F1E' }}
    >
      <TileLayer url={DARK_TILES} attribution={DARK_TILES_ATTR} />

      <MapAutoFit sensors={sensors} />

      {/* Parcela boundaries */}
      {parcelasWithBoundary.map((parcela) => (
        <GeoJSON
          key={parcela.id}
          data={parcela.boundary_geojson as GeoJSON.GeoJsonObject}
          style={{
            color: '#00FF9C',
            weight: 1.5,
            opacity: 0.4,
            fillColor: '#00FF9C',
            fillOpacity: 0.05,
          }}
        />
      ))}

      {/* Sensor markers */}
      {sensors.map((sensor) => (
        <Marker
          key={sensor.id}
          position={[sensor.lat, sensor.lng]}
          icon={createSensorIcon(sensor.status, sensor.type)}
        >
          <Popup className="dark-popup">
            <div className="bg-space-100 text-text p-2 rounded min-w-[180px]">
              <div className="font-display text-xs text-voc mb-1">{sensor.hardware_id}</div>
              <div className="space-y-1 text-[11px] font-body">
                <div className="flex justify-between">
                  <span className="text-text-dim">Status:</span>
                  <span
                    className={
                      sensor.status === 'online'
                        ? 'text-voc'
                        : sensor.status === 'offline'
                          ? 'text-alert'
                          : 'text-yellow-400'
                    }
                  >
                    {sensor.status}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-dim">Type:</span>
                  <span className="text-text-muted">{sensor.type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-dim">Last seen:</span>
                  <span className="text-text-muted">
                    {new Date(sensor.last_seen).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
              </div>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
