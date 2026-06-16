import { useEffect, useRef, useCallback } from 'react'
import { useMarketStore } from '../store/marketStore'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/prices'
const RECONNECT_DELAY = 3000
const MAX_RECONNECT = 5

export function useWebSocket() {
  const wsRef = useRef(null)
  const reconnectCount = useRef(0)
  const reconnectTimer = useRef(null)
  const isMounted = useRef(true)
  const { setWsStatus, updatePrice, subscriptions } = useMarketStore()

  const connect = useCallback(() => {
    if (!isMounted.current) return

    setWsStatus('connecting')
    const token = localStorage.getItem('tradeai-auth')
    let wsUrl = WS_URL
    try {
      const parsed = JSON.parse(token)
      if (parsed?.state?.accessToken && parsed.state.accessToken !== 'demo-token') {
        wsUrl = `${WS_URL}?token=${parsed.state.accessToken}`
      }
    } catch {}

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        if (!isMounted.current) return
        setWsStatus('connected')
        reconnectCount.current = 0

        // Subscribe to all symbols in the store
        const subs = useMarketStore.getState().subscriptions
        if (subs.size > 0) {
          ws.send(JSON.stringify({ type: 'subscribe', symbols: [...subs] }))
        }
      }

      ws.onmessage = (event) => {
        if (!isMounted.current) return
        try {
          const msg = JSON.parse(event.data)
          if (msg.type === 'price_update') {
            updatePrice(msg.symbol, {
              price: msg.price,
              change: msg.change,
              change_pct: msg.change_pct,
              volume: msg.volume,
              bid: msg.bid,
              ask: msg.ask,
              high: msg.high,
              low: msg.low,
            })
          } else if (msg.type === 'batch_update') {
            msg.data?.forEach((item) => updatePrice(item.symbol, item))
          }
        } catch {}
      }

      ws.onerror = () => {
        if (!isMounted.current) return
        setWsStatus('error')
      }

      ws.onclose = () => {
        if (!isMounted.current) return
        setWsStatus('disconnected')
        if (reconnectCount.current < MAX_RECONNECT) {
          reconnectCount.current += 1
          reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY * reconnectCount.current)
        }
      }
    } catch {
      setWsStatus('error')
    }
  }, [setWsStatus, updatePrice])

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current)
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const subscribe = useCallback((symbols) => {
    const arr = Array.isArray(symbols) ? symbols : [symbols]
    arr.forEach((s) => useMarketStore.getState().subscribeTo(s))
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'subscribe', symbols: arr }))
    }
  }, [])

  const unsubscribe = useCallback((symbols) => {
    const arr = Array.isArray(symbols) ? symbols : [symbols]
    arr.forEach((s) => useMarketStore.getState().unsubscribeFrom(s))
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'unsubscribe', symbols: arr }))
    }
  }, [])

  useEffect(() => {
    isMounted.current = true
    // For demo mode, simulate price updates without real WS
    const authData = localStorage.getItem('tradeai-auth')
    let isDemo = false
    try {
      const parsed = JSON.parse(authData)
      isDemo = parsed?.state?.accessToken === 'demo-token'
    } catch {}

    if (isDemo) {
      setWsStatus('connected')
      // Simulate live price updates
      const interval = setInterval(() => {
        if (!isMounted.current) return
        const state = useMarketStore.getState()
        const symbols = Object.keys(state.prices)
        if (symbols.length === 0) return
        const sym = symbols[Math.floor(Math.random() * symbols.length)]
        const cur = state.prices[sym]
        if (!cur) return
        const delta = cur.price * (Math.random() - 0.49) * 0.003
        const newPrice = Math.max(0.01, cur.price + delta)
        updatePrice(sym, {
          price: parseFloat(newPrice.toFixed(2)),
          change: parseFloat((cur.change + delta).toFixed(2)),
          change_pct: parseFloat(((newPrice / (newPrice - cur.change) - 1) * 100).toFixed(2)),
        })
      }, 1500)

      return () => {
        isMounted.current = false
        clearInterval(interval)
      }
    } else {
      connect()
      return () => {
        isMounted.current = false
        disconnect()
      }
    }
  }, [connect, disconnect, setWsStatus, updatePrice])

  return { subscribe, unsubscribe, wsStatus: useMarketStore((s) => s.wsStatus) }
}
