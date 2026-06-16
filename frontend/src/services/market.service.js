import api from './api'

export const marketService = {
  search: async (query, limit = 10) => {
    const { data } = await api.get('/market/search', { params: { q: query, limit } })
    return data
  },
  getQuote: async (symbol) => {
    const { data } = await api.get(`/market/stock/${symbol}`)
    return data
  },
  getBatchQuotes: async (symbols) => {
    const { data } = await api.post('/market/quotes', { symbols })
    return data
  },
  getHistory: async (symbol, interval = '1d', period = '1y') => {
    const { data } = await api.get(`/market/stock/${symbol}/history`, {
      params: { interval, period }
    })
    return data
  },
  getMarketSummary: async () => {
    const { data } = await api.get('/market/summary')
    return data
  },
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
  getStockInfo: async (symbol) => {
    const { data } = await api.get(`/market/stock/${symbol}`)
    return data
  },
  getStockNews: async (symbol, limit = 10) => {
    const { data } = await api.get(`/market/stock/${symbol}/news`, { params: { limit } })
    return data
  },
  getOrderBook: async (symbol) => {
    const { data } = await api.get(`/trading/orderbook/${symbol}`)
    return data
  },
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
  getSectors: async () => {
    const { data } = await api.get('/market/stocks', { params: { page_size: 1 } })
    const stocks = await api.get('/market/stocks', { params: { page_size: 100 } })
    const sectors = [...new Set(stocks.data.stocks?.map(s => s.sector).filter(Boolean))]
    return sectors
  },
  getTrending: async () => {
    const { data } = await api.get('/market/trending')
    return data
  },
}