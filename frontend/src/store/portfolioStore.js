import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'

export const usePortfolioStore = create(
  subscribeWithSelector((set, get) => ({
    portfolio: null,
    holdings: [],
    balance: 100000,
    totalValue: 100000,
    investedValue: 0,
    pnl: 0,
    pnlPct: 0,
    dayPnl: 0,
    dayPnlPct: 0,
    history: [],
    isLoaded: false,

    setPortfolio: (portfolioData) => {
      const { holdings = [], cash_balance = 0, history = [] } = portfolioData
      const investedValue = holdings.reduce((sum, h) => sum + h.current_value, 0)
      const totalValue = investedValue + cash_balance
      const costBasis = holdings.reduce((sum, h) => sum + h.cost_basis * h.quantity, 0)
      const pnl = totalValue - (costBasis + cash_balance)
      const pnlPct = costBasis > 0 ? (pnl / costBasis) * 100 : 0
      const dayPnl = holdings.reduce((sum, h) => sum + (h.day_change || 0) * h.quantity, 0)
      const dayPnlPct = investedValue > 0 ? (dayPnl / investedValue) * 100 : 0

      set({
        portfolio: portfolioData,
        holdings,
        balance: cash_balance,
        investedValue,
        totalValue,
        pnl,
        pnlPct,
        dayPnl,
        dayPnlPct,
        history,
        isLoaded: true,
      })
    },

    updateHolding: (symbol, updatedHolding) => {
      set((state) => {
        const idx = state.holdings.findIndex((h) => h.symbol === symbol)
        let newHoldings
        if (idx >= 0) {
          newHoldings = [...state.holdings]
          newHoldings[idx] = { ...newHoldings[idx], ...updatedHolding }
        } else {
          newHoldings = [...state.holdings, updatedHolding]
        }
        const investedValue = newHoldings.reduce((sum, h) => sum + h.current_value, 0)
        const totalValue = investedValue + state.balance
        return { holdings: newHoldings, investedValue, totalValue }
      })
    },

    removeHolding: (symbol) => {
      set((state) => {
        const newHoldings = state.holdings.filter((h) => h.symbol !== symbol)
        const investedValue = newHoldings.reduce((sum, h) => sum + h.current_value, 0)
        const totalValue = investedValue + state.balance
        return { holdings: newHoldings, investedValue, totalValue }
      })
    },

    updateBalance: (newBalance) => {
      set((state) => ({
        balance: newBalance,
        totalValue: newBalance + state.investedValue,
      }))
    },

    addHistoryPoint: (point) => {
      set((state) => ({
        history: [...state.history, point].slice(-365),
      }))
    },

    loadDemoData: () => {
      const holdings = [
        { symbol: 'AAPL', company: 'Apple Inc.', quantity: 10, avg_cost: 165.0, current_price: 189.50, current_value: 1895.0, cost_basis: 1650.0, day_change: 2.30, day_change_pct: 1.23, sector: 'Technology' },
        { symbol: 'MSFT', company: 'Microsoft Corp.', quantity: 5, avg_cost: 380.0, current_price: 415.20, current_value: 2076.0, cost_basis: 1900.0, day_change: -3.10, day_change_pct: -0.74, sector: 'Technology' },
        { symbol: 'GOOGL', company: 'Alphabet Inc.', quantity: 8, avg_cost: 155.0, current_price: 171.30, current_value: 1370.4, cost_basis: 1240.0, day_change: 1.80, day_change_pct: 1.06, sector: 'Communication' },
        { symbol: 'NVDA', company: 'NVIDIA Corp.', quantity: 12, avg_cost: 680.0, current_price: 875.60, current_value: 10507.2, cost_basis: 8160.0, day_change: 15.40, day_change_pct: 1.79, sector: 'Technology' },
        { symbol: 'TSLA', company: 'Tesla Inc.', quantity: 20, avg_cost: 220.0, current_price: 185.30, current_value: 3706.0, cost_basis: 4400.0, day_change: -4.20, day_change_pct: -2.22, sector: 'Consumer Discretionary' },
        { symbol: 'AMZN', company: 'Amazon.com Inc.', quantity: 6, avg_cost: 178.0, current_price: 197.80, current_value: 1186.8, cost_basis: 1068.0, day_change: 2.50, day_change_pct: 1.28, sector: 'Consumer Discretionary' },
      ]
      const cash_balance = 73580.50
      get().setPortfolio({ holdings, cash_balance, history: generateDemoHistory() })
    },
  }))
)

function generateDemoHistory() {
  const history = []
  let value = 95000
  const now = Date.now()
  for (let i = 90; i >= 0; i--) {
    value = value * (1 + (Math.random() - 0.45) * 0.02)
    history.push({
      date: new Date(now - i * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      value: Math.round(value * 100) / 100,
    })
  }
  return history
}