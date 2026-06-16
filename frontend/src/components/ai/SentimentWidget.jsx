import { Newspaper } from 'lucide-react';

export default function SentimentWidget({ sentiment }) {
  if (!sentiment) return null;
  const score = sentiment.score ?? 0;
  const label = sentiment.label || 'Neutral';
  const isPos = score > 0.1;
  const isNeg = score < -0.1;
  const color = isPos ? 'text-emerald-400' : isNeg ? 'text-red-400' : 'text-gray-400';
  const bg = isPos ? 'bg-emerald-500/10 border-emerald-500/20' : isNeg ? 'bg-red-500/10 border-red-500/20' : 'bg-gray-500/10 border-gray-500/20';
  const pct = Math.round((score + 1) * 50); // map -1..1 to 0..100

  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold text-gray-400 uppercase flex items-center gap-1.5">
          <Newspaper className="w-3.5 h-3.5" /> News Sentiment
        </h3>
        <span className={`px-3 py-0.5 rounded-full text-xs font-bold border ${bg} ${color}`}>{label}</span>
      </div>

      {/* Gauge */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-gray-600">
          <span>Bearish</span><span>Neutral</span><span>Bullish</span>
        </div>
        <div className="h-2 bg-white/10 rounded-full overflow-hidden relative">
          <div className="absolute inset-y-0 w-0.5 bg-white/20" style={{ left: '50%' }} />
          <div
            className={`h-full rounded-full transition-all ${isPos ? 'bg-emerald-400' : isNeg ? 'bg-red-400' : 'bg-gray-400'}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className={`text-xs font-mono text-right ${color}`}>
          Score: {score > 0 ? '+' : ''}{score.toFixed(3)}
        </p>
      </div>

      {/* Top News */}
      {sentiment.scored_news?.length > 0 && (
        <div className="space-y-2 mt-2">
          {sentiment.scored_news.slice(0, 5).map((n, i) => {
            const ns = n.score ?? 0;
            const nc = ns > 0.1 ? 'text-emerald-400' : ns < -0.1 ? 'text-red-400' : 'text-gray-500';
            return (
              <div key={i} className="flex items-start gap-2">
                <span className={`text-xs font-mono flex-shrink-0 mt-0.5 ${nc}`}>
                  {ns > 0.1 ? '↑' : ns < -0.1 ? '↓' : '→'}
                </span>
                <p className="text-xs text-gray-400 line-clamp-2">{n.title}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
