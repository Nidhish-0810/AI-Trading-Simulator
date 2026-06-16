import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, X, TrendingUp, TrendingDown } from 'lucide-react'
import { useMarketStore } from '../../store/marketStore'
import clsx from 'clsx'

const ALL_STOCKS = [
  { symbol: 'AAPL', name: 'Apple Inc.', sector: 'Technology' },
  { symbol: 'MSFT', name: 'Microsoft Corp.', sector: 'Technology' },
  { symbol: 'GOOGL', name: 'Alphabet Inc.', sector: 'Communication' },
  { symbol: 'NVDA', name: 'NVIDIA Corp.', sector: 'Technology' },
  { symbol: 'TSLA', name: 'Tesla Inc.', sector: 'Consumer Discretionary' },
  { symbol: 'AMZN', name: 'Amazon.com Inc.', sector: 'Consumer Discretionary' },
  { symbol: 'META', name: 'Meta Platforms', sector: 'Communication' },
  { symbol: 'AMD', name: 'Advanced Micro Devices', sector: 'Technology' },
  { symbol: 'NFLX', name: 'Netflix Inc.', sector: 'Communication' },
  { symbol: 'JPM', name: 'JPMorgan Chase', sector: 'Financials' },
  { symbol: 'BAC', name: 'Bank of America', sector: 'Financials' },
  { symbol: 'V', name: 'Visa Inc.', sector: 'Financials' },
  { symbol: 'JNJ', name: 'Johnson & Johnson', sector: 'Healthcare' },
  { symbol: 'WMT', name: 'Walmart Inc.', sector: 'Consumer Staples' },
  { symbol: 'DIS', name: 'Walt Disney Co.', sector: 'Communication' },
  { symbol: 'INTC', name: 'Intel Corp.', sector: 'Technology' },
  { symbol: 'CRM', name: 'Salesforce Inc.', sector: 'Technology' },
  { symbol: 'PYPL', name: 'PayPal Holdings', sector: 'Financials' },
  { symbol: 'UBER', name: 'Uber Technologies', sector: 'Consumer Disc.' },
  { symbol: 'SPOT', name: 'Spotify Technology', sector: 'Communication' },
  { symbol: 'COIN', name: 'Coinbase Global', sector: 'Financials' },
  { symbol: 'PLTR', name: 'Palantir Technologies', sector: 'Technology' },
  { symbol: 'SQ', name: 'Block Inc.', sector: 'Financials' },
  { symbol: 'RBLX', name: 'Roblox Corp.', sector: 'Communication' },
]

export default function StockSearchDropdown({ placeholder = 'Search stocks...', onSelect, className }) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [results, setResults] = useState([])
  const ref = useRef(null)
  const navigate = useNavigate()
  const prices = useMarketStore((s) => s.prices)

  useEffect(() => {
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleQuery = (q) => {
    setQuery(q)
    if (!q.trim()) { setResults([]); setOpen(false); return }
    const filtered = ALL_STOCKS.filter(
      (s) => s.symbol.toLowerCase().includes(q.toLowerCase()) || s.name.toLowerCase().includes(q.toLowerCase())
    ).slice(0, 8)
    setResults(filtered)
    setOpen(true)
  }

  const handleSelect = (stock) => {
    setQuery('')
    setOpen(false)
    if (onSelect) onSelect(stock)
    else navigate(`/stock/${stock.symbol}`)
  }

  return (
    <div ref={ref} className={clsx('relative', className)}>
      <div className="relative">
        <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30" />
        <input
          type="text"
          value={query}
          onChange={(e) => handleQuery(e.target.value)}
          placeholder={placeholder}
          onFocus={() => { if (results.length) setOpen(true) }}
          className="w-full bg-white/5 border border-white/10 rounded-xl pl-11 pr-10 py-3 text-white placeholder-white/30 text-sm focus:outline-none focus:border-brand-500/50 focus:bg-white/8 focus:ring-2 focus:ring-brand-500/10 transition-all duration-200"
        />
        {query && (
          <button
            onClick={() => { setQuery(''); setResults([]); setOpen(false) }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
          >
            <X size={15} />
          </button>
        )}
      </div>

      <AnimatePresence>
        {open && results.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full mt-2 left-0 right-0 glass-dark border border-white/8 rounded-xl overflow-hidden shadow-glass-lg z-50"
          >
            {results.map((stock, i) => {
              const p = prices[stock.symbol]
              const isUp = (p?.change_pct ?? 0) >= 0
              return (
                <div
                  key={stock.symbol}
                  onClick={() => handleSelect(stock)}
                  className="flex items-center gap-3 px-4 py-3 hover:bg-white/6 cursor-pointer transition-colors border-b border-white/4 last:border-0"
                >
                  <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent-700 to-brand-600 flex items-center justify-center text-sm font-bold text-white flex-shrink-0">
                    {stock.symbol.charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-white">{stock.symbol}</p>
                    <p className="text-xs text-white/40 truncate">{stock.name}</p>
                  </div>
                  <div className="text-xs text-white/40 hidden sm:block">{stock.sector}</div>
                  {p && (
                    <div className="text-right ml-2">
                      <p className="text-sm font-price font-bold text-white">${p.price?.toFixed(2)}</p>
                      <p className={clsx('text-xs font-price flex items-center gap-0.5 justify-end', isUp ? 'text-gain' : 'text-loss')}>
                        {isUp ? <TrendingUp size={9} /> : <TrendingDown size={9} />}
                        {p.change_pct?.toFixed(2)}%
                      </p>
                    </div>
                  )}
                </div>
              )
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
