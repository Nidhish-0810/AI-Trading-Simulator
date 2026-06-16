import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search, Bell, ChevronDown, User, Settings, LogOut,
  Wifi, WifiOff, TrendingUp, Zap
} from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { usePortfolioStore } from '../../store/portfolioStore'
import { useMarketStore } from '../../store/marketStore'
import clsx from 'clsx'

const STOCKS_DB = [
  { symbol: 'AAPL', name: 'Apple Inc.', sector: 'Technology' },
  { symbol: 'MSFT', name: 'Microsoft Corp.', sector: 'Technology' },
  { symbol: 'GOOGL', name: 'Alphabet Inc.', sector: 'Communication' },
  { symbol: 'NVDA', name: 'NVIDIA Corp.', sector: 'Technology' },
  { symbol: 'TSLA', name: 'Tesla Inc.', sector: 'Consumer Discretionary' },
  { symbol: 'AMZN', name: 'Amazon.com Inc.', sector: 'Consumer Discretionary' },
  { symbol: 'META', name: 'Meta Platforms Inc.', sector: 'Communication' },
  { symbol: 'AMD', name: 'Advanced Micro Devices', sector: 'Technology' },
  { symbol: 'NFLX', name: 'Netflix Inc.', sector: 'Communication' },
  { symbol: 'JPM', name: 'JPMorgan Chase & Co.', sector: 'Financials' },
]

function NotificationItem({ title, message, time, type }) {
  const typeColor = {
    trade: 'bg-brand-500/20 text-brand-400',
    alert: 'bg-gold/20 text-gold',
    system: 'bg-accent-500/20 text-accent-400',
  }
  return (
    <div className="flex items-start gap-3 px-4 py-3 hover:bg-white/4 transition-colors cursor-pointer">
      <span className={clsx('w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 text-xs', typeColor[type] || typeColor.system)}>
        <Zap size={14} />
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white">{title}</p>
        <p className="text-xs text-white/50 mt-0.5 truncate">{message}</p>
        <p className="text-xs text-white/30 mt-1">{time}</p>
      </div>
    </div>
  )
}

export default function Navbar() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const { totalValue, pnl, pnlPct } = usePortfolioStore()
  const wsStatus = useMarketStore((s) => s.wsStatus)

  const [search, setSearch] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [showSearch, setShowSearch] = useState(false)
  const [showNotifications, setShowNotifications] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const searchRef = useRef(null)
  const notifRef = useRef(null)
  const userRef = useRef(null)

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClickOutside(e) {
      if (searchRef.current && !searchRef.current.contains(e.target)) setShowSearch(false)
      if (notifRef.current && !notifRef.current.contains(e.target)) setShowNotifications(false)
      if (userRef.current && !userRef.current.contains(e.target)) setShowUserMenu(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSearch = (q) => {
    setSearch(q)
    if (q.length < 1) { setSearchResults([]); setShowSearch(false); return }
    const results = STOCKS_DB.filter(
      (s) => s.symbol.toLowerCase().includes(q.toLowerCase()) || s.name.toLowerCase().includes(q.toLowerCase())
    ).slice(0, 6)
    setSearchResults(results)
    setShowSearch(true)
  }

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const isPositive = pnl >= 0
  const wsConnected = wsStatus === 'connected'

  return (
    <header className="h-16 glass-dark border-b border-white/8 flex items-center px-6 gap-4 sticky top-0 z-40">
      {/* Logo */}
      <Link to="/dashboard" className="flex items-center gap-2.5 flex-shrink-0">
        <div className="w-8 h-8 bg-gradient-to-br from-accent-600 to-brand-500 rounded-lg flex items-center justify-center shadow-accent-sm">
          <TrendingUp size={16} className="text-white" />
        </div>
        <span className="text-lg font-bold gradient-text hidden sm:block">TradeAI</span>
      </Link>

      {/* Search */}
      <div ref={searchRef} className="relative flex-1 max-w-md">
        <div className="relative">
          <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/30" />
          <input
            type="text"
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search stocks..."
            className="w-full bg-white/5 border border-white/8 rounded-xl pl-10 pr-4 py-2 text-sm text-white placeholder-white/25 focus:outline-none focus:border-brand-500/40 focus:bg-white/8 transition-all duration-200"
          />
        </div>

        <AnimatePresence>
          {showSearch && searchResults.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -8, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.97 }}
              transition={{ duration: 0.15 }}
              className="absolute top-full mt-2 w-full glass-dark rounded-xl overflow-hidden shadow-glass-lg border border-white/8 z-50"
            >
              {searchResults.map((stock) => {
                const prices = useMarketStore.getState().prices[stock.symbol]
                return (
                  <div
                    key={stock.symbol}
                    onClick={() => { navigate(`/stock/${stock.symbol}`); setShowSearch(false); setSearch('') }}
                    className="flex items-center gap-3 px-4 py-3 hover:bg-white/6 cursor-pointer transition-colors border-b border-white/4 last:border-0"
                  >
                    <div className="w-8 h-8 bg-gradient-to-br from-accent-700 to-brand-600 rounded-lg flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                      {stock.symbol.charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-white">{stock.symbol}</p>
                      <p className="text-xs text-white/40 truncate">{stock.name}</p>
                    </div>
                    {prices && (
                      <div className="text-right">
                        <p className="text-sm font-price font-semibold text-white">${prices.price?.toFixed(2)}</p>
                        <p className={clsx('text-xs font-price', prices.change_pct >= 0 ? 'text-gain' : 'text-loss')}>
                          {prices.change_pct >= 0 ? '+' : ''}{prices.change_pct?.toFixed(2)}%
                        </p>
                      </div>
                    )}
                  </div>
                )
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-3 ml-auto">
        {/* Portfolio Balance */}
        <div className="hidden lg:flex flex-col items-end">
          <p className="text-xs text-white/40 leading-none mb-0.5">Portfolio</p>
          <p className="text-sm font-price font-bold text-white">
            ${totalValue?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '—'}
          </p>
          {pnl !== undefined && (
            <p className={clsx('text-xs font-price', isPositive ? 'text-gain' : 'text-loss')}>
              {isPositive ? '+' : ''}${Math.abs(pnl).toFixed(2)} ({isPositive ? '+' : ''}{pnlPct?.toFixed(2)}%)
            </p>
          )}
        </div>

        {/* WS Status */}
        <div
          title={wsConnected ? 'Live data connected' : 'Disconnected'}
          className={clsx(
            'w-7 h-7 rounded-lg flex items-center justify-center transition-all',
            wsConnected
              ? 'bg-gain/15 text-gain'
              : 'bg-loss/15 text-loss'
          )}
        >
          {wsConnected ? <Wifi size={14} /> : <WifiOff size={14} />}
        </div>

        {/* Notifications */}
        <div ref={notifRef} className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative w-9 h-9 rounded-xl bg-white/5 border border-white/8 flex items-center justify-center hover:bg-white/10 hover:border-white/16 transition-all duration-200"
          >
            <Bell size={16} className="text-white/70" />
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-loss rounded-full text-white text-[9px] font-bold flex items-center justify-center">3</span>
          </button>

          <AnimatePresence>
            {showNotifications && (
              <motion.div
                initial={{ opacity: 0, y: -8, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.97 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 top-full mt-2 w-80 glass-dark rounded-xl overflow-hidden shadow-glass-lg border border-white/8 z-50"
              >
                <div className="px-4 py-3 border-b border-white/6 flex items-center justify-between">
                  <p className="text-sm font-semibold text-white">Notifications</p>
                  <button className="text-xs text-brand-400 hover:text-brand-300 transition-colors">Mark all read</button>
                </div>
                <NotificationItem title="AAPL Price Alert" message="AAPL reached $190 — your target price" time="2 min ago" type="alert" />
                <NotificationItem title="Order Filled" message="Bought 10 NVDA @ $875.60" time="15 min ago" type="trade" />
                <NotificationItem title="Stop-Loss Triggered" message="TSLA stop-loss at $183.00 was triggered" time="1 hr ago" type="alert" />
                <div className="px-4 py-3 border-t border-white/6">
                  <Link to="/notifications" onClick={() => setShowNotifications(false)} className="text-xs text-center block text-white/50 hover:text-white transition-colors">
                    View all notifications
                  </Link>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* User Menu */}
        <div ref={userRef} className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-white/5 border border-white/8 hover:bg-white/10 hover:border-white/16 transition-all duration-200"
          >
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-accent-600 to-brand-500 flex items-center justify-center text-xs font-bold text-white">
              {user?.username?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <span className="text-sm font-medium text-white/80 hidden sm:block max-w-[80px] truncate">
              {user?.username || 'User'}
            </span>
            <ChevronDown size={14} className="text-white/40 hidden sm:block" />
          </button>

          <AnimatePresence>
            {showUserMenu && (
              <motion.div
                initial={{ opacity: 0, y: -8, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.97 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 top-full mt-2 w-52 glass-dark rounded-xl overflow-hidden shadow-glass-lg border border-white/8 z-50 py-1"
              >
                <div className="px-4 py-3 border-b border-white/6">
                  <p className="text-sm font-semibold text-white">{user?.username || 'Demo User'}</p>
                  <p className="text-xs text-white/40 truncate">{user?.email || 'demo@tradeai.com'}</p>
                </div>
                {[
                  { label: 'Profile', icon: User, to: '/profile' },
                  { label: 'Settings', icon: Settings, to: '/settings' },
                ].map(({ label, icon: Icon, to }) => (
                  <Link
                    key={label}
                    to={to}
                    onClick={() => setShowUserMenu(false)}
                    className="flex items-center gap-3 px-4 py-2.5 text-sm text-white/70 hover:text-white hover:bg-white/6 transition-colors"
                  >
                    <Icon size={15} />
                    {label}
                  </Link>
                ))}
                <div className="border-t border-white/6 mt-1 pt-1">
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-loss hover:bg-loss/8 transition-colors"
                  >
                    <LogOut size={15} />
                    Sign Out
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  )
}
