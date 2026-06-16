import { useQuery } from '@tanstack/react-query';
import { TrendingUp, Activity, AlertTriangle, Award, Target, BarChart2 } from 'lucide-react';
import { portfolioService } from '../services/portfolio.service';
import { formatPrice, formatPercent } from '../utils/format';
import PortfolioChart from '../components/charts/PortfolioChart';
import { Skeleton } from '../components/ui/Skeleton';

const MetricCard = ({ label, value, sub, color, icon: Icon, description }) => (
  <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5 hover:border-white/20 transition-all">
    <div className="flex items-center justify-between mb-3">
      <span className="text-sm text-gray-500">{label}</span>
      <div className={`w-8 h-8 rounded-lg ${color} flex items-center justify-center`}>
        <Icon className="w-4 h-4 text-white" />
      </div>
    </div>
    <p className="font-mono text-2xl font-black text-white">{value}</p>
    {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    {description && <p className="text-xs text-gray-600 mt-2">{description}</p>}
  </div>
);

const GaugeBar = ({ value, min, max, label, good = 'high' }) => {
  const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
  const isGood = good === 'high' ? pct > 50 : pct < 50;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-gray-500">
        <span>{label}</span>
        <span className="font-mono">{typeof value === 'number' ? value.toFixed(3) : value}</span>
      </div>
      <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${isGood ? 'bg-emerald-400' : 'bg-red-400'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
};

export default function Analytics() {
  const { data: analytics, isLoading } = useQuery({
    queryKey: ['analytics'],
    queryFn: portfolioService.getAnalytics,
    refetchInterval: 60000,
  });

  const { data: history } = useQuery({
    queryKey: ['portfolio-history'],
    queryFn: portfolioService.getHistory,
  });

  const a = analytics || {};

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-black text-white">Analytics</h1>
        <p className="text-gray-500 text-sm">Advanced portfolio performance metrics</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? (
          Array.from({length: 6}).map((_,i) => <Skeleton key={i} className="h-28 rounded-2xl" />)
        ) : (
          <>
            <MetricCard label="Sharpe Ratio" value={(a.sharpe_ratio ?? 0).toFixed(3)}
              sub="Risk-adjusted return" color="bg-violet-600/60"
              icon={Award} description=">1.0 is good, >2.0 is excellent" />
            <MetricCard label="Beta" value={(a.beta ?? 0).toFixed(3)}
              sub="vs S&P 500" color="bg-blue-600/60"
              icon={Activity} description="1.0 = market avg volatility" />
            <MetricCard label="Alpha" value={`${(a.alpha ?? 0).toFixed(3)}%`}
              sub="Excess return" color="bg-emerald-600/60"
              icon={TrendingUp} description="Positive = outperforming market" />
            <MetricCard label="Max Drawdown" value={`-${(a.max_drawdown_pct ?? 0).toFixed(1)}%`}
              sub="Largest peak-to-trough" color="bg-red-600/60"
              icon={AlertTriangle} description="Lower is better" />
            <MetricCard label="Win Rate" value={`${(a.win_rate ?? 0).toFixed(1)}%`}
              sub="% of profitable trades" color="bg-amber-600/60"
              icon={Target} description=">50% is profitable" />
            <MetricCard label="Volatility" value={`${(a.volatility ?? 0).toFixed(1)}%`}
              sub="Annualized std deviation" color="bg-pink-600/60"
              icon={BarChart2} description="Lower = less risk" />
          </>
        )}
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
        <h2 className="text-lg font-bold text-white mb-5">Risk Profile</h2>
        {isLoading ? <Skeleton className="h-32" /> : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <GaugeBar label="Sharpe Ratio" value={a.sharpe_ratio ?? 0} min={-2} max={3} good="high" />
              <GaugeBar label="Win Rate %" value={a.win_rate ?? 0} min={0} max={100} good="high" />
              <GaugeBar label="Alpha %" value={a.alpha ?? 0} min={-10} max={20} good="high" />
            </div>
            <div className="space-y-4">
              <GaugeBar label="Volatility %" value={a.volatility ?? 0} min={0} max={100} good="low" />
              <GaugeBar label="Max Drawdown %" value={a.max_drawdown_pct ?? 0} min={0} max={100} good="low" />
              <GaugeBar label="Beta" value={a.beta ?? 1} min={0} max={3} good="low" />
            </div>
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-white">Portfolio Performance</h2>
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-violet-400 inline-block" /> Portfolio</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-gray-600 inline-block" /> Market</span>
          </div>
        </div>
        <PortfolioChart data={history?.history || []} showBenchmark />
      </div>

      {!isLoading && a.best_trades && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
            <h3 className="font-bold text-emerald-400 mb-3">Best Trades</h3>
            <div className="space-y-2">
              {(a.best_trades || []).slice(0, 5).map((t, i) => (
                <div key={i} className="flex justify-between items-center">
                  <span className="font-mono text-sm text-white">{t.symbol}</span>
                  <span className="font-mono text-sm text-emerald-400">{formatPercent(t.pnl_pct)}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
            <h3 className="font-bold text-red-400 mb-3">Worst Trades</h3>
            <div className="space-y-2">
              {(a.worst_trades || []).slice(0, 5).map((t, i) => (
                <div key={i} className="flex justify-between items-center">
                  <span className="font-mono text-sm text-white">{t.symbol}</span>
                  <span className="font-mono text-sm text-red-400">{formatPercent(t.pnl_pct)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}