import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useMarketStore } from '../../store/marketStore'
import clsx from 'clsx'

function generateOrderBook(price) {
  const bids = []
  const asks = []
  for (let i = 0; i < 12; i++) {
    const bidPrice = price - i * 0.05 - Math.random() * 0.05
    const askPrice = price + 0.03 + i * 0.05 + Math.random() * 0.05
    const bidSize = Math.round(100 + Math.random() * 2000)
    const askSize = Math.round(100 + Math.random() * 2000)
    bids.push({ price: parseFloat(bidPrice.toFixed(2)), size: bidSize, total: 0 })
    asks.push({ price: parseFloat(askPrice.toFixed(2)), size: askSize, total: 0 })
  }
  // Cumulative totals
  let bidTotal = 0, askTotal = 0
  bids.forEach((b) => { bidTotal += b.size; b.total = bidTotal })
  asks.forEach((a) => { askTotal += a.size; a.total = askTotal })
  return { bids, asks }
}

export default function OrderBook({ symbol = 'AAPL' }) {
  const price = useMarketStore((s) => s.prices[symbol]?.price || 185)
  const [book, setBook] = useState(() => generateOrderBook(price))
  const [flash, setFlash] = useState({})

  useEffect(() => {
    const interval = setInterval(() => {
      setBook(generateOrderBook(useMarketStore.getState().prices[symbol]?.price || price))
    }, 2000)
    return () => clearInterval(interval)
  }, [symbol, price])

  const spread = book.asks[0]?.price - book.bids[0]?.price
  const spreadPct = ((spread / book.bids[0]?.price) * 100).toFixed(3)

  const maxBidTotal = Math.max(...book.bids.map((b) => b.total))
  const maxAskTotal = Math.max(...book.asks.map((a) => a.total))

  return (
    <div className="space-y-1">
      {/* Header */}
      <div className="grid grid-cols-3 text-[10px] font-semibold uppercase tracking-wider text-white/30 pb-2 border-b border-white/6">
        <span>Price (USD)</span>
        <span className="text-center">Size</span>
        <span className="text-right">Total</span>
      </div>

      {/* Asks (reversed — lowest at top) */}
      <div className="space-y-0.5">
        {[...book.asks].reverse().map((ask, i) => (
          <div key={i} className="relative grid grid-cols-3 text-xs py-0.5 font-price group cursor-pointer hover:bg-white/4 rounded transition-colors">
            <div
              className="absolute inset-0 right-auto rounded opacity-20"
              style={{ width: `${(ask.total / maxAskTotal) * 100}%`, background: 'rgba(255,71,87,0.4)' }}
            />
            <span className="text-loss relative z-10 pl-1">{ask.price.toFixed(2)}</span>
            <span className="text-white/70 text-center relative z-10">{ask.size.toLocaleString()}</span>
            <span className="text-white/40 text-right relative z-10 pr-1">{ask.total.toLocaleString()}</span>
          </div>
        ))}
      </div>

      {/* Spread */}
      <div className="flex items-center justify-between py-2 px-1 bg-white/4 rounded-lg my-1">
        <span className="text-xs text-white/40">Spread</span>
        <span className="text-xs font-price text-white/70">
          ${spread.toFixed(2)} <span className="text-white/30">({spreadPct}%)</span>
        </span>
        <span className="text-sm font-price font-bold text-white">${price.toFixed(2)}</span>
      </div>

      {/* Bids */}
      <div className="space-y-0.5">
        {book.bids.map((bid, i) => (
          <div key={i} className="relative grid grid-cols-3 text-xs py-0.5 font-price group cursor-pointer hover:bg-white/4 rounded transition-colors">
            <div
              className="absolute inset-0 right-auto rounded opacity-20"
              style={{ width: `${(bid.total / maxBidTotal) * 100}%`, background: 'rgba(0,212,170,0.4)' }}
            />
            <span className="text-gain relative z-10 pl-1">{bid.price.toFixed(2)}</span>
            <span className="text-white/70 text-center relative z-10">{bid.size.toLocaleString()}</span>
            <span className="text-white/40 text-right relative z-10 pr-1">{bid.total.toLocaleString()}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
