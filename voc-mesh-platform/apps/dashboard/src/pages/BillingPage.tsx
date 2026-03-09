import { useState, useEffect } from 'react';
import clsx from 'clsx';
import { api, type BillingInfo, type UsageStats } from '../store/api';
import { useTenantStore } from '../store/tenant';
import SkeletonCard, { SkeletonTable } from '../components/SkeletonCard';

function StatCard({
  label,
  value,
  unit,
  icon,
}: {
  label: string;
  value: string | number;
  unit?: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="glass-panel p-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-voc/10 flex items-center justify-center text-voc flex-shrink-0">
          {icon}
        </div>
        <div>
          <div className="text-[10px] text-text-dim uppercase tracking-wider font-body">{label}</div>
          <div className="font-display text-lg text-text">
            {value}
            {unit && <span className="text-xs text-text-dim ml-1">{unit}</span>}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function BillingPage() {
  const [billing, setBilling] = useState<BillingInfo | null>(null);
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const tenant = useTenantStore((s) => s.tenant);

  useEffect(() => {
    const load = async () => {
      try {
        const [billingData, usageData] = await Promise.all([
          api.getBilling(),
          api.getUsage(),
        ]);
        setBilling(billingData);
        setUsage(usageData);
      } catch {
        // handled by api client
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <SkeletonCard key={i} lines={2} />
          ))}
        </div>
        <SkeletonCard lines={3} />
        <SkeletonTable rows={5} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-lg text-text">Billing & Usage</h2>
        <span className={clsx(
          'px-3 py-1 rounded-full text-xs font-body font-medium capitalize',
          tenant?.tier === 'enterprise' && 'bg-purple-500/10 text-purple-400',
          tenant?.tier === 'pro' && 'bg-voc/10 text-voc',
          tenant?.tier === 'free' && 'bg-white/5 text-text-muted',
        )}>
          {tenant?.tier} tier
        </span>
      </div>

      {/* Current month estimate */}
      <div className="glass-panel p-6 voc-glow">
        <div className="text-[10px] text-text-dim uppercase tracking-wider font-body mb-1">
          Current Month Estimate
        </div>
        <div className="flex items-baseline gap-2">
          <span className="font-display text-4xl text-voc">
            {billing?.currency === 'USD' ? '$' : billing?.currency}
            {billing?.current_month_estimate.toFixed(2)}
          </span>
          <span className="text-text-dim text-sm font-body">/ month</span>
        </div>
      </div>

      {/* Usage stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Sensors"
          value={usage?.sensors ?? billing?.sensors_count ?? 0}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.288 15.038a5.25 5.25 0 0 1 7.424 0M5.106 11.856c3.807-3.808 9.98-3.808 13.788 0M12.53 18.22l-.53.53-.53-.53a.75.75 0 0 1 1.06 0Z" />
            </svg>
          }
        />
        <StatCard
          label="Monitored Area"
          value={(usage?.area_km2 ?? billing?.area_km2 ?? 0).toFixed(1)}
          unit="km2"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498 4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 0 0-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0Z" />
            </svg>
          }
        />
        <StatCard
          label="Readings Today"
          value={(usage?.readings_today ?? billing?.readings_count ?? 0).toLocaleString()}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
            </svg>
          }
        />
        <StatCard
          label="API Calls Today"
          value={(usage?.api_calls_today ?? billing?.api_calls ?? 0).toLocaleString()}
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
            </svg>
          }
        />
      </div>

      {/* Tier info */}
      <div className="glass-panel p-4">
        <h3 className="font-display text-sm text-text mb-3">Tier Details</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm font-body">
          <div>
            <div className="text-text-dim text-xs mb-1">Plan</div>
            <div className="text-text capitalize">{billing?.tier ?? tenant?.tier}</div>
          </div>
          <div>
            <div className="text-text-dim text-xs mb-1">Sensors</div>
            <div className="text-text">{billing?.sensors_count ?? 0} active</div>
          </div>
          <div>
            <div className="text-text-dim text-xs mb-1">Area Coverage</div>
            <div className="text-text">{billing?.area_km2?.toFixed(1) ?? 0} km2</div>
          </div>
        </div>
      </div>

      {/* Invoice history */}
      <div className="glass-panel p-4">
        <h3 className="font-display text-sm text-text mb-4">Invoice History</h3>
        {billing?.invoices && billing.invoices.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm font-body">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="text-left py-2 px-3 text-text-dim text-xs font-medium uppercase tracking-wider">
                    Period
                  </th>
                  <th className="text-left py-2 px-3 text-text-dim text-xs font-medium uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="text-left py-2 px-3 text-text-dim text-xs font-medium uppercase tracking-wider">
                    Status
                  </th>
                  <th className="text-left py-2 px-3 text-text-dim text-xs font-medium uppercase tracking-wider">
                    ID
                  </th>
                </tr>
              </thead>
              <tbody>
                {billing.invoices.map((invoice) => (
                  <tr
                    key={invoice.id}
                    className="border-b border-white/5 hover:bg-white/[0.02] transition-colors"
                  >
                    <td className="py-2.5 px-3 text-text-muted">{invoice.period}</td>
                    <td className="py-2.5 px-3 text-text font-display">
                      ${invoice.amount.toFixed(2)}
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={clsx(
                          'inline-flex px-2 py-0.5 rounded-full text-[10px] font-medium capitalize',
                          invoice.status === 'paid' && 'bg-voc/10 text-voc',
                          invoice.status === 'pending' && 'bg-yellow-400/10 text-yellow-400',
                          invoice.status === 'overdue' && 'bg-alert/10 text-alert',
                        )}
                      >
                        {invoice.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-text-dim text-xs font-display">{invoice.id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-text-dim text-sm">No invoices yet.</div>
        )}
      </div>
    </div>
  );
}
