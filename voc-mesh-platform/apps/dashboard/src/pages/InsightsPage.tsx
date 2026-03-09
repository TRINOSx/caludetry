import { useState, useEffect } from 'react';
import clsx from 'clsx';
import { api, type Insight, type Parcela } from '../store/api';
import SkeletonCard from '../components/SkeletonCard';

const URGENCY_CONFIG: Record<string, { bg: string; text: string; label: string }> = {
  low: { bg: 'bg-voc/10', text: 'text-voc', label: 'Low' },
  medium: { bg: 'bg-yellow-400/10', text: 'text-yellow-400', label: 'Medium' },
  high: { bg: 'bg-orange-500/10', text: 'text-orange-500', label: 'High' },
  critical: { bg: 'bg-alert/10', text: 'text-alert', label: 'Critical' },
};

function InsightCard({ insight }: { insight: Insight }) {
  const [expanded, setExpanded] = useState(false);
  const urgency = URGENCY_CONFIG[insight.urgency] ?? URGENCY_CONFIG.low;

  return (
    <div className="glass-panel p-4 border border-white/5">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={clsx('px-2 py-0.5 rounded-full text-[10px] font-medium', urgency.bg, urgency.text)}>
              {urgency.label}
            </span>
            <span className="text-[10px] text-text-dim font-body">
              {insight.parcela_name}
            </span>
          </div>
          <h3 className="font-display text-sm text-text">{insight.title}</h3>
        </div>
        <span className="text-[10px] text-text-dim font-body whitespace-nowrap">
          {new Date(insight.created_at).toLocaleDateString([], {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>

      <p className="text-sm text-text-muted font-body leading-relaxed mb-3">
        {insight.recommendation}
      </p>

      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-xs text-voc/70 hover:text-voc font-body transition-colors"
      >
        <svg
          className={clsx('w-3 h-3 transition-transform', expanded && 'rotate-90')}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
        </svg>
        Scientific Reasoning
      </button>

      {expanded && (
        <div className="mt-3 pt-3 border-t border-white/5">
          <p className="text-xs text-text-dim font-body leading-relaxed whitespace-pre-wrap">
            {insight.scientific_reasoning}
          </p>
        </div>
      )}
    </div>
  );
}

export default function InsightsPage() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [parcelas, setParcelas] = useState<Parcela[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<string | null>(null);
  const [filterUrgency, setFilterUrgency] = useState<string>('all');

  useEffect(() => {
    const load = async () => {
      try {
        const [insightList, parcelaList] = await Promise.all([
          api.getInsights(),
          api.getParcelas(),
        ]);
        setInsights(insightList);
        setParcelas(parcelaList);
      } catch {
        // handled by api client
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleGenerate = async (parcelaId: string) => {
    setGenerating(parcelaId);
    try {
      const newInsight = await api.generateInsight(parcelaId);
      setInsights((prev) => [newInsight, ...prev]);
    } catch {
      // handled by api client
    } finally {
      setGenerating(null);
    }
  };

  const filteredInsights =
    filterUrgency === 'all'
      ? insights
      : insights.filter((i) => i.urgency === filterUrgency);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="font-display text-lg text-text">AI Insights</h2>
        <div className="flex gap-1">
          {['all', 'critical', 'high', 'medium', 'low'].map((level) => (
            <button
              key={level}
              onClick={() => setFilterUrgency(level)}
              className={clsx(
                'px-2.5 py-1 text-xs font-body rounded capitalize transition-colors',
                filterUrgency === level
                  ? 'bg-voc/20 text-voc'
                  : 'text-text-dim hover:text-text-muted hover:bg-white/5',
              )}
            >
              {level}
            </button>
          ))}
        </div>
      </div>

      {/* Generate buttons per parcela */}
      <div className="flex flex-wrap gap-2">
        {parcelas.map((p) => (
          <button
            key={p.id}
            onClick={() => handleGenerate(p.id)}
            disabled={generating === p.id}
            className={clsx(
              'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-body transition-colors border',
              generating === p.id
                ? 'border-voc/20 text-voc/50 cursor-not-allowed'
                : 'border-voc/30 text-voc hover:bg-voc/10',
            )}
          >
            {generating === p.id ? (
              <svg className="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : (
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
              </svg>
            )}
            Generate for {p.name}
          </button>
        ))}
      </div>

      {/* Insights feed */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <SkeletonCard key={i} lines={4} />
          ))}
        </div>
      ) : filteredInsights.length > 0 ? (
        <div className="space-y-4">
          {filteredInsights.map((insight) => (
            <InsightCard key={insight.id} insight={insight} />
          ))}
        </div>
      ) : (
        <div className="glass-panel p-12 text-center">
          <svg className="w-12 h-12 text-text-dim mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-.189m-1.5.189a6.01 6.01 0 0 1-1.5-.189m3.75 7.478a12.06 12.06 0 0 1-4.5 0m3.75 2.383a14.406 14.406 0 0 1-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 1 0-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
          </svg>
          <p className="text-text-muted font-body text-sm">No insights yet. Generate one from a parcela above.</p>
        </div>
      )}
    </div>
  );
}
