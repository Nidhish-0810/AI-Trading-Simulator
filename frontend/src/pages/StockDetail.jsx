import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { TrendingUp, TrendingDown, Star, StarOff, BarChart2, Brain, Newspaper, BookOpen } from 'lucide-react';
import { marketService } from '../services/market.service';
import { aiService } from '../services/ai.service';
import { formatPrice, formatPercent, formatVolume, formatMarketCap, getChangeColor, getSignalColor } from '../utils/format';
import CandlestickChart from '../components/charts/CandlestickChart';
import TradingPanel from '../components/trading/TradingPanel';
import OrderBook from '../components/trading/OrderBook';
import AISignalsWidget from '../components/ai/AISignalsWidget';
import SentimentWidget from '../components/ai/SentimentWidget';
import { Skeleton } from '../components/ui/Skeleton';
import toast from 'react-hot-toast';

const TABS = [
  { id: 'chart', label: 'Chart', Icon: BarChart2 },
  { id: 'signals', label: 'AI Signals', Icon: Brain },
  { id: 'news', label: 'News', Icon: Newspaper },
  { id: 'orderbook', label: 'Order Book', Icon: BookOpen },
];

const INTERVALS = ['1D', '1W', '1M', '3M', '6M', '1Y'];

export default function StockDetail() {
  const { symbol } = useParams();
  const [tab, setTab] = useState('chart');
  const [interval, setInterval] = useState('1M');
  const [inWatchlist, setInWatchlist] = useState(false);

  const PERIOD_MAP = { '1D': '1d', '1W': '5d', '1M': '1mo', '3M': '3mo', '6M': '6mo', '1Y': '1y' };

  const { data: quote, isLoading: quoteLoading } = useQuery({
    queryKey: ['quote', symbol],
    queryFn: () => marketService.getQuote(symbol),
    refetchInterval: 15000,
  });

  const { data: history, isLoading: histLoading } = useQuery({
    queryKey: ['history', symbol, interval],
    queryFn: () => marketService.getHistory(symbol, PERIOD_MAP[interval] || '1mo'),
  });

  const { data: signals, isLoading: signalsLoading } = useQuery({
    queryKey: ['signals', symbol],
    queryFn: () => aiService.getSignals(symbol),
    enabled: tab === 'signals',
  });

  const { data: sentiment } = useQuery({
    queryKey: ['sentiment', symbol],
    queryFn: () => aiService.getSentiment(symbol),
    enabled: tab === 'signals' || tab === 'news',
  });

  const { data: news } = useQuery({
    queryKey: ['news', symbol],
    queryFn: () => marketService.getNews(symbol),
    enabled: tab === 'news',
  });

  const toggleWatchlist = async () => {
    try {
      if (inWatchlist) {
        await marketService.removeFromWatchlist(symbol);
        setInWatchlist(false);
        toast.success(`${symbol} removed from watchlist`);
      } else {
        await marketService.addToWatchlist(symbol);
        setInWatchlist(true);
        toast.success(`${symbol} added to watchlist ⭐`);
      }
    } catch (e) {
      toast.error('Failed to update watchlist');
    }
  };

  const price = quote?.price ?? 0;
  const change = quote?.change ?? 0;
  const changePct = quote?.change_pct ?? 0;
  const isUp = change >= 0;

  return (
    <div className="flex gap-6 h-full">
      <div className="flex-1 min-w-0 space-y-4">
        <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
          {quoteLoading ? (
            <Skeleton className="h-24" />
          ) : (
            <>
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <h1 className="text-3xl font-black text-white font-mono">{symbol}</h1>
                    <span className="text-sm text-gray-400">{quote?.name || symbol}</span>
                    {quote?.sector && (
                      <span className="px-2 py-0.5 rounded-full text-xs border border-violet-500/30 bg-violet-500/10 text-violet-300">
                        {quote.sector}
                      </span>
                    )}
                  </div>
                  <div className="flex items-baseline gap-3">
                    <span className="font-mono text-4xl font-black text-white">{formatPrice(price)}</span>
                    <span className={`font-mono text-lg font-bold ${getChangeColor(change)}`}>
                      {change >= 0 ? '+' : ''}{formatPrice(change)} ({formatPercent(changePct)})
                    </span>
                    {isUp
                      ? <TrendingUp className="w-6 h-6 text-emerald-400" />
                      : <TrendingDown className="w-6 h-6 text-red-400" />
                    }
                  </div>
                </div>
                <button onClick={toggleWatchlist} className="p-2 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 transition-colors">
                  {inWatchlist
                    ? <Star className="w-5 h-5 text-yellow-400 fill-yellow-400" />
                    : <StarOff className="w-5 h-5 text-gray-400" />
                  }
                </button>
              </div>

              <div className="grid grid-cols-3 md:grid-cols-6 gap-3 mt-4">
                {[
                  { label: 'Market Cap', value: formatMarketCap(quote?.market_cap) },
                  { label: 'P/E Ratio', value: quote?.pe_ratio?.toFixed(1) || 'N/A' },
                  { label: '52W High', value: formatPrice(quote?.week52_high) },
                  { label: '52W Low', value: formatPrice(quote?.week52_low) },
                  { label: 'Volume', value: formatVolume(quote?.volume) },
                  { label: 'Avg Volume', value: formatVolume(quote?.avg_volume) },
                ].map(({ label, value }) => (
                  <div key={label} className="rounded-lg bg-white/5 p-2.5">
                    <p className="text-xs text-gray-500 mb-0.5">{label}</p>
                    <p className="font-mono text-sm font-semibold text-white">{value}</p>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="flex gap-2">
          {TABS.map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                tab === id
                  ? 'bg-violet-600 text-white shadow-lg shadow-violet-500/20'
                  : 'bg-white/5 border border-white/10 text-gray-400 hover:text-white hover:bg-white/10'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
          {tab === 'chart' && (
            <>
              <div className="flex gap-2 mb-4">
                {INTERVALS.map(iv => (
                  <button key={iv} onClick={() => setInterval(iv)}
                    className={`px-3 py-1 rounded-lg text-xs font-mono font-bold transition-all ${
                      interval === iv ? 'bg-violet-600 text-white' : 'bg-white/5 text-gray-500 hover:text-white border border-white/10'
                    }`}
                  >{iv}</button>
                ))}
              </div>
              {histLoading ? <Skeleton className="h-80" /> : (
                <CandlestickChart data={history?.history || []} symbol={symbol} />
              )}
            </>
          )}

          {tab === 'signals' && (
            <div className="space-y-4">
              {signalsLoading ? <Skeleton className="h-64" /> : <AISignalsWidget signals={signals} />}
              {sentiment && <SentimentWidget sentiment={sentiment} />}
            </div>
          )}

          {tab === 'news' && (
            <div className="space-y-3">
              {(news?.news || []).map((item, i) => (
                <a key={i} href={item.link} target="_blank" rel="noopener noreferrer"
                  className="flex items-start gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors group">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white group-hover:text-violet-300 transition-colors line-clamp-2">{item.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-gray-500">{item.publisher}</span>
                      {item.sentiment_score != null && (
                        <span className={`text-xs font-mono px-1.5 py-0.5 rounded ${item.sentiment_score > 0.1 ? 'bg-emerald-500/20 text-emerald-400' : item.sentiment_score < -0.1 ? 'bg-red-500/20 text-red-400' : 'bg-gray-500/20 text-gray-400'}`}>
                          {item.sentiment_score > 0.1 ? '↑ Positive' : item.sentiment_score < -0.1 ? '↓ Negative' : '→ Neutral'}
                        </span>
                      )}
                    </div>
                  </div>
                </a>
              ))}
              {(!news?.news || news.news.length === 0) && (
                <p className="text-center text-gray-500 py-10">No recent news available</p>
              )}
            </div>
          )}

          {tab === 'orderbook' && <OrderBook symbol={symbol} currentPrice={price} />}
        </div>
      </div>

      <div className="hidden xl:block w-80 flex-shrink-0">
        <div className="sticky top-6">
          <TradingPanel symbol={symbol} currentPrice={price} />
        </div>
      </div>
    </div>
  );
}