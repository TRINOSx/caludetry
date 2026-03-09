import { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api, type ParcelaLiveData } from '../store/api';
import VOCRealtimeChart from '../components/charts/VOCRealtimeChart';
import MetabolismPanel from '../components/charts/MetabolismPanel';
import SkeletonCard from '../components/SkeletonCard';

export default function ParcelaDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [liveData, setLiveData] = useState<ParcelaLiveData | null>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    if (!id) return;
    try {
      const [live, alertData] = await Promise.all([
        api.getParcelaLive(id),
        api.getAlerts(),
      ]);
      setLiveData(live);
      setAlerts(alertData.filter((a: any) => a.parcela_id === id));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading) {
    return (
      <div className="space-y-4">
        <SkeletonCard className="h-20" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SkeletonCard className="h-80" />
          <SkeletonCard className="h-80" />
        </div>
      </div>
    );
  }

  const parcela = liveData?.parcela;
  const prediction = liveData?.prediction;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-panel rounded-lg border border-space-50 p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <Link to="/dashboard" className="text-text-muted hover:text-voc transition-colors">← Back</Link>
              <h2 className="font-display text-xl text-text">{parcela?.name || 'Parcela'}</h2>
            </div>
            <p className="text-sm text-text-muted mt-1">
              {parcela?.crop_type} — {parcela?.area_km2} km²
            </p>
          </div>
          <div className="grid grid-cols-4 gap-6 text-center">
            <div>
              <p className="text-xs text-text-muted">Stress</p>
              <p className={`font-display text-xl ${(prediction?.stress_pct || 0) > 20 ? 'text-alert' : 'text-voc'}`}>
                {prediction?.stress_pct?.toFixed(1) || 0}%
              </p>
            </div>
            <div>
              <p className="text-xs text-text-muted">Bloom</p>
              <p className="font-display text-xl text-purple-400">
                {((prediction?.bloom_pct || 0) * 100).toFixed(0)}%
              </p>
            </div>
            <div>
              <p className="text-xs text-text-muted">Pest</p>
              <p className="font-display text-xl">
                {prediction?.pest_zone_detected ? '🔴' : '🟢'}
              </p>
            </div>
            <div>
              <p className="text-xs text-text-muted">Carbon</p>
              <p className="font-display text-xl text-cyan-400">
                {prediction?.carbon_index?.toFixed(1) || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Full VOC Chart */}
      <div className="bg-panel rounded-lg border border-space-50 p-4">
        <h3 className="font-display text-sm text-text mb-3">Full VOC Spectrum (24h)</h3>
        <div className="h-80">
          <VOCRealtimeChart data={liveData?.readings || []} timeRange="24h" />
        </div>
      </div>

      {/* Metabolism + Climate */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <MetabolismPanel data={liveData} />

        <div className="bg-panel rounded-lg border border-space-50 p-4">
          <h3 className="font-display text-sm text-text mb-3">Soil & Climate</h3>
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: 'Temperature', value: `${liveData?.climate?.temperature?.toFixed(1) || '--'}°C`, color: 'text-orange-400' },
              { label: 'Humidity', value: `${liveData?.climate?.humidity?.toFixed(0) || '--'}%`, color: 'text-blue-400' },
              { label: 'Soil pH', value: liveData?.soil?.ph?.toFixed(1) || '--', color: 'text-green-400' },
              { label: 'Soil Moisture', value: `${liveData?.soil?.moisture?.toFixed(0) || '--'}%`, color: 'text-purple-400' },
              { label: 'Pressure', value: `${liveData?.climate?.pressure?.toFixed(0) || '--'} hPa`, color: 'text-text-muted' },
              { label: 'Wind', value: `${liveData?.climate?.wind_speed?.toFixed(0) || '--'} km/h`, color: 'text-text-muted' },
            ].map((item) => (
              <div key={item.label} className="bg-space rounded-lg p-3">
                <p className="text-xs text-text-muted">{item.label}</p>
                <p className={`font-display text-lg ${item.color}`}>{item.value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Alert History */}
      <div className="bg-panel rounded-lg border border-space-50 p-4">
        <h3 className="font-display text-sm text-text mb-3">Alert History</h3>
        {alerts.length === 0 ? (
          <p className="text-text-dim text-sm py-4 text-center">No alerts for this parcela</p>
        ) : (
          <div className="space-y-2">
            {alerts.map((alert: any) => (
              <div key={alert.id} className="flex items-center gap-3 py-2 border-b border-space-50/50">
                <span className={`w-2 h-2 rounded-full ${
                  alert.alert_type === 'danger' ? 'bg-alert' :
                  alert.alert_type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
                }`} />
                <span className="text-sm text-text flex-1">{alert.title}</span>
                <span className="text-xs font-mono text-text-dim">
                  {new Date(alert.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
