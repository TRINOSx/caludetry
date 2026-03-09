import { useMemo } from 'react';
import clsx from 'clsx';
import { LineChart, Line, ResponsiveContainer } from 'recharts';

interface MetaboliteData {
  label: string;
  key: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  trendPercent: number;
  sparkline: number[];
  color: string;
}

interface MetabolismPanelProps {
  data: {
    o2: number;
    co2: number;
    h2: number;
    ch4: number;
    ammonia: number;
    ethanol: number;
  };
  history: Array<{
    o2: number;
    co2: number;
    h2: number;
    ch4: number;
    ammonia: number;
    ethanol: number;
  }>;
}

const METABOLITES_CONFIG: Array<{ key: string; label: string; unit: string; color: string }> = [
  { key: 'o2', label: 'O2 Generate', unit: 'ppm', color: '#00BFFF' },
  { key: 'co2', label: 'CO2 Transform', unit: 'ppm', color: '#FF6B6B' },
  { key: 'h2', label: 'Hydrogen', unit: 'ppb', color: '#FFD93D' },
  { key: 'ch4', label: 'Methane', unit: 'ppm', color: '#C084FC' },
  { key: 'ammonia', label: 'Ammonia', unit: 'ppb', color: '#F97316' },
  { key: 'ethanol', label: 'Ethanol', unit: 'ppb', color: '#00FF9C' },
];

function TrendArrow({ direction, color }: { direction: 'up' | 'down' | 'stable'; color: string }) {
  if (direction === 'stable') {
    return <span className="text-text-dim text-xs">--</span>;
  }
  return (
    <svg
      className={clsx('w-3 h-3', direction === 'down' && 'rotate-180')}
      fill={color}
      viewBox="0 0 24 24"
    >
      <path d="M12 4l-8 8h5v8h6v-8h5z" />
    </svg>
  );
}

export default function MetabolismPanel({ data, history }: MetabolismPanelProps) {
  const metabolites: MetaboliteData[] = useMemo(() => {
    return METABOLITES_CONFIG.map((config) => {
      const key = config.key as keyof typeof data;
      const currentValue = data[key];
      const sparkline = history.map((h) => h[key]);
      const prevValue = history.length > 1 ? history[history.length - 2]?.[key] ?? currentValue : currentValue;
      const trendPercent = prevValue !== 0 ? ((currentValue - prevValue) / prevValue) * 100 : 0;
      const trend: 'up' | 'down' | 'stable' =
        Math.abs(trendPercent) < 1 ? 'stable' : trendPercent > 0 ? 'up' : 'down';

      return {
        label: config.label,
        key: config.key,
        value: currentValue,
        unit: config.unit,
        trend,
        trendPercent: Math.abs(trendPercent),
        sparkline,
        color: config.color,
      };
    });
  }, [data, history]);

  return (
    <div className="glass-panel p-4">
      <h3 className="font-display text-sm text-text mb-4">Metabolism Panel</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {metabolites.map((met) => (
          <div
            key={met.key}
            className="bg-space/60 rounded-lg p-3 border border-white/5"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-body text-text-dim uppercase tracking-wider">
                {met.label}
              </span>
              <div className="flex items-center gap-1">
                <TrendArrow
                  direction={met.trend}
                  color={met.trend === 'up' ? '#FF6B6B' : met.trend === 'down' ? '#00FF9C' : '#5A6577'}
                />
                {met.trend !== 'stable' && (
                  <span
                    className={clsx(
                      'text-[10px]',
                      met.trend === 'up' ? 'text-alert' : 'text-voc',
                    )}
                  >
                    {met.trendPercent.toFixed(1)}%
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-baseline gap-1.5 mb-2">
              <span className="font-display text-xl text-text" style={{ color: met.color }}>
                {met.value.toFixed(met.unit === 'ppb' ? 0 : 1)}
              </span>
              <span className="text-[10px] text-text-dim">{met.unit}</span>
            </div>
            <div className="h-8">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={met.sparkline.map((v, i) => ({ v, i }))}>
                  <Line
                    type="monotone"
                    dataKey="v"
                    stroke={met.color}
                    strokeWidth={1.5}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
