import { useQuery } from '@tanstack/react-query';
import { DollarSign, TrendingUp, TrendingDown, PieChart } from 'lucide-react';
import { portfolioService } from '../services/portfolio.service';
import { formatPrice, formatPercent, getChangeColor } from '../utils/format';
import PortfolioChart from '../components/charts/PortfolioChart';
import SectorAllocationChart from '../components/charts/SectorAllocationChart';
import HoldingsTable from '../components/portfolio/HoldingsTable';
import TransactionHistory from '../components/portfolio/TransactionHistory';
import { Skeleton } from '../components/ui/Skeleton';

const StatBadge = ({ label, value, sub, up }) => (
  <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
    <p className="text-sm text-gray-500 mb-1">{label}</p>
    <p className={`font-mono text-2xl font-bold ${up != null ? (up ? 'text-emerald-400' : 'text-red-400') : 'text-white'}`}>
      {value}
    </p>
    {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
  </div>
);

export default function Portfolio() {
  const { data: portfolio, isLoading } = useQuery({
    queryKey: ['portfolio'],
    queryFn: portfolioService.getPortfolio,
    refetchInterval: 30000,
  });

  const { data: history } = useQuery({
    queryKey: ['portfolio-history'],
    queryFn: portfolioService.getHistory,
  });

  const { data: transactions } = useQuery({
    queryKey: ['transactions'],
    queryFn: portfolioService.getTransactions,
  });

  const totalValue = portfolio?.total_value ?? 0;
  const invested = portfolio?.total_invested ?? 0;
  const pnl = portfolio?.total_pnl ?? 0;
  const pnlPct = portfolio?.total_pnl_pct ?? 0;
  const cash = portfolio?.cash_balance ?? 0;
  const holdings = portfolio?.holdings ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-black text-white">Portfolio</h1>
        <p className="text-gray-500 text-sm">Your complete investment overview</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {isLoading ? (
          Array.from({length: 5}).map((_,i) => <Skeleton key={i} className="h-24 rounded-2xl" />)
        ) : (
          <>
            <StatBadge label="Total Value" value={formatPrice(totalValue)} sub="Portfolio + Cash" />
            <StatBadge label="Invested" value={formatPrice(invested)} sub={`${holdings.length} positions`} />
            <StatBadge label="Total P&L" value={`${pnl >= 0 ? '+' : ''}${formatPrice(pnl)}`} sub={formatPercent(pnlPct)} up={pnl >= 0} />
            <StatBadge label="Cash Balance" value={formatPrice(cash)} sub="Available to trade" />
            <StatBadge label="# Holdings" value={holdings.length} sub="Unique stocks" />
          </>
        )}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
          <h2 className="text-lg font-bold text-white mb-4">Portfolio History</h2>
          <PortfolioChart data={history?.history || []} />
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <PieChart className="w-4 h-4 text-violet-400" /> Sector Allocation
          </h2>
          <SectorAllocationChart holdings={holdings} />
        </div>
      </div>

      {/* Holdings Table */}
      <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
        <h2 className="text-lg font-bold text-white mb-4">Holdings</h2>
        {isLoading
          ? <div className="space-y-3">{[1,2,3].map(i => <Skeleton key={i} className="h-14" />)}</div>
          : <HoldingsTable holdings={holdings} />
        }
      </div>

      {/* Transaction History */}
      <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
        <h2 className="text-lg font-bold text-white mb-4">Transaction History</h2>
        <TransactionHistory transactions={transactions?.transactions || []} />
      </div>
    </div>
  );
}
