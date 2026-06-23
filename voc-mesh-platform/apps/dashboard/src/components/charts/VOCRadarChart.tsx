import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  type ChartOptions,
} from 'chart.js';
import { Radar } from 'react-chartjs-2';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

export interface RadarDataSet {
  tvoc: number;
  voc: number;
  co: number;
  h2: number;
  ch4: number;
  o2: number;
  co2: number;
  ammonia: number;
}

interface VOCRadarChartProps {
  current: RadarDataSet;
  average: RadarDataSet;
}

const LABELS = ['TVOC', 'VOC', 'CO', 'H2', 'CH4', 'O2', 'CO2', 'NH3'];
const KEYS: (keyof RadarDataSet)[] = ['tvoc', 'voc', 'co', 'h2', 'ch4', 'o2', 'co2', 'ammonia'];

export default function VOCRadarChart({ current, average }: VOCRadarChartProps) {
  const chartData = {
    labels: LABELS,
    datasets: [
      {
        label: 'Current',
        data: KEYS.map((k) => current[k]),
        borderColor: '#00FF9C',
        backgroundColor: 'rgba(0, 255, 156, 0.15)',
        borderWidth: 2,
        pointBackgroundColor: '#00FF9C',
        pointBorderColor: '#00FF9C',
        pointRadius: 3,
      },
      {
        label: '7-Day Average',
        data: KEYS.map((k) => average[k]),
        borderColor: '#5A6577',
        backgroundColor: 'rgba(90, 101, 119, 0.1)',
        borderWidth: 1,
        borderDash: [4, 4],
        pointBackgroundColor: '#5A6577',
        pointBorderColor: '#5A6577',
        pointRadius: 2,
      },
    ],
  };

  const options: ChartOptions<'radar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'bottom',
        labels: {
          color: '#8B95A5',
          font: { family: 'IBM Plex Sans', size: 11 },
          boxWidth: 10,
          padding: 12,
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
      },
    },
    scales: {
      r: {
        angleLines: { color: 'rgba(255,255,255,0.06)' },
        grid: { color: 'rgba(255,255,255,0.06)' },
        pointLabels: {
          color: '#8B95A5',
          font: { family: 'Space Mono', size: 10 },
        },
        ticks: {
          display: false,
        },
      },
    },
    animation: false,
    transitions: {
      active: { animation: { duration: 0 } },
    },
  };

  return (
    <div className="glass-panel p-3">
      <h3 className="font-display text-xs text-text mb-2">VOC Compound Profile</h3>
      <div className="h-44">
        <Radar data={chartData} options={options} />
      </div>
    </div>
  );
}
