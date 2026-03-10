import { useRef } from 'react';
import type { Prediction } from '../../store/api';

interface PredictionTimelineProps {
  predictions: Prediction[];
}

export default function PredictionTimeline({ predictions }: PredictionTimelineProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const now = new Date();

  const pastPredictions = predictions
    .filter((p) => new Date(p.prediction_for) <= now)
    .sort((a, b) => new Date(a.prediction_for).getTime() - new Date(b.prediction_for).getTime());

  const futurePredictions = predictions
    .filter((p) => new Date(p.prediction_for) > now)
    .sort((a, b) => new Date(a.prediction_for).getTime() - new Date(b.prediction_for).getTime());

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  const formatTime = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="glass-panel p-4">
      <h3 className="font-display text-sm text-text mb-4">Prediction Timeline</h3>

      <div
        ref={scrollRef}
        className="flex items-center gap-3 overflow-x-auto pb-3 scrollbar-thin"
      >
        {/* Past predictions */}
        {pastPredictions.map((pred) => (
          <div
            key={pred.id}
            className="flex-shrink-0 w-36 opacity-60 hover:opacity-80 transition-opacity"
          >
            <div className="bg-space/80 rounded-lg border border-white/5 p-3">
              {pred.thumbnail_url ? (
                <img
                  src={pred.thumbnail_url}
                  alt="Prediction"
                  className="w-full h-16 object-cover rounded mb-2 grayscale"
                />
              ) : (
                <div className="w-full h-16 bg-space-50 rounded mb-2 flex items-center justify-center">
                  <svg className="w-5 h-5 text-text-dim" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
                  </svg>
                </div>
              )}
              <div className="text-[10px] text-text-dim font-body">{formatDate(pred.prediction_for)}</div>
              <div className="text-[10px] text-text-muted font-body">{formatTime(pred.prediction_for)}</div>
              <div className="flex items-center gap-1 mt-1">
                <span className="text-[10px] text-text-dim">Stress:</span>
                <span className="text-[10px] text-alert">{(pred.stress_predicted * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>
        ))}

        {/* NOW marker */}
        <div className="flex-shrink-0 flex flex-col items-center">
          <div className="w-px h-8 bg-voc/40" />
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-voc/20 border-2 border-voc flex items-center justify-center animate-pulse-slow">
              <span className="text-voc font-display text-[10px] font-bold">NOW</span>
            </div>
          </div>
          <div className="w-px h-8 bg-voc/40" />
        </div>

        {/* Future predictions */}
        {futurePredictions.map((pred) => (
          <div key={pred.id} className="flex-shrink-0 w-36">
            <div
              className="bg-space/40 rounded-lg border border-dashed border-voc/30 p-3"
              style={{ opacity: 0.4 + pred.confidence * 0.6 }}
            >
              {pred.thumbnail_url ? (
                <img
                  src={pred.thumbnail_url}
                  alt="Prediction"
                  className="w-full h-16 object-cover rounded mb-2"
                />
              ) : (
                <div className="w-full h-16 bg-voc/5 rounded mb-2 flex items-center justify-center border border-dashed border-voc/20">
                  <svg className="w-5 h-5 text-voc/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
                  </svg>
                </div>
              )}
              <div className="text-[10px] text-voc/70 font-body">{formatDate(pred.prediction_for)}</div>
              <div className="text-[10px] text-text-muted font-body">{formatTime(pred.prediction_for)}</div>
              <div className="flex items-center justify-between mt-1">
                <span className="text-[10px] text-text-dim">Conf:</span>
                <span className="text-[10px] text-voc">{(pred.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>
        ))}

        {futurePredictions.length === 0 && (
          <div className="flex-shrink-0 w-36">
            <div className="bg-space/40 rounded-lg border border-dashed border-white/10 p-3 flex items-center justify-center h-28">
              <span className="text-text-dim text-xs font-body text-center">
                No predictions yet
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
