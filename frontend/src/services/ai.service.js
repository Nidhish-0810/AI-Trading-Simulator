import api from './api'

export const aiService = {
  // AI signals for a stock — real endpoint
  getSignals: async (symbol) => {
    const { data } = await api.get(`/ai/signals/${symbol}`)
    return data
  },

  // Sentiment analysis — real endpoint
  getSentiment: async (symbol) => {
    const { data } = await api.get(`/ai/sentiment/${symbol}`)
    return data
  },

  // Market-wide AI overview — real endpoint
  getMarketOverview: async () => {
    const { data } = await api.get('/ai/market-overview')
    return data
  },

  // Backtesting — fixed to POST with JSON body
  runBacktest: async (params) => {
    const { data } = await api.post('/ai/backtest', params)
    return data
  },

  // Backtesting via GET params (alternative)
  runBacktestGet: async (params) => {
    const { data } = await api.get('/ai/backtest', { params })
    return data
  },
}
