import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'

export const useMarketStore = create(
  subscribeWithSelector((set, get) => ({
    prices: {},          // { AAPL: { price, change, change_pct, volume, ... } }
    previousPrices: {},  // for flash detection
    subscriptions: new Set(),
    wsStatus: 'disconnected', // 'connecting' | 'connected' | 'disconnected' | 'error'
    marketStatus: 'open', // 'open' | 'closed' | 'pre' | 'post'
    lastUpdate: null,

    updatePrice: (symbol, data) => {
      set((state) => ({
        previousPrices: {
          ...state.previousPrices,
          [symbol]: state.prices[symbol]?.price,
        },
        prices: {
          ...state.prices,
          [symbol]: { ...state.prices[symbol], ...data, symbol, updatedAt: Date.now() },
        },
        lastUpdate: Date.now(),
      }))
    },

    updatePrices: (pricesMap) => {
      set((state) => {
        const prev = {}
        const next = { ...state.prices }
        Object.entries(pricesMap).forEach(([sym, data]) => {
          prev[sym] = state.prices[sym]?.price
          next[sym] = { ...state.prices[sym], ...data, symbol: sym, updatedAt: Date.now() }
        })
        return { prices: next, previousPrices: { ...state.previousPrices, ...prev }, lastUpdate: Date.now() }
      })
    },

    getPrice: (symbol) => get().prices[symbol] || null,

    getPriceDirection: (symbol) => {
      const state = get()
      const curr = state.prices[symbol]?.price
      const prev = state.previousPrices[symbol]
      if (!curr || !prev) return 'neutral'
      return curr > prev ? 'up' : curr < prev ? 'down' : 'neutral'
    },

    subscribeTo: (symbol) => {
      set((state) => {
        const subs = new Set(state.subscriptions)
        subs.add(symbol)
        return { subscriptions: subs }
      })
    },

    unsubscribeFrom: (symbol) => {
      set((state) => {
        const subs = new Set(state.subscriptions)
        subs.delete(symbol)
        return { subscriptions: subs }
      })
    },

    setWsStatus: (status) => set({ wsStatus: status }),
    setMarketStatus: (status) => set({ marketStatus: status }),

    // Initialize with mock prices for demo
    loadDemoPrices: () => {
      const mockPrices = {
        AAPL:  { price: 189.50, change: 2.30,  change_pct: 1.23,  volume: 58_420_000, market_cap: '2.94T', high: 191.20, low: 187.80 },
        MSFT:  { price: 415.20, change: -3.10, change_pct: -0.74, volume: 22_150_000, market_cap: '3.08T', high: 419.50, low: 413.00 },
        GOOGL: { price: 171.30, change: 1.80,  change_pct: 1.06,  volume: 24_680_000, market_cap: '2.14T', high: 172.80, low: 169.50 },
        NVDA:  { price: 875.60, change: 15.40, change_pct: 1.79,  volume: 41_230_000, market_cap: '2.16T', high: 882.00, low: 861.50 },
        TSLA:  { price: 185.30, change: -4.20, change_pct: -2.22, volume: 89_540_000, market_cap: '590B',  high: 191.00, low: 183.80 },
        AMZN:  { price: 197.80, change: 2.50,  change_pct: 1.28,  volume: 35_120_000, market_cap: '2.07T', high: 199.40, low: 195.20 },
        META:  { price: 501.30, change: 5.80,  change_pct: 1.17,  volume: 18_640_000, market_cap: '1.28T', high: 504.90, low: 495.30 },
        AMD:   { price: 162.40, change: -2.80, change_pct: -1.69, volume: 43_280_000, market_cap: '262B',  high: 167.20, low: 161.80 },
        NFLX:  { price: 698.20, change: 8.40,  change_pct: 1.22,  volume: 8_420_000,  market_cap: '299B',  high: 703.50, low: 690.10 },
        JPM:   { price: 201.30, change: 1.20,  change_pct: 0.60,  volume: 12_380_000, market_cap: '579B',  high: 202.80, low: 200.10 },
        BAC:   { price: 39.80,  change: -0.30, change_pct: -0.75, volume: 45_680_000, market_cap: '312B',  high: 40.50,  low: 39.60  },
        V:     { price: 278.40, change: 2.10,  change_pct: 0.76,  volume: 6_940_000,  market_cap: '568B',  high: 279.80, low: 276.50 },
        JNJ:   { price: 152.60, change: -1.40, change_pct: -0.91, volume: 9_150_000,  market_cap: '366B',  high: 154.20, low: 152.10 },
        WMT:   { price: 68.90,  change: 0.80,  change_pct: 1.17,  volume: 18_760_000, market_cap: '556B',  high: 69.50,  low: 68.20  },
        DIS:   { price: 103.40, change: -1.80, change_pct: -1.71, volume: 14_280_000, market_cap: '189B',  high: 105.80, low: 102.90 },
        INTC:  { price: 30.20,  change: -0.60, change_pct: -1.95, volume: 52_400_000, market_cap: '128B',  high: 31.40,  low: 29.80  },
        CRM:   { price: 268.50, change: 3.40,  change_pct: 1.28,  volume: 7_230_000,  market_cap: '259B',  high: 271.20, low: 265.30 },
        PYPL:  { price: 65.80,  change: 1.20,  change_pct: 1.86,  volume: 16_820_000, market_cap: '68B',   high: 67.20,  low: 64.90  },
        UBER:  { price: 74.30,  change: 0.90,  change_pct: 1.23,  volume: 22_140_000, market_cap: '155B',  high: 75.60,  low: 73.20  },
        SPOT:  { price: 348.90, change: 6.20,  change_pct: 1.81,  volume: 4_680_000,  market_cap: '67B',   high: 352.40, low: 343.10 },
        COIN:  { price: 215.60, change: -8.40, change_pct: -3.75, volume: 12_340_000, market_cap: '54B',   high: 228.40, low: 213.20 },
        PLTR:  { price: 23.80,  change: 0.40,  change_pct: 1.71,  volume: 38_920_000, market_cap: '51B',   high: 24.30,  low: 23.40  },
        SQ:    { price: 67.40,  change: -1.30, change_pct: -1.89, volume: 11_650_000, market_cap: '41B',   high: 69.20,  low: 66.80  },
        RBLX:  { price: 38.20,  change: 0.60,  change_pct: 1.60,  volume: 8_920_000,  market_cap: '21B',   high: 39.10,  low: 37.60  },
      }
      const withUpdatedAt = {}
      Object.entries(mockPrices).forEach(([sym, data]) => {
        withUpdatedAt[sym] = { ...data, symbol: sym, updatedAt: Date.now() }
      })
      set({ prices: withUpdatedAt })
    },
  }))
)
