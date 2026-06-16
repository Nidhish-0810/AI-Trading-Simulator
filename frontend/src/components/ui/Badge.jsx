import clsx from 'clsx'
import { TrendingUp, TrendingDown, Minus, Zap, ShoppingCart, DollarSign, AlertTriangle } from 'lucide-react'

const configs = {
  gain: {
    class: 'badge-gain',
    Icon: TrendingUp,
  },
  loss: {
    class: 'badge-loss',
    Icon: TrendingDown,
  },
  neutral: {
    class: 'badge-neutral',
    Icon: Minus,
  },
  buy: {
    class: 'badge-gain',
    Icon: ShoppingCart,
  },
  sell: {
    class: 'badge-loss',
    Icon: DollarSign,
  },
  accent: {
    class: 'badge-accent',
    Icon: Zap,
  },
  gold: {
    class: 'badge-gold',
    Icon: AlertTriangle,
  },
  strong_buy: {
    class: '',
    custom: 'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-brand-500/20 text-brand-400 border border-brand-500/30',
    Icon: TrendingUp,
  },
  strong_sell: {
    class: '',
    custom: 'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-loss/20 text-loss border border-loss/30',
    Icon: TrendingDown,
  },
}

const signalColors = {
  STRONG_BUY:  { bg: 'bg-brand-500/20', text: 'text-brand-400', border: 'border-brand-500/30', label: 'Strong Buy' },
  BUY:         { bg: 'bg-gain/15', text: 'text-gain', border: 'border-gain/25', label: 'Buy' },
  NEUTRAL:     { bg: 'bg-white/8', text: 'text-white/60', border: 'border-white/12', label: 'Neutral' },
  SELL:        { bg: 'bg-loss/15', text: 'text-loss', border: 'border-loss/25', label: 'Sell' },
  STRONG_SELL: { bg: 'bg-red-900/30', text: 'text-red-400', border: 'border-red-500/30', label: 'Strong Sell' },
}

export function Badge({ children, variant = 'neutral', icon = true, className, dot = false }) {
  const config = configs[variant] || configs.neutral
  const { Icon } = config

  return (
    <span className={clsx(config.custom || config.class, className)}>
      {dot && <span className="w-1.5 h-1.5 rounded-full bg-current" />}
      {!dot && icon && Icon && <Icon size={10} />}
      {children}
    </span>
  )
}

export function SignalBadge({ signal, size = 'sm' }) {
  const config = signalColors[signal] || signalColors.NEUTRAL
  const sizeClass = size === 'lg'
    ? 'px-4 py-1.5 text-sm font-bold rounded-full'
    : 'px-2.5 py-0.5 text-xs font-semibold rounded-full'

  return (
    <span className={clsx(
      'inline-flex items-center gap-1.5 border',
      sizeClass,
      config.bg, config.text, config.border
    )}>
      {signal === 'STRONG_BUY' || signal === 'BUY' ? <TrendingUp size={size === 'lg' ? 14 : 10} /> : signal === 'STRONG_SELL' || signal === 'SELL' ? <TrendingDown size={size === 'lg' ? 14 : 10} /> : <Minus size={size === 'lg' ? 14 : 10} />}
      {config.label}
    </span>
  )
}

export function PctBadge({ value, showIcon = true }) {
  const isGain = value >= 0
  return (
    <span className={clsx(
      'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold font-price',
      isGain ? 'badge-gain' : 'badge-loss'
    )}>
      {showIcon && (isGain ? <TrendingUp size={10} /> : <TrendingDown size={10} />)}
      {isGain ? '+' : ''}{value?.toFixed(2)}%
    </span>
  )
}

export function SectorBadge({ sector }) {
  const sectorColors = {
    Technology: 'bg-blue-500/15 text-blue-400 border-blue-500/25',
    'Communication': 'bg-purple-500/15 text-purple-400 border-purple-500/25',
    'Consumer Discretionary': 'bg-orange-500/15 text-orange-400 border-orange-500/25',
    Healthcare: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25',
    Financials: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/25',
    Energy: 'bg-red-500/15 text-red-400 border-red-500/25',
    Industrials: 'bg-gray-500/15 text-gray-400 border-gray-500/25',
    'Consumer Staples': 'bg-green-500/15 text-green-400 border-green-500/25',
    Utilities: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/25',
    Materials: 'bg-amber-500/15 text-amber-400 border-amber-500/25',
    'Real Estate': 'bg-pink-500/15 text-pink-400 border-pink-500/25',
  }
  return (
    <span className={clsx(
      'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border',
      sectorColors[sector] || 'bg-white/8 text-white/60 border-white/12'
    )}>
      {sector}
    </span>
  )
}

export default Badge
