import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Play, BarChart2, TrendingUp, AlertTriangle, Award, Target } from 'lucide-react';
import { aiService } from '../services/ai.service';
import { formatPrice, formatPercent, getChangeColor } from '../utils/format';
import PortfolioChart from '../components/charts/PortfolioChart';
import toast from 'react-hot-toast';

const STRATEGIES = [
  { id: 'sma_crossover', label: 'SMA Crossover', desc: 'Fast SMA crosses above/below slow SMA', color: 'from-violet-500 to-purple-500' },
  { id: 'rsi', label: 'RSI Strategy', desc: 'Buy oversold (<30), sell overbought (>70)', color: 'from-emerald-500 to-teal-500' },
  { id: 'macd', label: 'MACD Strategy', desc: 'Trade MACD/signal line crossovers', color: 'from-blue-500 to-cyan-500' },
  { id: 'bollinger', label: 'Bollinger Bands', desc: 'Mean reversion at band touches', color: 'from-amber-500 to-orange-500' },
];

const MetricBox = ({ label, value, good }) => {
  const color = good === true ? 'text-emerald-400' : good === false ? 'text-red-400' : 'text-white';
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-center">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`font-mono text-xl font-bold ${color}`}>{value}</p>
    </div>
  );
};

export default function Backtesting() {
  const [symbol, setSymbol] = useState('AAPL');
  const [strategy, setStrategy] = useState('sma_crossover');
  const [startDate, setStartDate] = useState('2022-01-01');
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [capital, setCapital] = useState(10000);
  const [results, setResults] = useState(null);

  const runMutation = useMutation({
    mutationFn: () => aiService.runBacktest({ symbol, strategy, start_date: startDate, end_date: endDate, capital }),
    onSuccess: (data) => {
      setResults(data);
      toast.success('Backtest completed! 📊');
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Backtest failed');
    },
  });

  const selectedStrategy = STRATEGIES.find(s => s.id === strategy);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-black text-white">Strategy Backtesting</h1>
        <p className="text-gray-500 text-sm">Test trading strategies against historical data</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="space-y-4">
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5 space-y-4">
            <h2 className="font-bold text-white">Configuration</h2>

            <div>
              <label className="text-sm text-gray-400 block mb-1.5">Symbol</label>
              <input
                value={symbol}
                onChange={e => setSymbol(e.target.value.toUpperCase())}
                className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white font-mono focus:border-violet-500 outline-none transition-all text-sm"
                placeholder="AAPL"
              />
            </div>

            <div>
              <label className="text-sm text-gray-400 block mb-2">Strategy</label>
              <div className="grid grid-cols-1 gap-2">
                {STRATEGIES.map(s => (
                  <button
                    key={s.id}
                    onClick={() => setStrategy(s.id)}
                    className={`flex items-start gap-3 p-3 rounded-xl border text-left transition-all ${
                      strategy === s.id
                        ? 'border-violet-500/50 bg-violet-500/10'
                        : 'border-white/10 bg-white/5 hover:bg-white/10'
                    }`}
                  >
                    <div className={`w-2 h-2 rounded-full mt-1.5 bg-gradient-to-r ${s.color} flex-shrink-0`} />
                    <div>
                      <p className={`text-sm font-semibold ${strategy === s.id ? 'text-violet-300' : 'text-gray-300'}`}>{s.label}</p>
                      <p className="text-xs text-gray-600">{s.desc}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm text-gray-400 block mb-1.5">Start Date</label>
                <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm focus:border-violet-500 outline-none" />
              </div>
              <div>
                <label className="text-sm text-gray-400 block mb-1.5">End Date</label>
                <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm focus:border-violet-500 outline-none" />
              </div>
            </div>

            <div>
              <label className="text-sm text-gray-400 block mb-1.5">Starting Capital (USD)</label>
              <input type="number" value={capital} onChange={e => setCapital(Number(e.target.value))}
                min={100} step={1000}
                className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white font-mono text-sm focus:border-violet-500 outline-none" />
            </div>

            <button
              onClick={() => runMutation.mutate()}
              disabled={runMutation.isPending}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-500 hover:to-cyan-500 text-white font-bold transition-all disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              {runMutation.isPending ? 'Running...' : 'Run Backtest'}
            </button>
          </div>
        </div>

        <div className="xl:col-span-2 space-y-4">
          {!results && !runMutation.isPending && (
            <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-12 text-center">
              <BarChart2 className="w-14 h-14 mx-auto text-gray-700 mb-4" />
              <p className="text-gray-500">Configure a strategy and click Run Backtest</p>
              <p className="text-xs text-gray-700 mt-2">Results will appear here</p>
            </div>
          )}

          {runMutation.isPending && (
            <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-12 text-center">
              <div className="w-12 h-12 mx-auto mb-4 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-gray-400">Running backtest against {symbol}...</p>
            </div>
          )}

          {results && (
            <>
              <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-bold text-white">
                    {selectedStrategy?.label} — {results.symbol}
                  </h2>
                  <span className={`font-mono text-lg font-black ${results.total_return_pct >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {results.total_return_pct >= 0 ? '+' : ''}{results.total_return_pct?.toFixed(2)}%
                  </span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  <MetricBox label="Final Value" value={formatPrice(results.final_value)} />
                  <MetricBox label="Total Return" value={formatPercent(results.total_return_pct)} good={results.total_return_pct > 0} />
                  <MetricBox label="Sharpe Ratio" value={results.sharpe_ratio?.toFixed(3)} good={results.sharpe_ratio > 1} />
                  <MetricBox label="Max Drawdown" value={`-${results.max_drawdown_pct?.toFixed(1)}%`} good={results.max_drawdown_pct < 15} />
                  <MetricBox label="Win Rate" value={`${results.win_rate?.toFixed(1)}%`} good={results.win_rate > 50} />
                  <MetricBox label="Total Trades" value={results.total_trades} />
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
                <h3 className="font-bold text-white mb-4">Equity Curve</h3>
                <PortfolioChart data={(results.equity_curve || []).map(d => ({ date: d.date, value: d.value }))} />
              </div>

              {results.trades?.length > 0 && (
                <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
                  <h3 className="font-bold text-white mb-4">Trade Log (Last 20)</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-white/10 text-gray-500">
                          <th className="py-2 text-left font-medium">Date</th>
                          <th className="py-2 text-left font-medium">Action</th>
                          <th className="py-2 text-right font-medium">Price</th>
                          <th className="py-2 text-right font-medium">Value</th>
                          <th className="py-2 text-right font-medium">P&L</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {results.trades.slice(-20).map((t, i) => (
                          <tr key={i} className="hover:bg-white/5">
                            <td className="py-2 font-mono text-xs text-gray-400">{t.date}</td>
                            <td className="py-2">
                              <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${t.action?.startsWith('BUY') ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                                {t.action}
                              </span>
                            </td>
                            <td className="py-2 text-right font-mono text-gray-300">{formatPrice(t.price)}</td>
                            <td className="py-2 text-right font-mono text-gray-300">{formatPrice(t.value)}</td>
                            <td className={`py-2 text-right font-mono ${(t.pnl || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {t.pnl != null ? `${t.pnl >= 0 ? '+' : ''}${formatPrice(t.pnl)}` : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}