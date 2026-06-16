import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import {
  TrendingUp, TrendingDown, AlertCircle,
  ShoppingCart, DollarSign, Clock, RefreshCw
} from 'lucide-react'
import { useMarketStore } from '../../store/marketStore'
import { usePortfolioStore } from '../../store/portfolioStore'
import { useAuthStore } from '../../store/authStore'
import { tradingService } from '../../services/trading.service'
import clsx from 'clsx'

const ORDER_TYPES = ['Market', 'Limit', 'Stop-Loss']

const ORDER_TYPE_MAP = {
  'Market': 'market',
  'Limit': 'limit',
  'Stop-Loss': 'stop_loss',
}

export default function TradingPanel({ defaultSymbol = 'AAPL' }) {
  const [symbol, setSymbol] = useState(defaultSymbol)
  const [side, setSide] = useState('buy')
  const [orderType, setOrderType] = useState('Market')
  const [quantity, setQuantity] = useState('')
  const [limitPrice, setLimitPrice] = useState('')
  const [stopPrice, setStopPrice] = useState('')
  const [confirmed, setConfirmed] = useState(false)

  const prices = useMarketStore((s) => s.prices)
  const { balance, updateBalance } = usePortfolioStore()
  const { isAuthenticated, accessToken } = useAuthStore()
  const isDemo = accessToken === 'demo-token'
  const queryClient = useQueryClient()

  const currentPrice = prices[symbol]?.price || 0
  const qty = parseFloat(quantity) || 0
  const execPrice = orderType === 'Market' ? currentPrice : parseFloat(limitPrice) || currentPrice
  const totalCost = qty * execPrice
  const commission = totalCost * 0.001
  const totalWithFee = side === 'buy' ? totalCost + commission : totalCost - commission
  const canAfford = balance >= totalWithFee
  const isGain = (prices[symbol]?.change_pct ?? 0) >= 0

  // Load recent orders
  const { data: recentOrders, refetch: refetchOrders } = useQuery({
    queryKey: ['recent-orders'],
    queryFn: () => tradingService.getOrders({ limit: 3 }),
    enabled: isAuthenticated && !isDemo,
    staleTime: 30_000,
  })

  useEffect(() => {
    setSymbol(defaultSymbol)
    setLimitPrice(prices[defaultSymbol]?.price?.toFixed(2) || '')
    setStopPrice(((prices[defaultSymbol]?.price || 0) * 0.95).toFixed(2))
    setConfirmed(false)
  }, [defaultSymbol, prices])

  const mutation = useMutation({
    mutationFn: () => {
      if (isDemo) {
        // Demo mode: simulate trade locally
        return Promise.resolve({
          id: Date.now().toString(),
          symbol,
          side,
          quantity: qty,
          executed_price: execPrice,
          order_type: ORDER_TYPE_MAP[orderType],
          status: 'filled',
        })
      }
      // Real mode: call backend
      const payload = {
        symbol: symbol.toUpperCase(),
        quantity: qty,
        order_type: ORDER_TYPE_MAP[orderType],
        side,
      }
      if (orderType === 'Limit') payload.price = parseFloat(limitPrice)
      if (orderType === 'Stop-Loss') payload.stop_price = parseFloat(stopPrice)
      return tradingService.placeOrder(payload)
    },
    onSuccess: (data) => {
      const filledPrice = data.executed_price || execPrice
      toast.success(
        `✅ ${side === 'buy' ? 'Bought' : 'Sold'} ${qty} ${symbol} @ $${filledPrice.toFixed(2)}`,
        { duration: 4000 }
      )
      if (isDemo) {
        // Update demo balance locally
        updateBalance(side === 'buy' ? balance - totalWithFee : balance + totalWithFee)
      }
      setQuantity('')
      setConfirmed(false)
      // Invalidate queries so portfolio updates
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      refetchOrders()
    },
    onError: (err) => {
      const msg = err.message || err.response?.data?.detail || 'Order failed. Please try again.'
      toast.error(`❌ ${msg}`, { duration: 5000 })
      setConfirmed(false)
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!qty || qty <= 0) { toast.error('Please enter a valid quantity'); return }
    if (!currentPrice && orderType === 'Market') { toast.error('Price data not available yet'); return }
    if (orderType === 'Limit' && (!limitPrice || parseFloat(limitPrice) <= 0)) {
      toast.error('Please enter a valid limit price'); return
    }
    if (orderType === 'Stop-Loss' && (!stopPrice || parseFloat(stopPrice) <= 0)) {
      toast.error('Please enter a valid stop price'); return
    }
    if (side === 'buy' && !canAfford) { toast.error('Insufficient balance'); return }
    if (!confirmed) { setConfirmed(true); return }
    mutation.mutate()
  }

  return (
    <div className="glass-card p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-base font-bold text-white">Place Order</h3>
        <div className="text-right">
          <p className="text-xs text-white/40">Available</p>
          <p className="text-sm font-price font-bold text-white">
            ${balance?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
        </div>
      </div>

      {/* Stock Info */}
      <div className="flex items-center justify-between p-3 bg-white/4 rounded-xl border border-white/6">
        <div>
          <p className="text-lg font-bold text-white">{symbol}</p>
          <p className="text-xs text-white/40">Stock</p>
        </div>
        <div className="text-right">
          <p className="text-lg font-price font-bold text-white">
            ${currentPrice ? currentPrice.toFixed(2) : '—'}
          </p>
          <p className={clsx('text-xs font-price', isGain ? 'text-gain' : 'text-loss')}>
            {isGain ? '+' : ''}{prices[symbol]?.change_pct?.toFixed(2) || '0.00'}%
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Buy/Sell Toggle */}
        <div className="grid grid-cols-2 gap-2">
          {['buy', 'sell'].map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => { setSide(s); setConfirmed(false) }}
              className={clsx(
                'py-2.5 rounded-xl font-semibold text-sm transition-all duration-200',
                side === s
                  ? s === 'buy'
                    ? 'bg-gain/20 text-gain border border-gain/40'
                    : 'bg-loss/20 text-loss border border-loss/40'
                  : 'bg-white/5 text-white/40 border border-white/8 hover:border-white/20'
              )}
            >
              <span className="flex items-center justify-center gap-1.5">
                {s === 'buy' ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                {s === 'buy' ? 'Buy' : 'Sell'}
              </span>
            </button>
          ))}
        </div>

        {/* Order Type */}
        <div className="flex gap-1 bg-white/4 rounded-xl p-1">
          {ORDER_TYPES.map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => { setOrderType(type); setConfirmed(false) }}
              className={clsx(
                'flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all duration-150',
                orderType === type
                  ? 'bg-white/10 text-white border border-white/12'
                  : 'text-white/40 hover:text-white/70'
              )}
            >
              {type}
            </button>
          ))}
        </div>

        {/* Quantity */}
        <div>
          <label className="text-xs font-medium text-white/60 mb-1.5 block">Shares</label>
          <input
            type="number"
            value={quantity}
            onChange={(e) => { setQuantity(e.target.value); setConfirmed(false) }}
            placeholder="0"
            min="1"
            step="1"
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white font-price text-sm placeholder-white/20 focus:outline-none focus:border-brand-500/50 focus:ring-2 focus:ring-brand-500/10 transition-all"
          />
        </div>

        {/* Quick quantity buttons */}
        {currentPrice > 0 && side === 'buy' && (
          <div className="flex gap-2">
            {[25, 50, 100].map((pct) => {
              const shares = Math.floor((balance * pct / 100) / (execPrice * 1.001))
              return (
                <button
                  key={pct}
                  type="button"
                  disabled={shares <= 0}
                  onClick={() => { setQuantity(String(shares || 1)); setConfirmed(false) }}
                  className="flex-1 text-xs py-1.5 rounded-lg bg-white/5 text-white/40 hover:text-white/70 hover:bg-white/10 transition-all disabled:opacity-30"
                >
                  {pct}%
                </button>
              )
            })}
            <button
              type="button"
              onClick={() => {
                const max = Math.floor(balance / (execPrice * 1.001))
                setQuantity(String(max || 1))
                setConfirmed(false)
              }}
              className="flex-1 text-xs py-1.5 rounded-lg bg-white/5 text-white/40 hover:text-white/70 hover:bg-white/10 transition-all"
            >
              Max
            </button>
          </div>
        )}

        {/* Limit / Stop Price */}
        {orderType !== 'Market' && (
          <div>
            <label className="text-xs font-medium text-white/60 mb-1.5 block">
              {orderType === 'Limit' ? 'Limit Price' : 'Stop Price'}
            </label>
            <div className="relative">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/30 text-sm">$</span>
              <input
                type="number"
                value={orderType === 'Limit' ? limitPrice : stopPrice}
                onChange={(e) => {
                  orderType === 'Limit' ? setLimitPrice(e.target.value) : setStopPrice(e.target.value)
                  setConfirmed(false)
                }}
                step="0.01"
                min="0.01"
                className="w-full bg-white/5 border border-white/10 rounded-xl pl-8 pr-4 py-2.5 text-white font-price text-sm focus:outline-none focus:border-brand-500/50 focus:ring-2 focus:ring-brand-500/10 transition-all"
              />
            </div>
          </div>
        )}

        {/* Order Summary */}
        {qty > 0 && (
          <AnimatePresence>
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-white/4 rounded-xl p-3 space-y-2 border border-white/6"
            >
              {[
                ['Shares', `${qty}`],
                ['Est. Price', `$${execPrice.toFixed(2)}`],
                ['Subtotal', `$${totalCost.toFixed(2)}`],
                ['Commission (0.1%)', `$${commission.toFixed(2)}`],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between text-xs">
                  <span className="text-white/50">{k}</span>
                  <span className="text-white font-price">{v}</span>
                </div>
              ))}
              <div className="border-t border-white/8 pt-2 flex justify-between">
                <span className="text-xs font-semibold text-white/70">
                  {side === 'buy' ? 'Total Cost' : 'You Receive'}
                </span>
                <span className={clsx(
                  'text-sm font-price font-bold',
                  side === 'buy' ? (canAfford ? 'text-white' : 'text-loss') : 'text-gain'
                )}>
                  ${totalWithFee.toFixed(2)}
                </span>
              </div>
              {side === 'buy' && !canAfford && (
                <p className="text-xs text-loss flex items-center gap-1">
                  <AlertCircle size={11} /> Insufficient funds (need ${(totalWithFee - balance).toFixed(2)} more)
                </p>
              )}
            </motion.div>
          </AnimatePresence>
        )}

        {/* Confirm / Submit */}
        <button
          type="submit"
          disabled={mutation.isPending || (side === 'buy' && !canAfford && qty > 0)}
          className={clsx(
            'w-full py-3 rounded-xl font-bold text-sm transition-all duration-200 flex items-center justify-center gap-2',
            mutation.isPending && 'opacity-70 cursor-wait',
            confirmed
              ? side === 'buy'
                ? 'bg-gain text-dark-900 hover:brightness-110'
                : 'bg-loss text-white hover:brightness-110'
              : side === 'buy'
                ? 'bg-gain/20 text-gain border border-gain/40 hover:bg-gain/30'
                : 'bg-loss/20 text-loss border border-loss/40 hover:bg-loss/30',
            side === 'buy' && !canAfford && qty > 0 && 'opacity-50 cursor-not-allowed'
          )}
        >
          {mutation.isPending ? (
            <span className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
              Processing...
            </span>
          ) : confirmed ? (
            <span className="flex items-center gap-2">
              {side === 'buy' ? <ShoppingCart size={16} /> : <DollarSign size={16} />}
              Confirm {side === 'buy' ? 'Buy' : 'Sell'}
            </span>
          ) : (
            <span>Review {side === 'buy' ? 'Buy' : 'Sell'} Order</span>
          )}
        </button>

        {confirmed && (
          <button
            type="button"
            onClick={() => setConfirmed(false)}
            className="w-full text-xs text-white/40 hover:text-white/70 transition-colors"
          >
            Cancel
          </button>
        )}
      </form>

      {/* Recent Orders — real data */}
      <div className="border-t border-white/6 pt-4">
        <p className="text-xs font-semibold text-white/50 mb-2.5 flex items-center gap-1.5">
          <Clock size={12} /> Recent Orders
        </p>
        <div className="space-y-2">
          {recentOrders && recentOrders.length > 0 ? (
            recentOrders.slice(0, 3).map((order) => (
              <div key={order.id} className="flex items-center gap-2.5 text-xs">
                <span className={clsx(
                  'px-1.5 py-0.5 rounded font-semibold',
                  order.side === 'buy' ? 'bg-gain/15 text-gain' : 'bg-loss/15 text-loss'
                )}>
                  {order.side?.toUpperCase()}
                </span>
                <span className="font-semibold text-white">{order.symbol}</span>
                <span className="text-white/40">
                  {order.quantity} @ ${order.executed_price?.toFixed(2) || order.price?.toFixed(2) || '—'}
                </span>
                <span className={clsx(
                  'ml-auto px-1.5 py-0.5 rounded text-[10px]',
                  order.status === 'filled' ? 'bg-gain/10 text-gain/70' : 'bg-white/5 text-white/30'
                )}>
                  {order.status}
                </span>
              </div>
            ))
          ) : (
            <p className="text-xs text-white/25 italic">No orders yet</p>
          )}
        </div>
      </div>
    </div>
  )
}
