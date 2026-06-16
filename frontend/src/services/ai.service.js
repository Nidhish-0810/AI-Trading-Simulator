import api from './api'

export const aiService = {
  getSignals: async (symbol) => {
    const { data } = await api.get(`/ai/signals/${symbol}`)
    return data
  },
  getSentiment: async (symbol) => {
    const { data } = await api.get(`/ai/sentiment/${symbol}`)
    return data
  },
  getMarketOverview: async () => {
    const { data } = await api.get('/ai/market-overview')
    return data
  },
  runBacktest: async (params) => {
    const { data } = await api.post('/ai/backtest', params)
    return data
  },
  runBacktestGet: async (params) => {
    const { data } = await api.get('/ai/backtest', { params })
    return data
  },
}