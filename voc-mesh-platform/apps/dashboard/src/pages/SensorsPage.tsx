import { useState, useEffect } from 'react';
import clsx from 'clsx';
import SensorMeshMap from '../components/SensorMeshMap';
import { SkeletonTable } from '../components/SkeletonCard';
import { api, type SensorData, type Parcela } from '../store/api';

export default function SensorsPage() {
  const [sensors, setSensors] = useState<SensorData[]>([]);
  const [parcelas, setParcelas] = useState<Parcela[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('all');

  useEffect(() => {
    const load = async () => {
      try {
        const [sensorList, parcelaList] = await Promise.all([
          api.getSensors(),
          api.getParcelas(),
        ]);
        setSensors(sensorList);
        setParcelas(parcelaList);
      } catch {
        // handled by api client
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const filteredSensors =
    filterStatus === 'all'
      ? sensors
      : sensors.filter((s) => s.status === filterStatus);

  const onlineCount = sensors.filter((s) => s.status === 'online').length;
  const offlineCount = sensors.filter((s) => s.status === 'offline').length;
  const maintenanceCount = sensors.filter((s) => s.status === 'maintenance').length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-lg text-text">Sensor Mesh</h2>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-body">
            <div className="w-2 h-2 rounded-full bg-voc" />
            <span className="text-text-muted">{onlineCount} online</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs font-body">
            <div className="w-2 h-2 rounded-full bg-alert" />
            <span className="text-text-muted">{offlineCount} offline</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs font-body">
            <div className="w-2 h-2 rounded-full bg-yellow-400" />
            <span className="text-text-muted">{maintenanceCount} maint</span>
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="glass-panel overflow-hidden">
        {loading ? (
          <div className="h-[400px] skeleton" />
        ) : (
          <SensorMeshMap
            sensors={filteredSensors}
            parcelas={parcelas}
            className="h-[400px] w-full"
          />
        )}
      </div>

      {/* Sensor table */}
      <div className="glass-panel p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-sm text-text">All Sensors</h3>
          <div className="flex gap-1">
            {['all', 'online', 'offline', 'maintenance'].map((status) => (
              <button
                key={status}
                onClick={() => setFilterStatus(status)}
                className={clsx(
                  'px-2.5 py-1 text-xs font-body rounded capitalize transition-colors',
                  filterStatus === status
                    ? 'bg-voc/20 text-voc'
                    : 'text-text-dim hover:text-text-muted hover:bg-white/5',
                )}
              >
                {status}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <SkeletonTable rows={8} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm font-body">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="text-left py-2 px-3 text-text-dim text-xs font-medium uppercase tracking-wider">
                    Hardware ID
                  </th>
                  <th className="text-left py-2 px-3 text-text-dim text-xs font-medium uppercase tracking-wider">
                    Type
                  </th>
                  <th className="text-left py-2 px-3 text-text-dim text-xs font-medium uppercase tracking-wider">
                    Status
                  </th>
                  <th className="text-left py-2 px-3 text-text-dim text-xs font-medium uppercase tracking-wider">
                    Last Seen
                  </th>
                  <th className="text-left py-2 px-3 text-text-dim text-xs font-medium uppercase tracking-wider">
                    Location
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredSensors.map((sensor) => (
                  <tr
                    key={sensor.id}
                    className="border-b border-white/5 hover:bg-white/[0.02] transition-colors"
                  >
                    <td className="py-2.5 px-3">
                      <span className="font-display text-xs text-voc">{sensor.hardware_id}</span>
                    </td>
                    <td className="py-2.5 px-3 text-text-muted text-xs">{sensor.type}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={clsx(
                          'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium',
                          sensor.status === 'online' && 'bg-voc/10 text-voc',
                          sensor.status === 'offline' && 'bg-alert/10 text-alert',
                          sensor.status === 'maintenance' && 'bg-yellow-400/10 text-yellow-400',
                        )}
                      >
                        <div
                          className={clsx(
                            'w-1.5 h-1.5 rounded-full',
                            sensor.status === 'online' && 'bg-voc',
                            sensor.status === 'offline' && 'bg-alert',
                            sensor.status === 'maintenance' && 'bg-yellow-400',
                          )}
                        />
                        {sensor.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-text-dim text-xs">
                      {new Date(sensor.last_seen).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="py-2.5 px-3 text-text-dim text-xs font-display">
                      {sensor.lat.toFixed(4)}, {sensor.lng.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {filteredSensors.length === 0 && (
              <div className="text-center py-8 text-text-dim text-sm">
                No sensors found matching filter.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
