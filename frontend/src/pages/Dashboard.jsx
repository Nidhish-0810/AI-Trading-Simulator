import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, DollarSign, BarChart2, Activity, Wifi } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { portfolioService } from '../services/portfolio.service';
import { marketService } from '../services/market.service';
import { formatPrice, formatPercent, getChangeColor } from '../utils/format';
import PortfolioChart from '../components/charts/PortfolioChart';
import HoldingsTable from '../components/portfolio/HoldingsTable';
import StockCard from '../components/market/StockCard';
import { Skeleton } from '../components/ui/Skeleton';

const StatCard = ({ label, value, change, changePct, icon: Icon, color, loading }) => (
  <motion.div
    whileHover={{ y: -2 }}
    className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5 hover:border-white/20 transition-all"
  >
    {loading ? (
      <Skeleton className="h-20" />
    ) : (
      <>
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-gray-500">{label}</span>
          <div className={`w-9 h-9 rounded-xl ${color} flex items-center justify-center`}>
            <Icon className="w-4 h-4 text-white" />
          </div>
        </div>
        <p className={`font-mono text-2xl font-bold text-white`}>{value}</p>
        {change != null && (
          <p className={`text-sm font-mono mt-1 ${getChangeColor(changePct)}`}>
            {formatPercent(changePct)} today
          </p>
        )}
      </>
    )}
  </motion.div>
);

const TRENDING_SYMBOLS = ['AAPL', 'NVDA', 'MSFT', 'TSLA', 'META', 'GOOGL'];

export default function Dashboard() {
  const { user } = useAuthStore();

  const { data: portfolio, isLoading: portfolioLoading } = useQuery({
    queryKey: ['portfolio'],
    queryFn: portfolioService.getPortfolio,
    refetchInterval: 30000,
  });

  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ['portfolio-history'],
    queryFn: portfolioService.getHistory,
    refetchInterval: 60000,
  });

  const { data: trending } = useQuery({
    queryKey: ['trending'],
    queryFn: marketService.getTrending,
    refetchInterval: 60000,
  });

  const totalValue = portfolio?.total_value ?? 0;
  const cashBalance = portfolio?.cash_balance ?? user?.balance ?? 0;
  const invested = portfolio?.total_invested ?? 0;
  const pnl = portfolio?.total_pnl ?? 0;
  const pnlPct = portfolio?.total_pnl_pct ?? 0;
  const totalReturn = totalValue - 100000;
  const totalReturnPct = (totalReturn / 100000) * 100;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white">
            Welcome back, {user?.username || 'Trader'} 👋
          </h1>
          <p className="text-gray-500 text-sm mt-0.5">Here's your portfolio overview</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <Wifi className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
          <span className="text-xs text-emerald-400 font-medium">Live Data</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          label="Portfolio Value"
          value={formatPrice(totalValue)}
          change={pnl}
          changePct={pnlPct}
          icon={DollarSign}
          color="bg-gradient-to-br from-violet-600 to-violet-800"
          loading={portfolioLoading}
        />
        <StatCard
          label="Day's P&L"
          value={`${pnl >= 0 ? '+' : ''}${formatPrice(pnl)}`}
          change={pnl}
          changePct={pnlPct}
          icon={pnl >= 0 ? TrendingUp : TrendingDown}
          color={pnl >= 0 ? 'bg-gradient-to-br from-emerald-600 to-emerald-800' : 'bg-gradient-to-br from-red-600 to-red-800'}
          loading={portfolioLoading}
        />
        <StatCard
          label="Total Return"
          value={`${totalReturn >= 0 ? '+' : ''}${formatPrice(totalReturn)}`}
          change={totalReturn}
          changePct={totalReturnPct}
          icon={BarChart2}
          color="bg-gradient-to-br from-cyan-600 to-cyan-800"
          loading={portfolioLoading}
        />
        <StatCard
          label="Cash Balance"
          value={formatPrice(cashBalance)}
          icon={Activity}
          color="bg-gradient-to-br from-amber-600 to-amber-800"
          loading={portfolioLoading}
        />
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-white">Portfolio Performance</h2>
          <span className={`font-mono text-sm font-bold ${getChangeColor(totalReturnPct)}`}>
            {formatPercent(totalReturnPct)} all time
          </span>
        </div>
        {historyLoading ? (
          <Skeleton className="h-64" />
        ) : (
          <PortfolioChart data={history?.history || []} />
        )}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
          <h2 className="text-lg font-bold text-white mb-4">Your Holdings</h2>
          {portfolioLoading ? (
            <div className="space-y-3">
              {[1,2,3].map(i => <Skeleton key={i} className="h-14" />)}
            </div>
          ) : (
            <HoldingsTable holdings={portfolio?.holdings || []} compact />
          )}
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
          <h2 className="text-lg font-bold text-white mb-4">Top Movers</h2>
          <div className="space-y-3">
            {(trending?.trending || TRENDING_SYMBOLS.map(s => ({ symbol: s }))).slice(0, 6).map((stock, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/8 transition-colors cursor-pointer">
                <div>
                  <p className="font-mono text-sm font-bold text-white">{stock.symbol}</p>
                  <p className="text-xs text-gray-500">{stock.name || stock.symbol}</p>
                </div>
                <div className="text-right">
                  <p className="font-mono text-sm text-white">{formatPrice(stock.price || 0)}</p>
                  <p className={`font-mono text-xs ${getChangeColor(stock.change_pct || 0)}`}>
                    {formatPercent(stock.change_pct || 0)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}