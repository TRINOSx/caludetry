import { useEffect, useState } from 'react';
import { api, type Parcela } from '../store/api';
import { useTenantStore } from '../store/tenant';

interface Insight {
  id: string;
  parcela_id: string;
  parcela_name?: string;
  summary: string;
  urgency_level: 'low' | 'medium' | 'high' | 'critical';
  recommended_actions: string[];
  scientific_reasoning: string;
  created_at: string;
}

const urgencyColors = {
  low: 'bg-green-500/20 text-green-400 border-green-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
};

export default function InsightsPage() {
  const { useFeatureFlag } = useTenantStore();
  const aiEnabled = useFeatureFlag('ai_insights_enabled');
  const [insights, setInsights] = useState<Insight[]>([]);
  const [parcelas, setParcelas] = useState<Parcela[]>([]);
  const [generating, setGenerating] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    api.getParcelas().then(setParcelas);
    api.getInsights().then(setInsights).catch(() => {});
  }, []);

  const generateInsight = async (parcelaId: string) => {
    setGenerating(parcelaId);
    try {
      const insight = await api.generateInsight(parcelaId);
      setInsights((prev) => [insight, ...prev]);
    } catch (err) {
      console.error('Failed to generate insight:', err);
    } finally {
      setGenerating(null);
    }
  };

  if (!aiEnabled) {
    return (
      <div className="text-center py-20">
        <p className="text-4xl mb-4">🧠</p>
        <p className="text-text-muted text-lg">AI Insights not available on your plan</p>
        <p className="text-text-dim text-sm mt-2">Upgrade to AGRO_ENTERPRISE for AI-powered recommendations</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Generate Buttons */}
      <div className="bg-panel rounded-lg p-4 border border-space-50">
        <h3 className="font-display text-sm text-text mb-3">Generate AI Insight</h3>
        <div className="flex flex-wrap gap-2">
          {parcelas.map((p) => (
            <button
              key={p.id}
              onClick={() => generateInsight(p.id)}
              disabled={generating === p.id}
              className="px-4 py-2 bg-space rounded-lg border border-space-50 text-sm text-text-muted
                         hover:border-voc hover:text-voc transition-all disabled:opacity-50"
            >
              {generating === p.id ? (
                <span className="flex items-center gap-2">
                  <span className="w-3 h-3 border-2 border-voc border-t-transparent rounded-full animate-spin" />
                  Analyzing...
                </span>
              ) : (
                `🧠 ${p.name}`
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Insights Feed */}
      <div className="space-y-3">
        {insights.length === 0 ? (
          <div className="text-center py-16 text-text-muted">
            <p className="text-3xl mb-3">🌱</p>
            <p>No insights generated yet. Click a parcela above to analyze.</p>
          </div>
        ) : (
          insights.map((insight) => (
            <div key={insight.id} className="bg-panel rounded-lg border border-space-50 overflow-hidden">
              <div className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-0.5 text-xs font-bold rounded border ${urgencyColors[insight.urgency_level]}`}>
                      {insight.urgency_level.toUpperCase()}
                    </span>
                    <span className="text-xs text-text-dim font-mono">
                      {insight.parcela_name || insight.parcela_id}
                    </span>
                  </div>
                  <span className="text-xs text-text-dim font-mono">
                    {new Date(insight.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="text-text text-sm leading-relaxed">{insight.summary}</p>

                {/* Recommended Actions */}
                {insight.recommended_actions?.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs text-text-muted uppercase mb-1">Recommended Actions</p>
                    <ul className="space-y-1">
                      {insight.recommended_actions.map((action, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-voc">
                          <span className="text-voc mt-0.5">→</span>
                          <span className="text-text-muted">{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Scientific Reasoning (expandable) */}
                <button
                  onClick={() => setExpandedId(expandedId === insight.id ? null : insight.id)}
                  className="mt-3 text-xs text-voc/70 hover:text-voc transition-colors"
                >
                  {expandedId === insight.id ? '▼ Hide reasoning' : '▶ Scientific reasoning'}
                </button>
                {expandedId === insight.id && (
                  <div className="mt-2 p-3 bg-space rounded-lg text-xs text-text-muted leading-relaxed border border-space-50">
                    {insight.scientific_reasoning}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
