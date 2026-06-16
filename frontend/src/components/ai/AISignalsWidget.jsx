import { TrendingUp, TrendingDown, Minus, Activity, Target } from 'lucide-react';

const SIGNAL_STYLES = {
  STRONG_BUY: { label: 'STRONG BUY', bg: 'bg-emerald-500/20', border: 'border-emerald-500/40', text: 'text-emerald-300', dot: 'bg-emerald-400' },
  BUY: { label: 'BUY', bg: 'bg-green-500/20', border: 'border-green-500/40', text: 'text-green-300', dot: 'bg-green-400' },
  NEUTRAL: { label: 'NEUTRAL', bg: 'bg-gray-500/20', border: 'border-gray-500/40', text: 'text-gray-300', dot: 'bg-gray-400' },
  SELL: { label: 'SELL', bg: 'bg-amber-500/20', border: 'border-amber-500/40', text: 'text-amber-300', dot: 'bg-amber-400' },
  STRONG_SELL: { label: 'STRONG SELL', bg: 'bg-red-500/20', border: 'border-red-500/40', text: 'text-red-300', dot: 'bg-red-400' },
};

const IndicatorRow = ({ name, indicator }) => {
  if (!indicator) return null;
  const isUp = indicator.signal === 'bullish';
  const isDown = indicator.signal === 'bearish';
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-white/5">
      <div className="flex items-center gap-2">
        {isUp ? <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> :
         isDown ? <TrendingDown className="w-3.5 h-3.5 text-red-400" /> :
         <Minus className="w-3.5 h-3.5 text-gray-500" />}
        <span className="text-sm text-gray-300 uppercase text-xs font-mono font-bold">{name}</span>
      </div>
      <div className="text-right">
        <p className={`text-xs font-mono ${isUp ? 'text-emerald-400' : isDown ? 'text-red-400' : 'text-gray-500'}`}>
          {isUp ? '▲ Bullish' : isDown ? '▼ Bearish' : '→ Neutral'}
        </p>
        <p className="text-xs text-gray-600 truncate max-w-36">{indicator.description}</p>
      </div>
    </div>
  );
};

export default function AISignalsWidget({ signals }) {
  if (!signals) return (
    <div className="text-center py-8 text-gray-600">
      <Activity className="w-8 h-8 mx-auto mb-2 opacity-40" />
      <p className="text-sm">No signals available</p>
    </div>
  );

  const style = SIGNAL_STYLES[signals.signal] || SIGNAL_STYLES.NEUTRAL;

  return (
    <div className="space-y-4">
      {/* Main Signal */}
      <div className={`rounded-xl border ${style.border} ${style.bg} p-4 flex items-center justify-between`}>
        <div>
          <p className="text-xs text-gray-500 mb-1">AI Signal</p>
          <div className="flex items-center gap-2">
            <div className={`w-2.5 h-2.5 rounded-full ${style.dot} animate-pulse`} />
            <span className={`text-xl font-black ${style.text}`}>{style.label}</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">Score: {signals.score > 0 ? '+' : ''}{signals.score}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-500 mb-1">Confidence</p>
          <p className={`font-mono text-2xl font-black ${style.text}`}>{signals.confidence?.toFixed(0)}%</p>
          <div className="w-24 h-1.5 bg-white/10 rounded-full mt-1 overflow-hidden">
            <div className={`h-full ${style.dot} rounded-full`} style={{ width: `${signals.confidence || 0}%` }} />
          </div>
        </div>
      </div>

      {/* Support / Resistance */}
      {(signals.support_level || signals.resistance_level) && (
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3">
            <p className="text-xs text-gray-500 mb-0.5 flex items-center gap-1"><Target className="w-3 h-3" /> Support</p>
            <p className="font-mono text-sm font-bold text-emerald-400">
              ${signals.support_level?.toFixed(2) || 'N/A'}
            </p>
          </div>
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-3">
            <p className="text-xs text-gray-500 mb-0.5 flex items-center gap-1"><Target className="w-3 h-3" /> Resistance</p>
            <p className="font-mono text-sm font-bold text-red-400">
              ${signals.resistance_level?.toFixed(2) || 'N/A'}
            </p>
          </div>
        </div>
      )}

      {/* Indicators */}
      <div className="rounded-xl border border-white/10 bg-white/5 p-4">
        <h3 className="text-xs font-bold text-gray-400 uppercase mb-2">Technical Indicators</h3>
        <IndicatorRow name="RSI(14)" indicator={signals.indicators?.rsi} />
        <IndicatorRow name="MACD" indicator={signals.indicators?.macd} />
        <IndicatorRow name="SMA(50)" indicator={signals.indicators?.sma_50} />
        <IndicatorRow name="SMA(200)" indicator={signals.indicators?.sma_200} />
        <IndicatorRow name="Bollinger" indicator={signals.indicators?.bollinger} />
        <IndicatorRow name="Stochastic" indicator={signals.indicators?.stochastic} />
      </div>

      {/* Reasoning */}
      {signals.reasoning?.length > 0 && (
        <div className="rounded-xl border border-white/10 bg-white/5 p-4">
          <h3 className="text-xs font-bold text-gray-400 uppercase mb-3">Analysis</h3>
          <ul className="space-y-2">
            {signals.reasoning.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-gray-400">
                <span className="text-violet-400 mt-0.5 flex-shrink-0">•</span>
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Volatility */}
      {signals.volatility_score != null && (
        <div className="rounded-xl border border-white/10 bg-white/5 p-3 flex items-center justify-between">
          <span className="text-xs text-gray-500">Volatility Score</span>
          <div className="flex items-center gap-2">
            <div className="w-24 h-1.5 bg-white/10 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${signals.volatility_score > 70 ? 'bg-red-400' : signals.volatility_score > 40 ? 'bg-amber-400' : 'bg-emerald-400'}`}
                style={{ width: `${signals.volatility_score}%` }}
              />
            </div>
            <span className="font-mono text-xs text-gray-300">{signals.volatility_score?.toFixed(0)}/100</span>
          </div>
        </div>
      )}
    </div>
  );
}
