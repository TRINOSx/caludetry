import { useState, useEffect } from 'react';
import clsx from 'clsx';
import { useNavigate } from 'react-router-dom';
import VOCRealtimeChart, { type VOCDataPoint } from '../components/charts/VOCRealtimeChart';
import VOCRadarChart, { type RadarDataSet } from '../components/charts/VOCRadarChart';
import MetabolismPanel from '../components/charts/MetabolismPanel';
import PredictionTimeline from '../components/charts/PredictionTimeline';
import SkeletonCard, { SkeletonChart } from '../components/SkeletonCard';
import { api, type Parcela, type LiveData, type Prediction, type Alert } from '../store/api';

function ParcelaCard({ parcela, onClick }: { parcela: Parcela; onClick: () => void }) {
  const borderColor =
    parcela.stress_index > 0.7
      ? 'border-alert'
      : parcela.pest_risk > 0.5
        ? 'border-orange-500'
        : parcela.bloom_index > 0.6
          ? 'border-voc'
          : 'border-white/10';

  return (
    <button
      onClick={onClick}
      className={clsx(
        'glass-panel p-4 text-left w-full border transition-all hover:border-voc/30',
        borderColor,
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-display text-sm text-text truncate">{parcela.name}</h4>
        <span className="text-[10px] bg-space-50 px-2 py-0.5 rounded text-text-muted font-body">
          {parcela.crop_type}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <MetricBadge label="Stress" value={parcela.stress_index} colorHigh />
        <MetricBadge label="Bloom" value={parcela.bloom_index} />
        <MetricBadge label="Pest" value={parcela.pest_risk} colorHigh />
        <MetricBadge label="Carbon" value={parcela.carbon_flux} unit="g/m2" />
      </div>
      <div className="mt-3 flex items-center gap-2 text-[10px] text-text-dim">
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.288 15.038a5.25 5.25 0 0 1 7.424 0M5.106 11.856c3.807-3.808 9.98-3.808 13.788 0M12.53 18.22l-.53.53-.53-.53a.75.75 0 0 1 1.06 0Z" />
        </svg>
        <span>{parcela.sensor_count} sensors</span>
        <span className="text-text-dim/50">|</span>
        <span>{parcela.area_km2.toFixed(2)} km2</span>
      </div>
    </button>
  );
}

function MetricBadge({
  label,
  value,
  unit,
  colorHigh,
}: {
  label: string;
  value: number;
  unit?: string;
  colorHigh?: boolean;
}) {
  const displayValue = unit ? value.toFixed(1) : (value * 100).toFixed(0) + '%';
  const color = colorHigh
    ? value > 0.7
      ? 'text-alert'
      : value > 0.4
        ? 'text-orange-400'
        : 'text-voc'
    : 'text-voc';

  return (
    <div className="bg-space/60 rounded px-2 py-1.5">
      <div className="text-[9px] text-text-dim uppercase tracking-wider">{label}</div>
      <div className={clsx('font-display text-sm', color)}>
        {displayValue}
        {unit && <span className="text-[9px] text-text-dim ml-0.5">{unit}</span>}
      </div>
    </div>
  );
}

function GlobalAlertBar({ active }: { active: boolean }) {
  if (!active) return null;
  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-alert/90 backdrop-blur-sm px-4 py-2 flex items-center justify-center gap-2 animate-pulse-fast alert-glow">
      <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.362 5.214A8.252 8.252 0 0 1 12 21 8.25 8.25 0 0 1 6.038 7.047 8.287 8.287 0 0 0 9 9.601a8.983 8.983 0 0 1 3.361-6.867 8.21 8.21 0 0 0 3 2.48Z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 18a3.75 3.75 0 0 0 .495-7.468 5.99 5.99 0 0 0-1.925 3.547 5.975 5.975 0 0 1-2.133-1.001A3.75 3.75 0 0 0 12 18Z" />
      </svg>
      <span className="text-white font-display text-sm font-bold">FIRE ALERT DETECTED</span>
      <span className="text-white/80 font-body text-xs">Immediate action required</span>
    </div>
  );
}

const TIME_RANGE_HOURS: Record<string, number> = {
  '15m': 0.25,
  '1h': 1,
  '6h': 6,
  '24h': 24,
};

export default function DashboardPage() {
  const [parcelas, setParcelas] = useState<Parcela[]>([]);
  const [liveData, setLiveData] = useState<LiveData | null>(null);
  const [historyData, setHistoryData] = useState<LiveData[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [timeRange, setTimeRange] = useState<'15m' | '1h' | '6h' | '24h'>('1h');
  const [loading, setLoading] = useState(true);
  const [activeParcela, setActiveParcela] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const load = async () => {
      try {
        const [parcelaList, alertList] = await Promise.all([
          api.getParcelas(),
          api.getAlerts(),
        ]);
        setParcelas(parcelaList);
        setAlerts(alertList);
        if (parcelaList.length > 0) {
          setActiveParcela(parcelaList[0].id);
        }
      } catch {
        // handled by api client
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  useEffect(() => {
    if (!activeParcela) return;

    const fetchLive = async () => {
      try {
        const [live, history, preds] = await Promise.all([
          api.getParcelaLive(activeParcela),
          api.getParcelaHistory(activeParcela, TIME_RANGE_HOURS[timeRange]),
          api.getPredictions(activeParcela),
        ]);
        setLiveData(live);
        setHistoryData(history);
        setPredictions(preds);
      } catch {
        // handled by api client
      }
    };

    fetchLive();
    const interval = setInterval(fetchLive, 5000);
    return () => clearInterval(interval);
  }, [activeParcela, timeRange]);

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

  const fireAlert = liveData?.fire_alert ?? false;

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <SkeletonCard key={i} lines={4} />
          ))}
        </div>
        <SkeletonChart />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SkeletonChart />
          <SkeletonChart />
        </div>
      </div>
    );
  }

  return (
    <div className={clsx('space-y-6', fireAlert && 'pt-10')}>
      <GlobalAlertBar active={fireAlert} />

      <div>
        <h2 className="font-display text-lg text-text mb-3">Parcelas</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {parcelas.map((parcela) => (
            <ParcelaCard
              key={parcela.id}
              parcela={parcela}
              onClick={() => navigate(`/parcela/${parcela.id}`)}
            />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <VOCRealtimeChart
          data={chartData}
          timeRange={timeRange}
          onTimeRangeChange={setTimeRange}
          thresholds={{ tvoc: 500, co: 100 }}
        />
        <VOCRadarChart current={currentRadar} average={averageRadar} />
      </div>

      <PredictionTimeline predictions={predictions} />

      <MetabolismPanel data={metabolismData} history={metabolismHistory} />

      {alerts.filter((a) => !a.resolved).length > 0 && (
        <div className="glass-panel p-4">
          <h3 className="font-display text-sm text-text mb-3">Active Alerts</h3>
          <div className="space-y-2">
            {alerts
              .filter((a) => !a.resolved)
              .slice(0, 5)
              .map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-center gap-3 bg-space/60 rounded-lg px-3 py-2 border border-white/5"
                >
                  <div
                    className={clsx(
                      'w-2 h-2 rounded-full flex-shrink-0',
                      alert.severity === 'critical' && 'bg-alert animate-pulse-fast',
                      alert.severity === 'high' && 'bg-orange-500',
                      alert.severity === 'medium' && 'bg-yellow-400',
                      alert.severity === 'low' && 'bg-voc',
                    )}
                  />
                  <span className="text-sm text-text font-body flex-1 truncate">{alert.message}</span>
                  <span className="text-[10px] text-text-dim font-body">
                    {new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
