import { useEffect, useState } from 'react';
import { api } from '../store/api';
import { useTenantStore } from '../store/tenant';

interface BillingEstimate {
  sensor_count: number;
  amount_usd: number;
  tier: string;
  period_start: string;
  period_end: string;
}

interface UsageData {
  sensors_active: number;
  km2_covered: number;
  readings_count: number;
  api_calls: number;
  insights_generated: number;
  storage_mb: number;
}

interface Invoice {
  id: string;
  period_start: string;
  period_end: string;
  amount_usd: number;
  sensor_count: number;
  paid: boolean;
}

export default function BillingPage() {
  const { tenant } = useTenantStore();
  const [estimate, setEstimate] = useState<BillingEstimate | null>(null);
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);

  useEffect(() => {
    api.getBilling().then(setEstimate).catch(() => {});
    api.getUsage().then(setUsage).catch(() => {});
    api.getInvoices().then(setInvoices).catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      {/* Tier Info */}
      <div className="bg-panel rounded-lg border border-space-50 p-6">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-xs text-text-muted uppercase">Current Plan</p>
            <p className="font-display text-2xl text-voc">{tenant?.tier || 'AGRO_BASIC'}</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-text-muted">Rate</p>
            <p className="font-display text-xl text-text">
              ${estimate?.amount_usd?.toFixed(2) || '9.00'}<span className="text-sm text-text-muted">/sensor/mo</span>
            </p>
          </div>
        </div>
      </div>

      {/* Current Month Estimate */}
      {estimate && (
        <div className="bg-panel rounded-lg border border-voc/20 p-6">
          <h3 className="font-display text-sm text-text mb-4">Current Month Estimate</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-text-muted">Active Sensors</p>
              <p className="font-display text-2xl text-voc">{estimate.sensor_count}</p>
            </div>
            <div>
              <p className="text-xs text-text-muted">Estimated Total</p>
              <p className="font-display text-2xl text-text">${estimate.amount_usd.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-xs text-text-muted">Period</p>
              <p className="font-mono text-sm text-text-muted">
                {estimate.period_start} — {estimate.period_end}
              </p>
            </div>
            <div>
              <p className="text-xs text-text-muted">Status</p>
              <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded">Accruing</span>
            </div>
          </div>
        </div>
      )}

      {/* Usage Stats */}
      {usage && (
        <div className="bg-panel rounded-lg border border-space-50 p-6">
          <h3 className="font-display text-sm text-text mb-4">Usage This Month</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div>
              <p className="text-xs text-text-muted">Sensors</p>
              <p className="font-display text-xl text-text">{usage.sensors_active}</p>
            </div>
            <div>
              <p className="text-xs text-text-muted">Area (km²)</p>
              <p className="font-display text-xl text-text">{usage.km2_covered.toFixed(1)}</p>
            </div>
            <div>
              <p className="text-xs text-text-muted">Readings</p>
              <p className="font-display text-xl text-text">{(usage.readings_count / 1000).toFixed(1)}K</p>
            </div>
            <div>
              <p className="text-xs text-text-muted">API Calls</p>
              <p className="font-display text-xl text-text">{usage.api_calls.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs text-text-muted">AI Insights</p>
              <p className="font-display text-xl text-text">{usage.insights_generated}</p>
            </div>
            <div>
              <p className="text-xs text-text-muted">Storage</p>
              <p className="font-display text-xl text-text">{usage.storage_mb.toFixed(0)} MB</p>
            </div>
          </div>
        </div>
      )}

      {/* Invoice History */}
      <div className="bg-panel rounded-lg border border-space-50 overflow-hidden">
        <div className="p-4 border-b border-space-50">
          <h3 className="font-display text-sm text-text">Invoice History</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-text-muted text-xs uppercase border-b border-space-50">
                <th className="px-4 py-3">Period</th>
                <th className="px-4 py-3">Sensors</th>
                <th className="px-4 py-3">Amount</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {invoices.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-text-dim">No invoices yet</td>
                </tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id} className="border-b border-space-50/50">
                    <td className="px-4 py-3 font-mono text-xs text-text-muted">
                      {inv.period_start} — {inv.period_end}
                    </td>
                    <td className="px-4 py-3 font-mono">{inv.sensor_count}</td>
                    <td className="px-4 py-3 font-display">${inv.amount_usd.toFixed(2)}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        inv.paid ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                      }`}>
                        {inv.paid ? 'Paid' : 'Pending'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
