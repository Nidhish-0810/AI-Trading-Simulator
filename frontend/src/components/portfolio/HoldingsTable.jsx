import { Link } from 'react-router-dom';
import { formatPrice, formatPercent, getChangeColor } from '../../utils/format';
import { TrendingUp, TrendingDown } from 'lucide-react';
import MiniSparkline from '../charts/MiniSparkline';

const SECTOR_COLORS = {
  Technology: 'bg-violet-500/20 text-violet-300',
  Healthcare: 'bg-emerald-500/20 text-emerald-300',
  Finance: 'bg-blue-500/20 text-blue-300',
  Energy: 'bg-orange-500/20 text-orange-300',
  Consumer: 'bg-pink-500/20 text-pink-300',
};

export default function HoldingsTable({ holdings = [], compact = false }) {
  if (holdings.length === 0) {
    return (
      <div className="text-center py-10 text-gray-600">
        <p className="text-sm">No holdings yet — start trading!</p>
      </div>
    );
  }

  if (compact) {
    return (
      <div className="space-y-2">
        {holdings.slice(0, 5).map(h => {
          const pnl = h.pnl ?? 0;
          const pnlPct = h.pnl_pct ?? 0;
          return (
            <Link key={h.symbol} to={`/stock/${h.symbol}`}
              className="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors">
              <div>
                <p className="font-mono text-sm font-bold text-white">{h.symbol}</p>
                <p className="text-xs text-gray-500">{h.quantity?.toFixed(4)} shares @ {formatPrice(h.average_cost)}</p>
              </div>
              <div className="text-right">
                <p className="font-mono text-sm text-white">{formatPrice(h.current_value)}</p>
                <p className={`font-mono text-xs ${getChangeColor(pnlPct)}`}>{formatPercent(pnlPct)}</p>
              </div>
            </Link>
          );
        })}
        {holdings.length > 5 && (
          <Link to="/portfolio" className="block text-center text-xs text-violet-400 hover:text-violet-300 py-2">
            View all {holdings.length} holdings →
          </Link>
        )}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10 text-xs text-gray-500 font-medium">
            <th className="py-3 text-left">Symbol</th>
            <th className="py-3 text-right">Qty</th>
            <th className="py-3 text-right">Avg Cost</th>
            <th className="py-3 text-right">Current Price</th>
            <th className="py-3 text-right">Value</th>
            <th className="py-3 text-right">P&L</th>
            <th className="py-3 text-right">P&L %</th>
            <th className="py-3 text-right">Day Change</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {holdings.map(h => {
            const pnl = h.pnl ?? 0;
            const pnlPct = h.pnl_pct ?? 0;
            const dayChange = h.day_change ?? 0;
            return (
              <tr key={h.symbol} className="hover:bg-white/5 transition-colors group">
                <td className="py-3">
                  <Link to={`/stock/${h.symbol}`} className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-600/40 to-cyan-600/40 flex items-center justify-center">
                      <span className="text-xs font-bold text-white">{h.symbol[0]}</span>
                    </div>
                    <div>
                      <p className="font-mono font-bold text-white group-hover:text-violet-300 transition-colors">{h.symbol}</p>
                      {h.sector && (
                        <span className={`text-xs px-1.5 py-0.5 rounded ${SECTOR_COLORS[h.sector] || 'bg-gray-500/20 text-gray-400'}`}>
                          {h.sector}
                        </span>
                      )}
                    </div>
                  </Link>
                </td>
                <td className="py-3 text-right font-mono text-gray-300">{h.quantity?.toFixed(4)}</td>
                <td className="py-3 text-right font-mono text-gray-300">{formatPrice(h.average_cost)}</td>
                <td className="py-3 text-right font-mono text-white">{formatPrice(h.current_price)}</td>
                <td className="py-3 text-right font-mono text-white font-semibold">{formatPrice(h.current_value)}</td>
                <td className={`py-3 text-right font-mono font-bold ${getChangeColor(pnl)}`}>
                  {pnl >= 0 ? '+' : ''}{formatPrice(pnl)}
                </td>
                <td className={`py-3 text-right font-mono font-bold ${getChangeColor(pnlPct)}`}>
                  {formatPercent(pnlPct)}
                </td>
                <td className={`py-3 text-right font-mono text-sm ${getChangeColor(dayChange)}`}>
                  {dayChange >= 0 ? '+' : ''}{formatPrice(dayChange)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
