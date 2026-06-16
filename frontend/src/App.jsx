import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Layout from './components/layout/Layout'
import ErrorBoundary from './components/ErrorBoundary'

// Pages
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Markets from './pages/Markets'
import StockDetail from './pages/StockDetail'
import Portfolio from './pages/Portfolio'
import Analytics from './pages/Analytics'
import Backtesting from './pages/Backtesting'
import Leaderboard from './pages/Leaderboard'
import Notifications from './pages/Notifications'

function ProtectedRoute({ children }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  return (
    <Layout>
      <ErrorBoundary title="Page Error" message="This page encountered an error. Try navigating away and back.">
        {children}
      </ErrorBoundary>
    </Layout>
  )
}

function GuestRoute({ children }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
      <Route path="/register" element={<GuestRoute><Register /></GuestRoute>} />

      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/markets" element={<ProtectedRoute><Markets /></ProtectedRoute>} />
      <Route path="/stock/:symbol" element={<ProtectedRoute><StockDetail /></ProtectedRoute>} />
      <Route path="/portfolio" element={<ProtectedRoute><Portfolio /></ProtectedRoute>} />
      <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
      <Route path="/backtest" element={<ProtectedRoute><Backtesting /></ProtectedRoute>} />
      <Route path="/leaderboard" element={<ProtectedRoute><Leaderboard /></ProtectedRoute>} />
      <Route path="/notifications" element={<ProtectedRoute><Notifications /></ProtectedRoute>} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}