import api from './api'

export const portfolioService = {
  // Full portfolio with holdings and summary
  getPortfolio: async () => {
    const { data } = await api.get('/portfolio')
    return data
  },

  // Holdings come inside the /portfolio response — no separate endpoint
  getHoldings: async () => {
    const { data } = await api.get('/portfolio')
    return data.holdings || []
  },

  // Portfolio value over time
  getHistory: async () => {
    const { data } = await api.get('/portfolio/history')
    return data
  },

  // Stats / summary — now has /stats alias on backend too
  getStats: async () => {
    const { data } = await api.get('/portfolio/summary')
    return data
  },

  // Full analytics (Sharpe, Beta, Alpha, drawdown)
  getAnalytics: async () => {
    const { data } = await api.get('/portfolio/analytics')
    return data
  },

  // Sector allocation is inside analytics
  getSectorAllocation: async () => {
    const { data } = await api.get('/portfolio/analytics')
    return data.sector_allocation || {}
  },

  // Transactions
  getTransactions: async (skip = 0, limit = 50) => {
    const { data } = await api.get('/portfolio/transactions', { params: { skip, limit } })
    return data
  },

  // Reset portfolio to $100,000
  resetPortfolio: async () => {
    const { data } = await api.post('/portfolio/reset')
    return data
  },
}
