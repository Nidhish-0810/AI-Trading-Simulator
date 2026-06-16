import api from './api'

export const marketService = {
  // Search
  search: async (query, limit = 10) => {
    const { data } = await api.get('/market/search', { params: { q: query, limit } })
    return data
  },

  // Quote — fixed to match backend route /market/stock/:symbol
  getQuote: async (symbol) => {
    const { data } = await api.get(`/market/stock/${symbol}`)
    return data
  },

  // Batch quotes — POST /market/quotes
  getBatchQuotes: async (symbols) => {
    const { data } = await api.post('/market/quotes', { symbols })
    return data
  },

  // Historical data — fixed to match backend /market/stock/:symbol/history
  getHistory: async (symbol, interval = '1d', period = '1y') => {
    const { data } = await api.get(`/market/stock/${symbol}/history`, {
      params: { interval, period }
    })
    return data
  },

  // Market overview
  getMarketSummary: async () => {
    const { data } = await api.get('/market/summary')
    return data
  },

  // Movers — now backed by real backend endpoints
  getGainers: async (limit = 10) => {
    const { data } = await api.get('/market/gainers', { params: { limit } })
    return data
  },

  getLosers: async (limit = 10) => {
    const { data } = await api.get('/market/losers', { params: { limit } })
    return data
  },

  getMostActive: async (limit = 10) => {
    const { data } = await api.get('/market/active', { params: { limit } })
    return data
  },

  // Stock details — fixed route
  getStockInfo: async (symbol) => {
    const { data } = await api.get(`/market/stock/${symbol}`)
    return data
  },

  // News — fixed route
  getStockNews: async (symbol, limit = 10) => {
    const { data } = await api.get(`/market/stock/${symbol}/news`, { params: { limit } })
    return data
  },

  // Order book — correct route is under /trading/
  getOrderBook: async (symbol) => {
    const { data } = await api.get(`/trading/orderbook/${symbol}`)
    return data
  },

  // Watchlist
  getWatchlist: async () => {
    const { data } = await api.get('/market/watchlist')
    return data
  },

  addToWatchlist: async (symbol) => {
    const { data } = await api.post(`/market/watchlist/${symbol}`)
    return data
  },

  removeFromWatchlist: async (symbol) => {
    await api.delete(`/market/watchlist/${symbol}`)
  },

  // Sectors
  getSectors: async () => {
    const { data } = await api.get('/market/stocks', { params: { page_size: 1 } })
    // Extract unique sectors from stocks catalogue
    const stocks = await api.get('/market/stocks', { params: { page_size: 100 } })
    const sectors = [...new Set(stocks.data.stocks?.map(s => s.sector).filter(Boolean))]
    return sectors
  },

  // Trending
  getTrending: async () => {
    const { data } = await api.get('/market/trending')
    return data
  },
}
