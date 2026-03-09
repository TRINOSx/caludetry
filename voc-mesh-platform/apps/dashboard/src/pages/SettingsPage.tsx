import { useState } from 'react';
import { useTenantStore } from '../store/tenant';

export default function SettingsPage() {
  const { tenant } = useTenantStore();
  const [thresholds, setThresholds] = useState({
    methane: 500,
    nh3: 300,
    tvoc: 600,
    ethanol: 400,
    co: 500,
    stress_alert: 25,
  });
  const [sampling, setSampling] = useState({
    voc_rate: '15s',
    soil_rate: '5min',
    climate_rate: '1min',
  });
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    // POST to /api/v1/settings
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Tenant Info */}
      <div className="bg-panel rounded-lg border border-space-50 p-6">
        <h3 className="font-display text-sm text-text mb-4">Tenant Information</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-text-muted">Name</p>
            <p className="text-text font-medium">{tenant?.name || '--'}</p>
          </div>
          <div>
            <p className="text-xs text-text-muted">Slug</p>
            <p className="font-mono text-sm text-voc">{tenant?.slug || '--'}</p>
          </div>
          <div>
            <p className="text-xs text-text-muted">Tier</p>
            <p className="font-display text-voc">{tenant?.tier || '--'}</p>
          </div>
          <div>
            <p className="text-xs text-text-muted">Max Sensors</p>
            <p className="font-mono">{tenant?.max_sensors === -1 ? 'Unlimited' : tenant?.max_sensors || '--'}</p>
          </div>
        </div>
      </div>

      {/* Alert Thresholds */}
      <div className="bg-panel rounded-lg border border-space-50 p-6">
        <h3 className="font-display text-sm text-text mb-4">Alert Thresholds (ppb)</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {Object.entries(thresholds).map(([key, value]) => (
            <div key={key}>
              <label className="text-xs text-text-muted uppercase block mb-1">{key.replace('_', ' ')}</label>
              <input
                type="number"
                value={value}
                onChange={(e) => setThresholds((prev) => ({ ...prev, [key]: Number(e.target.value) }))}
                className="w-full bg-space border border-space-50 rounded-lg px-3 py-2 text-text font-mono
                           focus:border-voc focus:outline-none transition-colors"
              />
            </div>
          ))}
        </div>
      </div>

      {/* Sampling Rates */}
      <div className="bg-panel rounded-lg border border-space-50 p-6">
        <h3 className="font-display text-sm text-text mb-4">Sensor Sampling Rates</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(sampling).map(([key, value]) => (
            <div key={key}>
              <label className="text-xs text-text-muted uppercase block mb-1">{key.replace('_', ' ')}</label>
              <select
                value={value}
                onChange={(e) => setSampling((prev) => ({ ...prev, [key]: e.target.value }))}
                className="w-full bg-space border border-space-50 rounded-lg px-3 py-2 text-text font-mono
                           focus:border-voc focus:outline-none transition-colors"
              >
                <option value="5s">5 seconds</option>
                <option value="10s">10 seconds</option>
                <option value="15s">15 seconds</option>
                <option value="30s">30 seconds</option>
                <option value="1min">1 minute</option>
                <option value="5min">5 minutes</option>
                <option value="15min">15 minutes</option>
              </select>
            </div>
          ))}
        </div>
      </div>

      {/* Feature Flags (admin) */}
      <div className="bg-panel rounded-lg border border-space-50 p-6">
        <h3 className="font-display text-sm text-text mb-4">Feature Flags</h3>
        <div className="space-y-2">
          {(tenant?.feature_flags || []).map((flag: { flag_name: string; enabled: boolean }) => (
            <div key={flag.flag_name} className="flex items-center justify-between py-2 border-b border-space-50/50">
              <span className="text-sm text-text-muted">{flag.flag_name.replace(/_/g, ' ')}</span>
              <span className={`text-xs px-2 py-0.5 rounded ${
                flag.enabled ? 'bg-voc/20 text-voc' : 'bg-space text-text-dim'
              }`}>
                {flag.enabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end gap-3">
        {saved && <span className="text-voc text-sm self-center">Settings saved!</span>}
        <button
          onClick={handleSave}
          className="px-6 py-2.5 bg-voc text-space font-display text-sm rounded-lg
                     hover:bg-voc-dark transition-colors"
        >
          Save Settings
        </button>
      </div>
    </div>
  );
}
