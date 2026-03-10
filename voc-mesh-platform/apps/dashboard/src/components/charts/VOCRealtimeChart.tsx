import { useRef, useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  type ChartOptions,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import clsx from 'clsx';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

export interface VOCDataPoint {
  timestamp: string;
  tvoc: number;
  voc: number;
  co: number;
  h2: number;
  ch4: number;
}

interface VOCRealtimeChartProps {
  data: VOCDataPoint[];
  timeRange: '15m' | '1h' | '6h' | '24h';
  onTimeRangeChange: (range: '15m' | '1h' | '6h' | '24h') => void;
  compounds?: string[];
  thresholds?: Record<string, number>;
}

const COMPOUND_COLORS: Record<string, { border: string; bg: string }> = {
  tvoc: { border: '#00FF9C', bg: 'rgba(0, 255, 156, 0.1)' },
  voc: { border: '#00BFFF', bg: 'rgba(0, 191, 255, 0.1)' },
  co: { border: '#FF6B6B', bg: 'rgba(255, 107, 107, 0.1)' },
  h2: { border: '#FFD93D', bg: 'rgba(255, 217, 61, 0.1)' },
  ch4: { border: '#C084FC', bg: 'rgba(192, 132, 252, 0.1)' },
};

const TIME_RANGES = ['15m', '1h', '6h', '24h'] as const;

export default function VOCRealtimeChart({
  data,
  timeRange,
  onTimeRangeChange,
  compounds = ['tvoc', 'voc', 'co', 'h2', 'ch4'],
  thresholds = {},
}: VOCRealtimeChartProps) {
  const chartRef = useRef<ChartJS<'line'>>(null);

  const labels = useMemo(
    () =>
      data.map((d) => {
        const date = new Date(d.timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }),
    [data],
  );

  const datasets = useMemo(
    () =>
      compounds.map((compound) => ({
        label: compound.toUpperCase(),
        data: data.map((d) => d[compound as keyof VOCDataPoint] as number),
        borderColor: COMPOUND_COLORS[compound]?.border ?? '#888',
        backgroundColor: COMPOUND_COLORS[compound]?.bg ?? 'rgba(136,136,136,0.1)',
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.3,
        fill: false,
      })),
    [data, compounds],
  );

  const thresholdAnnotations = useMemo(() => {
    return Object.entries(thresholds).map(([compound, value]) => ({
      label: `${compound.toUpperCase()} Threshold`,
      data: data.map(() => value),
      borderColor: COMPOUND_COLORS[compound]?.border ?? '#888',
      borderWidth: 1,
      borderDash: [6, 4],
      pointRadius: 0,
      fill: false,
    }));
  }, [thresholds, data]);

  const chartData = {
    labels,
    datasets: [...datasets, ...thresholdAnnotations],
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: '#8B95A5',
          font: { family: 'IBM Plex Sans', size: 11 },
          boxWidth: 12,
          padding: 12,
          filter: (item) => !item.text.includes('Threshold'),
        },
      },
      tooltip: {
        backgroundColor: '#1A2332',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        titleColor: '#E8EDF2',
        bodyColor: '#8B95A5',
        titleFont: { family: 'Space Mono', size: 12 },
        bodyFont: { family: 'IBM Plex Sans', size: 11 },
        padding: 10,
      },
    },
    scales: {
      x: {
        grid: { color: 'rgba(255,255,255,0.04)' },
        ticks: { color: '#5A6577', font: { family: 'IBM Plex Sans', size: 10 }, maxTicksLimit: 8 },
      },
      y: {
        grid: { color: 'rgba(255,255,255,0.04)' },
        ticks: { color: '#5A6577', font: { family: 'IBM Plex Sans', size: 10 } },
      },
    },
  };

  return (
    <div className="glass-panel p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-display text-sm text-text">VOC Realtime</h3>
        <div className="flex gap-1">
          {TIME_RANGES.map((range) => (
            <button
              key={range}
              onClick={() => onTimeRangeChange(range)}
              className={clsx(
                'px-2.5 py-1 text-xs font-body rounded transition-colors',
                timeRange === range
                  ? 'bg-voc/20 text-voc'
                  : 'text-text-dim hover:text-text-muted hover:bg-white/5',
              )}
            >
              {range}
            </button>
          ))}
        </div>
      </div>
      <div className="h-64">
        <Line ref={chartRef} data={chartData} options={options} />
      </div>
    </div>
  );
}
