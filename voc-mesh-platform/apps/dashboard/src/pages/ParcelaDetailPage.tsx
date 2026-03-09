import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import VOCRealtimeChart, { type VOCDataPoint } from '../components/charts/VOCRealtimeChart';
import VOCRadarChart, { type RadarDataSet } from '../components/charts/VOCRadarChart';
import MetabolismPanel from '../components/charts/MetabolismPanel';
import PredictionTimeline from '../components/charts/PredictionTimeline';
import SkeletonCard, { SkeletonChart } from '../components/SkeletonCard';
import { api, type LiveData, type Prediction, type Alert } from '../store/api';
import clsx from 'clsx';

const TIME_RANGE_HOURS: Record<string, number> = {
  '15m': 0.25,
  '1h': 1,
  '6h': 6,
  '24h': 24,
};

export default function ParcelaDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [liveData, setLiveData] = useState<LiveData | null>(null);
  const [historyData, setHistoryData] = useState<LiveData[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [timeRange, setTimeRange] = useState<'15m' | '1h' | '6h' | '24h'>('1h');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;

    const fetchData = async () => {
      try {
        const [live, history, preds, alertList] = await Promise.all([
          api.getParcelaLive(id),
          api.getParcelaHistory(id, TIME_RANGE_HOURS[timeRange]),
          api.getPredictions(id),
          api.getAlerts(id),
        ]);
        setLiveData(live);
        setHistoryData(history);
        setPredictions(preds);
        setAlerts(alertList);
      } catch {
        // handled by api client
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [id, timeRange]);

  const chartData: VOCDataPoint[] = historyData.map((d) => ({
    timestamp: d.timestamp,
    tvoc: d.tvoc,
    voc: d.voc,
    co: d.co,
    h2: d.h2,
    ch4: d.ch4,
  }));

  const currentRadar: RadarDataSet = liveData
    ? { tvoc: liveData.tvoc, voc: liveData.voc, co: liveData.co, h2: liveData.h2, ch4: liveData.ch4, o2: liveData.o2, co2: liveData.co2, ammonia: liveData.ammonia }
    : { tvoc: 0, voc: 0, co: 0, h2: 0, ch4: 0, o2: 0, co2: 0, ammonia: 0 };

  const averageRadar: RadarDataSet =
    historyData.length > 0
      ? {
          tvoc: historyData.reduce((s, d) => s + d.tvoc, 0) / historyData.length,
          voc: historyData.reduce((s, d) => s + d.voc, 0) / historyData.length,
          co: historyData.reduce((s, d) => s + d.co, 0) / historyData.length,
          h2: historyData.reduce((s, d) => s + d.h2, 0) / historyData.length,
          ch4: historyData.reduce((s, d) => s + d.ch4, 0) / historyData.length,
          o2: historyData.reduce((s, d) => s + d.o2, 0) / historyData.length,
          co2: historyData.reduce((s, d) => s + d.co2, 0) / historyData.length,
          ammonia: historyData.reduce((s, d) => s + d.ammonia, 0) / historyData.length,
        }
      : currentRadar;

  const metabolismData = liveData
    ? { o2: liveData.o2, co2: liveData.co2, h2: liveData.h2, ch4: liveData.ch4, ammonia: liveData.ammonia, ethanol: liveData.ethanol }
    : { o2: 0, co2: 0, h2: 0, ch4: 0, ammonia: 0, ethanol: 0 };

  const metabolismHistory = historyData.map((d) => ({
    o2: d.o2, co2: d.co2, h2: d.h2, ch4: d.ch4, ammonia: d.ammonia, ethanol: d.ethanol,
  }));

  if (loading) {
    return (
      <div className="space-y-6">
        <SkeletonCard lines={2} />
        <SkeletonChart />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SkeletonChart />
          <SkeletonChart />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm font-body">
        <Link to="/dashboard" className="text-text-dim hover:text-voc transition-colors">
          Dashboard
        </Link>
        <svg className="w-3 h-3 text-text-dim" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
        </svg>
        <span className="text-text">Parcela Detail</span>
      </div>

      {/* Live environment stats */}
      {liveData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="glass-panel p-3">
            <div className="text-[10px] text-text-dim uppercase tracking-wider font-body">Temperature</div>
            <div className="font-display text-lg text-text">{liveData.temperature.toFixed(1)}<span className="text-xs text-text-dim">C</span></div>
          </div>
          <div className="glass-panel p-3">
            <div className="text-[10px] text-text-dim uppercase tracking-wider font-body">Humidity</div>
            <div className="font-display text-lg text-text">{liveData.humidity.toFixed(1)}<span className="text-xs text-text-dim">%</span></div>
          </div>
          <div className="glass-panel p-3">
            <div className="text-[10px] text-text-dim uppercase tracking-wider font-body">Soil Moisture</div>
            <div className="font-display text-lg text-text">{liveData.soil_moisture.toFixed(1)}<span className="text-xs text-text-dim">%</span></div>
          </div>
          <div className="glass-panel p-3">
            <div className="text-[10px] text-text-dim uppercase tracking-wider font-body">Fire Alert</div>
            <div className={clsx('font-display text-lg', liveData.fire_alert ? 'text-alert animate-pulse-fast' : 'text-voc')}>
              {liveData.fire_alert ? 'ACTIVE' : 'Clear'}
            </div>
          </div>
        </div>
      )}

      {/* Full VOC chart with all compounds */}
      <VOCRealtimeChart
        data={chartData}
        timeRange={timeRange}
        onTimeRangeChange={setTimeRange}
        compounds={['tvoc', 'voc', 'co', 'h2', 'ch4']}
        thresholds={{ tvoc: 500, co: 100 }}
      />

      {/* Prediction timeline */}
      <PredictionTimeline predictions={predictions} />

      {/* Radar + Metabolism */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <VOCRadarChart current={currentRadar} average={averageRadar} />
        <MetabolismPanel data={metabolismData} history={metabolismHistory} />
      </div>

      {/* Alert history for this parcela */}
      <div className="glass-panel p-4">
        <h3 className="font-display text-sm text-text mb-4">Alert History</h3>
        {alerts.length > 0 ? (
          <div className="space-y-2">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={clsx(
                  'flex items-center gap-3 bg-space/60 rounded-lg px-3 py-2.5 border border-white/5',
                  alert.resolved && 'opacity-50',
                )}
              >
                <div
                  className={clsx(
                    'w-2 h-2 rounded-full flex-shrink-0',
                    alert.severity === 'critical' && 'bg-alert',
                    alert.severity === 'high' && 'bg-orange-500',
                    alert.severity === 'medium' && 'bg-yellow-400',
                    alert.severity === 'low' && 'bg-voc',
                  )}
                />
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-text font-body truncate">{alert.message}</div>
                  <div className="text-[10px] text-text-dim font-body">
                    {alert.type} &middot;{' '}
                    {new Date(alert.created_at).toLocaleString([], {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                </div>
                <span
                  className={clsx(
                    'text-[10px] px-2 py-0.5 rounded-full font-body',
                    alert.resolved
                      ? 'bg-voc/10 text-voc'
                      : 'bg-alert/10 text-alert',
                  )}
                >
                  {alert.resolved ? 'Resolved' : 'Active'}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-text-dim text-sm font-body">
            No alerts recorded for this parcela.
          </div>
        )}
      </div>
    </div>
  );
}
