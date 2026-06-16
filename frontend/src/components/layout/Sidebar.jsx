import { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard, BarChart2, TrendingUp, PieChart,
  Activity, FlaskConical, Trophy, Bell, ChevronLeft,
  ChevronRight, DollarSign
} from 'lucide-react'
import { usePortfolioStore } from '../../store/portfolioStore'
import clsx from 'clsx'

const navItems = [
  { to: '/dashboard',    icon: LayoutDashboard, label: 'Dashboard',     badge: null },
  { to: '/markets',      icon: BarChart2,        label: 'Markets',       badge: 'LIVE' },
  { to: '/portfolio',    icon: PieChart,         label: 'Portfolio',     badge: null },
  { to: '/analytics',    icon: Activity,         label: 'Analytics',     badge: null },
  { to: '/backtest',     icon: FlaskConical,     label: 'Backtesting',   badge: null },
  { to: '/leaderboard',  icon: Trophy,           label: 'Leaderboard',   badge: null },
  { to: '/notifications',icon: Bell,             label: 'Alerts',        badge: '3' },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const { totalValue, pnl, pnlPct } = usePortfolioStore()
  const isPositive = (pnl ?? 0) >= 0

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 240 }}
      transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
      className="hidden md:flex flex-col h-screen bg-dark-900/80 border-r border-white/6 relative flex-shrink-0 overflow-hidden"
    >
      {/* Collapse Toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3.5 top-20 z-10 w-7 h-7 bg-dark-800 border border-white/10 rounded-full flex items-center justify-center text-white/40 hover:text-white hover:border-white/20 transition-all shadow-lg"
      >
        {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>

      {/* Logo area */}
      <div className={clsx('flex items-center gap-3 p-4 mb-2', collapsed && 'justify-center')}>
        <div className="w-9 h-9 bg-gradient-to-br from-accent-600 to-brand-500 rounded-xl flex items-center justify-center flex-shrink-0 shadow-accent-sm">
          <TrendingUp size={18} className="text-white" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              transition={{ duration: 0.2 }}
              className="text-lg font-bold gradient-text whitespace-nowrap overflow-hidden"
            >
              TradeAI
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 px-3 space-y-0.5">
        {navItems.map(({ to, icon: Icon, label, badge }) => (
          <NavLink key={to} to={to}>
            {({ isActive }) => (
              <div
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 relative group',
                  collapsed ? 'justify-center' : '',
                  isActive
                    ? 'bg-gradient-to-r from-accent-600/20 to-brand-500/10 border border-white/8 text-white'
                    : 'text-white/50 hover:text-white hover:bg-white/5'
                )}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeNav"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-4 bg-brand-500 rounded-r"
                  />
                )}
                <Icon
                  size={18}
                  className={clsx(
                    'flex-shrink-0 transition-colors',
                    isActive ? 'text-brand-400' : 'text-current'
                  )}
                />
                <AnimatePresence>
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: 'auto' }}
                      exit={{ opacity: 0, width: 0 }}
                      transition={{ duration: 0.2 }}
                      className="text-sm font-medium whitespace-nowrap overflow-hidden flex-1"
                    >
                      {label}
                    </motion.span>
                  )}
                </AnimatePresence>
                {!collapsed && badge && (
                  <span className={clsx(
                    'text-[10px] font-bold px-1.5 py-0.5 rounded-full leading-none',
                    badge === 'LIVE'
                      ? 'bg-gain/20 text-gain border border-gain/25'
                      : 'bg-loss/20 text-loss border border-loss/25'
                  )}>
                    {badge}
                  </span>
                )}

                {/* Collapsed tooltip */}
                {collapsed && (
                  <div className="absolute left-full ml-2 px-2.5 py-1.5 glass-dark rounded-lg text-xs font-medium text-white border border-white/8 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-glass">
                    {label}
                  </div>
                )}
              </div>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom User Card */}
      <div className={clsx('p-3 border-t border-white/6', collapsed && 'px-2')}>
        {collapsed ? (
          <div className="w-10 h-10 mx-auto bg-gradient-to-br from-accent-600 to-brand-500 rounded-xl flex items-center justify-center text-sm font-bold text-white">
            T
          </div>
        ) : (
          <div className="glass-card p-3 rounded-xl">
            <div className="flex items-center gap-2.5 mb-2.5">
              <div className="w-8 h-8 bg-gradient-to-br from-accent-600 to-brand-500 rounded-lg flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                T
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-white truncate">TraderPro</p>
                <div className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-gain animate-pulse" />
                  <span className="text-[10px] text-gain">Active</span>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] text-white/40">Portfolio</p>
                <p className="text-xs font-price font-bold text-white">
                  ${(totalValue || 0).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                </p>
              </div>
              <span className={clsx(
                'text-[10px] font-price font-semibold px-1.5 py-0.5 rounded-full',
                isPositive ? 'bg-gain/15 text-gain' : 'bg-loss/15 text-loss'
              )}>
                {isPositive ? '+' : ''}{pnlPct?.toFixed(1) || '0.0'}%
              </span>
            </div>
          </div>
        )}
      </div>
    </motion.aside>
  )
}
