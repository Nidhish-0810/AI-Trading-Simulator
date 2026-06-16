import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Volume2 } from 'lucide-react'
import { usePriceUpdate } from '../../hooks/usePriceUpdate'
import MiniSparkline from '../charts/MiniSparkline'
import { SectorBadge } from '../ui/Badge'
import clsx from 'clsx'

const COMPANY_NAMES = {
  AAPL: 'Apple Inc.', MSFT: 'Microsoft Corp.', GOOGL: 'Alphabet Inc.',
  NVDA: 'NVIDIA Corp.', TSLA: 'Tesla Inc.', AMZN: 'Amazon.com', META: 'Meta Platforms',
  AMD: 'Advanced Micro Devices', NFLX: 'Netflix Inc.', JPM: 'JPMorgan Chase',
  BAC: 'Bank of America', V: 'Visa Inc.', JNJ: 'Johnson & Johnson',
  WMT: 'Walmart Inc.', DIS: 'Walt Disney', INTC: 'Intel Corp.',
  CRM: 'Salesforce Inc.', PYPL: 'PayPal Holdings', UBER: 'Uber Technologies',
  SPOT: 'Spotify Technology', COIN: 'Coinbase Global', PLTR: 'Palantir Technologies',
  SQ: 'Block Inc.', RBLX: 'Roblox Corp.',
}

const SECTORS = {
  AAPL: 'Technology', MSFT: 'Technology', GOOGL: 'Communication', NVDA: 'Technology',
  TSLA: 'Consumer Discretionary', AMZN: 'Consumer Discretionary', META: 'Communication',
  AMD: 'Technology', NFLX: 'Communication', JPM: 'Financials', BAC: 'Financials',
  V: 'Financials', JNJ: 'Healthcare', WMT: 'Consumer Staples', DIS: 'Communication',
  INTC: 'Technology', CRM: 'Technology', PYPL: 'Financials', UBER: 'Consumer Discretionary',
  SPOT: 'Communication', COIN: 'Financials', PLTR: 'Technology', SQ: 'Financials',
  RBLX: 'Communication',
}

export default function StockCard({ symbol, index = 0 }) {
  const { price, change, changePct, volume, flashClass, isGain, direction } = usePriceUpdate(symbol)

  const displayPrice = price || 0
  const displayChange = change || 0
  const displayChangePct = changePct || 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.04 }}
    >
      <Link to={`/stock/${symbol}`}>
        <div className={clsx(
          'glass-card p-4 glass-hover cursor-pointer',
          'group transition-all duration-250'
        )}>
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent-700 to-brand-600 flex items-center justify-center text-sm font-bold text-white flex-shrink-0 group-hover:scale-105 transition-transform">
                {symbol.charAt(0)}
              </div>
              <div>
                <p className="text-sm font-bold text-white">{symbol}</p>
                <p className="text-[10px] text-white/40 max-w-[120px] truncate">{COMPANY_NAMES[symbol] || symbol}</p>
              </div>
            </div>
            <div className={clsx(
              'text-right transition-colors duration-300',
              flashClass === 'price-up' && 'text-gain',
              flashClass === 'price-down' && 'text-loss'
            )}>
              <p className="text-sm font-price font-bold text-white tabular-nums">
                ${displayPrice.toFixed(2)}
              </p>
              <div className={clsx(
                'flex items-center justify-end gap-0.5 text-xs font-price font-semibold',
                isGain ? 'text-gain' : 'text-loss'
              )}>
                {isGain ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                <span>{isGain ? '+' : ''}{displayChangePct.toFixed(2)}%</span>
              </div>
            </div>
          </div>

          {/* Sparkline */}
          <div className="my-2 -mx-1">
            <MiniSparkline positive={isGain} height={36} />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between mt-2">
            <SectorBadge sector={SECTORS[symbol] || 'Other'} />
            <div className="flex items-center gap-1 text-[10px] text-white/30">
              <Volume2 size={10} />
              <span className="font-price">{((volume || 0) / 1_000_000).toFixed(1)}M</span>
            </div>
          </div>

          {/* Change amount */}
          <div className={clsx(
            'mt-2 pt-2 border-t border-white/4 text-xs font-price flex items-center justify-between',
            isGain ? 'text-gain' : 'text-loss'
          )}>
            <span>{isGain ? '▲' : '▼'} ${Math.abs(displayChange).toFixed(2)} today</span>
            {direction !== 'neutral' && (
              <motion.span
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className={clsx(
                  'w-2 h-2 rounded-full',
                  direction === 'up' ? 'bg-gain animate-pulse' : 'bg-loss animate-pulse'
                )}
              />
            )}
          </div>
        </div>
      </Link>
    </motion.div>
  )
}
