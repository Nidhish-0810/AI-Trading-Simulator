import { useState, useEffect, useRef } from 'react'
import { useMarketStore } from '../store/marketStore'

export function usePriceUpdate(symbol) {
  const price = useMarketStore((s) => s.prices[symbol])
  const prevPrice = useMarketStore((s) => s.previousPrices[symbol])
  const [flashClass, setFlashClass] = useState('')
  const flashTimer = useRef(null)

  useEffect(() => {
    if (!price?.price || !prevPrice) return
    clearTimeout(flashTimer.current)
    if (price.price > prevPrice) {
      setFlashClass('price-up')
    } else if (price.price < prevPrice) {
      setFlashClass('price-down')
    }
    flashTimer.current = setTimeout(() => setFlashClass(''), 600)
    return () => clearTimeout(flashTimer.current)
  }, [price?.price, prevPrice])

  return {
    price: price?.price,
    change: price?.change,
    changePct: price?.change_pct,
    volume: price?.volume,
    high: price?.high,
    low: price?.low,
    bid: price?.bid,
    ask: price?.ask,
    flashClass,
    direction: price?.price > prevPrice ? 'up' : price?.price < prevPrice ? 'down' : 'neutral',
    isGain: (price?.change_pct ?? 0) >= 0,
  }
}