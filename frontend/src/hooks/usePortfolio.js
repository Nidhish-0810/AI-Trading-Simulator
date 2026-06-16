import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { usePortfolioStore } from '../store/portfolioStore'
import { portfolioService } from '../services/portfolio.service'
import { useAuthStore } from '../store/authStore'

export function usePortfolio() {
  const { setPortfolio, loadDemoData, holdings, balance, totalValue, investedValue, pnl, pnlPct, dayPnl, dayPnlPct, history, isLoaded } = usePortfolioStore()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const accessToken = useAuthStore((s) => s.accessToken)
  const isDemo = accessToken === 'demo-token'

  const query = useQuery({
    queryKey: ['portfolio'],
    queryFn: portfolioService.getPortfolio,
    enabled: isAuthenticated && !isDemo,
    onSuccess: (data) => setPortfolio(data),
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
  })

  useEffect(() => {
    if (isDemo && !isLoaded) {
      loadDemoData()
    }
  }, [isDemo, isLoaded, loadDemoData])

  return {
    holdings,
    balance,
    totalValue,
    investedValue,
    pnl,
    pnlPct,
    dayPnl,
    dayPnlPct,
    history,
    isLoading: query.isLoading && !isDemo,
    isError: query.isError,
    refetch: query.refetch,
  }
}
