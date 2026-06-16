import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Search, TrendingUp, TrendingDown, Zap, Star } from 'lucide-react';
import { marketService } from '../services/market.service';
import StockCard from '../components/market/StockCard';
import { Skeleton } from '../components/ui/Skeleton';
import { formatPrice, formatPercent, getChangeColor } from '../utils/format';

const FILTER_TABS = ['All', 'Gainers', 'Losers', 'Most Active', 'Watchlist'];
const SECTORS = ['All Sectors', 'Technology', 'Healthcare', 'Finance', 'Energy', 'Consumer', 'Industrial'];

const MarketIndex = ({ name, value, change, changePct }) => (
  <div className="flex items-center gap-4 px-5 py-3 rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm">
    <div>
      <p className="text-xs text-gray-500">{name}</p>
      <p className="font-mono text-base font-bold text-white">{value?.toLocaleString()}</p>
    </div>
    <div className={`text-sm font-mono font-medium ${getChangeColor(changePct)}`}>
      {formatPercent(changePct)}
    </div>
  </div>
);

export default function Markets() {
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState('All');
  const [sector, setSector] = useState('All Sectors');
  const [sortBy, setSortBy] = useState('market_cap');

  const { data: stocks, isLoading } = useQuery({
    queryKey: ['stocks', { search, sector }],
    queryFn: () => marketService.getStocks({ search, sector: sector === 'All Sectors' ? '' : sector }),
    refetchInterval: 30000,
  });

  const { data: summary } = useQuery({
    queryKey: ['market-summary'],
    queryFn: marketService.getSummary,
    refetchInterval: 60000,
  });

  const filtered = (stocks?.stocks || []).filter(s => {
    if (activeTab === 'Gainers') return s.change_pct > 0;
    if (activeTab === 'Losers') return s.change_pct < 0;
    if (activeTab === 'Most Active') return s.volume > 10_000_000;
    return true;
  }).sort((a, b) => {
    if (sortBy === 'change_pct') return b.change_pct - a.change_pct;
    if (sortBy === 'price') return b.price - a.price;
    if (sortBy === 'volume') return (b.volume || 0) - (a.volume || 0);
    return (b.market_cap || 0) - (a.market_cap || 0);
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-black text-white">Markets</h1>
        <p className="text-gray-500 text-sm mt-0.5">Real-time stock data • 15-min delayed</p>
      </div>

      <div className="flex gap-3 overflow-x-auto pb-2">
        {summary ? (
          Object.entries(summary).map(([name, data]) => (
            <MarketIndex key={name} name={name} value={data.price} changePct={data.change_pct} />
          ))
        ) : (
          [1,2,3,4].map(i => <Skeleton key={i} className="h-16 w-40 flex-shrink-0 rounded-xl" />)
        )}
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search stocks by symbol or name..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-600 focus:border-violet-500 outline-none transition-all text-sm"
          />
        </div>
        <select
          value={sortBy}
          onChange={e => setSortBy(e.target.value)}
          className="px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-gray-300 text-sm focus:border-violet-500 outline-none"
        >
          <option value="market_cap">Sort: Market Cap</option>
          <option value="change_pct">Sort: Change %</option>
          <option value="price">Sort: Price</option>
          <option value="volume">Sort: Volume</option>
        </select>
      </div>

      <div className="flex items-center gap-2 overflow-x-auto">
        {FILTER_TABS.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
              activeTab === tab
                ? 'bg-violet-600 text-white shadow-lg shadow-violet-500/20'
                : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white border border-white/10'
            }`}
          >
            {tab === 'Gainers' && <TrendingUp className="inline w-3.5 h-3.5 mr-1 text-emerald-400" />}
            {tab === 'Losers' && <TrendingDown className="inline w-3.5 h-3.5 mr-1 text-red-400" />}
            {tab === 'Most Active' && <Zap className="inline w-3.5 h-3.5 mr-1 text-yellow-400" />}
            {tab}
          </button>
        ))}
      </div>

      <div className="flex gap-2 overflow-x-auto">
        {SECTORS.map(s => (
          <button
            key={s}
            onClick={() => setSector(s)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-all whitespace-nowrap border ${
              sector === s
                ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300'
                : 'bg-white/5 border-white/10 text-gray-500 hover:text-gray-300'
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({length: 12}).map((_, i) => (
            <Skeleton key={i} className="h-44 rounded-2xl" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <Search className="w-10 h-10 mx-auto mb-3 opacity-40" />
          <p>No stocks found matching your filters</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filtered.map(stock => (
            <Link key={stock.symbol} to={`/stock/${stock.symbol}`}>
              <StockCard stock={stock} />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}