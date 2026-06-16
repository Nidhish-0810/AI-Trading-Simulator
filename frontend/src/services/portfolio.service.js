import api from './api'

export const portfolioService = {
  getPortfolio: async () => {
    const { data } = await api.get('/portfolio')
    return data
  },
  getHoldings: async () => {
    const { data } = await api.get('/portfolio')
    return data.holdings || []
  },
  getHistory: async () => {
    const { data } = await api.get('/portfolio/history')
    return data
  },
  getStats: async () => {
    const { data } = await api.get('/portfolio/summary')
    return data
  },
  getAnalytics: async () => {
    const { data } = await api.get('/portfolio/analytics')
    return data
  },
  getSectorAllocation: async () => {
    const { data } = await api.get('/portfolio/analytics')
    return data.sector_allocation || {}
  },
  getTransactions: async (skip = 0, limit = 50) => {
    const { data } = await api.get('/portfolio/transactions', { params: { skip, limit } })
    return data
  },
  resetPortfolio: async () => {
    const { data } = await api.post('/portfolio/reset')
    return data
  },
}