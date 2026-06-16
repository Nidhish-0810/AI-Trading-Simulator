import { useEffect } from 'react'
import Navbar from './Navbar'
import Sidebar from './Sidebar'
import { useWebSocket } from '../../hooks/useWebSocket'
import { useMarketStore } from '../../store/marketStore'
import { usePortfolioStore } from '../../store/portfolioStore'
import { useAuthStore } from '../../store/authStore'

export default function Layout({ children }) {
  const { loadDemoPrices } = useMarketStore()
  const { loadDemoData } = usePortfolioStore()
  const { isAuthenticated, accessToken } = useAuthStore()
  const isDemo = accessToken === 'demo-token'

  // Initialize WebSocket
  useWebSocket()

  // Load demo data on mount
  useEffect(() => {
    if (isAuthenticated) {
      loadDemoPrices()
      if (isDemo) loadDemoData()
    }
  }, [isAuthenticated, isDemo, loadDemoPrices, loadDemoData])

  return (
    <div className="flex h-screen bg-dark-950 overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-y-auto p-6 bg-gradient-to-b from-dark-950 to-dark-900">
          {children}
        </main>
      </div>
    </div>
  )
}
