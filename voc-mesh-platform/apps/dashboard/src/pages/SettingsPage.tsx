import { useState } from 'react';
import clsx from 'clsx';
import { useTenantStore, useFeatureFlag } from '../store/tenant';

interface ThresholdConfig {
  compound: string;
  label: string;
  min: number;
  max: number;
  step: number;
  unit: string;
  value: number;
}

const DEFAULT_THRESHOLDS: ThresholdConfig[] = [
  { compound: 'tvoc', label: 'Total VOC', min: 0, max: 2000, step: 10, unit: 'ppb', value: 500 },
  { compound: 'co', label: 'Carbon Monoxide', min: 0, max: 500, step: 5, unit: 'ppm', value: 100 },
  { compound: 'h2', label: 'Hydrogen', min: 0, max: 1000, step: 10, unit: 'ppb', value: 200 },
  { compound: 'ch4', label: 'Methane', min: 0, max: 5000, step: 50, unit: 'ppm', value: 1000 },
  { compound: 'ammonia', label: 'Ammonia', min: 0, max: 500, step: 5, unit: 'ppb', value: 100 },
  { compound: 'ethanol', label: 'Ethanol', min: 0, max: 1000, step: 10, unit: 'ppb', value: 300 },
  { compound: 'co2', label: 'Carbon Dioxide', min: 0, max: 5000, step: 50, unit: 'ppm', value: 2000 },
  { compound: 'o2', label: 'Oxygen (low)', min: 0, max: 25, step: 0.5, unit: '%', value: 18 },
];

const SAMPLING_RATES = [
  { label: '5 seconds', value: 5 },
  { label: '10 seconds', value: 10 },
  { label: '30 seconds', value: 30 },
  { label: '1 minute', value: 60 },
  { label: '5 minutes', value: 300 },
];

const FEATURE_FLAGS = [
  { key: 'crop_stress_detection', label: 'Crop Stress Detection' },
  { key: 'bloom_prediction', label: 'Bloom Prediction' },
  { key: 'pest_detection', label: 'Pest Detection' },
  { key: 'carbon_sequestration', label: 'Carbon Sequestration' },
  { key: 'crop_metabolism_monitor', label: 'Crop Metabolism Monitor' },
  { key: 'fire_humidity_detection', label: 'Fire & Humidity Detection' },
  { key: 'aerosol_organic_tracking', label: 'Aerosol Organic Tracking' },
  { key: 'api_access', label: 'API Access' },
  { key: 'white_label', label: 'White Label' },
  { key: 'custom_ml_models', label: 'Custom ML Models' },
];

export default function SettingsPage() {
  const tenant = useTenantStore((s) => s.tenant);
  const isAdmin = useFeatureFlag('api_access');
  const [thresholds, setThresholds] = useState<ThresholdConfig[]>(DEFAULT_THRESHOLDS);
  const [samplingRate, setSamplingRate] = useState(30);
  const [featureFlags, setFeatureFlags] = useState<Record<string, boolean>>(
    tenant?.feature_flags ?? {},
  );
  const [saved, setSaved] = useState(false);

  const handleThresholdChange = (compound: string, value: number) => {
    setThresholds((prev) =>
      prev.map((t) => (t.compound === compound ? { ...t, value } : t)),
    );
  };

  const handleFeatureFlagToggle = (key: string) => {
    setFeatureFlags((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-lg text-text">Settings</h2>
        <button
          onClick={handleSave}
          className={clsx(
            'px-4 py-2 rounded-lg text-sm font-body font-medium transition-all',
            saved
              ? 'bg-voc text-space'
              : 'bg-voc/20 text-voc hover:bg-voc/30',
          )}
        >
          {saved ? 'Saved!' : 'Save Changes'}
        </button>
      </div>

      {/* Feature Flags (admin only) */}
      {isAdmin && (
        <div className="glass-panel p-4">
          <h3 className="font-display text-sm text-text mb-4">Feature Flags</h3>
          <p className="text-xs text-text-dim font-body mb-4">
            Toggle features for this tenant. Changes take effect immediately.
          </p>
          <div className="space-y-3">
            {FEATURE_FLAGS.map((flag) => (
              <div
                key={flag.key}
                className="flex items-center justify-between py-2 border-b border-white/5 last:border-0"
              >
                <div>
                  <div className="text-sm text-text font-body">{flag.label}</div>
                  <div className="text-[10px] text-text-dim font-display">{flag.key}</div>
                </div>
                <button
                  onClick={() => handleFeatureFlagToggle(flag.key)}
                  className={clsx(
                    'relative w-10 h-5 rounded-full transition-colors',
                    featureFlags[flag.key] ? 'bg-voc' : 'bg-space-50',
                  )}
                >
                  <div
                    className={clsx(
                      'absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform',
                      featureFlags[flag.key] ? 'translate-x-5' : 'translate-x-0.5',
                    )}
                  />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Alert Thresholds */}
      <div className="glass-panel p-4">
        <h3 className="font-display text-sm text-text mb-4">Alert Thresholds</h3>
        <p className="text-xs text-text-dim font-body mb-4">
          Set alert trigger levels per compound. Readings exceeding these values will generate alerts.
        </p>
        <div className="space-y-4">
          {thresholds.map((threshold) => (
            <div key={threshold.compound} className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-sm text-text-muted font-body">{threshold.label}</label>
                <span className="font-display text-xs text-voc">
                  {threshold.value} {threshold.unit}
                </span>
              </div>
              <input
                type="range"
                min={threshold.min}
                max={threshold.max}
                step={threshold.step}
                value={threshold.value}
                onChange={(e) =>
                  handleThresholdChange(threshold.compound, Number(e.target.value))
                }
                className="w-full h-1.5 bg-space-50 rounded-full appearance-none cursor-pointer
                  [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:h-3.5
                  [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-voc [&::-webkit-slider-thumb]:cursor-pointer
                  [&::-moz-range-thumb]:w-3.5 [&::-moz-range-thumb]:h-3.5 [&::-moz-range-thumb]:rounded-full
                  [&::-moz-range-thumb]:bg-voc [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-text-dim">
                <span>{threshold.min} {threshold.unit}</span>
                <span>{threshold.max} {threshold.unit}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Sampling Rate */}
      <div className="glass-panel p-4">
        <h3 className="font-display text-sm text-text mb-4">Sensor Sampling Rate</h3>
        <p className="text-xs text-text-dim font-body mb-4">
          Configure how frequently sensors transmit readings. Lower intervals increase data resolution but consume more bandwidth and storage.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          {SAMPLING_RATES.map((rate) => (
            <button
              key={rate.value}
              onClick={() => setSamplingRate(rate.value)}
              className={clsx(
                'px-3 py-2 rounded-lg text-xs font-body transition-colors border',
                samplingRate === rate.value
                  ? 'border-voc bg-voc/10 text-voc'
                  : 'border-white/5 text-text-muted hover:border-white/10 hover:bg-white/[0.02]',
              )}
            >
              {rate.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tenant Info */}
      <div className="glass-panel p-4">
        <h3 className="font-display text-sm text-text mb-4">Tenant Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm font-body">
          <div>
            <div className="text-text-dim text-xs mb-1">Tenant ID</div>
            <div className="text-text font-display text-xs">{tenant?.id}</div>
          </div>
          <div>
            <div className="text-text-dim text-xs mb-1">Slug</div>
            <div className="text-text">{tenant?.slug}</div>
          </div>
          <div>
            <div className="text-text-dim text-xs mb-1">Name</div>
            <div className="text-text">{tenant?.name}</div>
          </div>
          <div>
            <div className="text-text-dim text-xs mb-1">Tier</div>
            <div className="text-text capitalize">{tenant?.tier}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
