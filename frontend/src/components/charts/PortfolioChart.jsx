import { useState, useMemo } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine
} from 'recharts'
import { format, parseISO } from 'date-fns'
import { motion } from 'framer-motion'
import clsx from 'clsx'

const RANGES = [
  { label: '1D', days: 1 },
  { label: '1W', days: 7 },
  { label: '1M', days: 30 },
  { label: '3M', days: 90 },
  { label: '1Y', days: 365 },
]

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const val = payload[0]?.value
  const prev = payload[0]?.payload?.prevValue
  const change = prev ? val - prev : 0
  const changePct = prev ? ((val - prev) / prev) * 100 : 0
  const isPos = change >= 0

  return (
    <div className="glass-dark px-4 py-3 rounded-xl border border-white/10 shadow-glass min-w-[160px]">
      <p className="text-xs text-white/40 mb-1.5">{label}</p>
      <p className="text-base font-price font-bold text-white">
        ${val?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </p>
      <p className={clsx('text-xs font-price mt-0.5', isPos ? 'text-gain' : 'text-loss')}>
        {isPos ? '+' : ''}${Math.abs(change).toFixed(2)} ({isPos ? '+' : ''}{changePct.toFixed(2)}%)
      </p>
    </div>
  )
}

export default function PortfolioChart({ history = [], height = 260 }) {
  const [range, setRange] = useState('3M')

  const filteredData = useMemo(() => {
    if (!history.length) return []
    const days = RANGES.find((r) => r.label === range)?.days || 90
    const sliced = history.slice(-days)
    return sliced.map((point, i) => ({
      ...point,
      date: typeof point.date === 'string'
        ? format(parseISO(point.date), days <= 1 ? 'HH:mm' : days <= 7 ? 'EEE' : 'MMM d')
        : format(new Date(point.date), 'MMM d'),
      prevValue: i > 0 ? sliced[i - 1].value : point.value,
    }))
  }, [history, range])

  const firstVal = filteredData[0]?.value || 0
  const lastVal = filteredData[filteredData.length - 1]?.value || 0
  const isPositive = lastVal >= firstVal
  const color = isPositive ? '#00d4aa' : '#ff4757'

  const gradientId = isPositive ? 'portfolioGainGrad' : 'portfolioLossGrad'

  if (!history.length) {
    return (
      <div className="flex items-center justify-center h-40 text-white/30 text-sm">
        No portfolio history yet. Start trading!
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Range Selector */}
      <div className="flex items-center gap-1 mb-4">
        {RANGES.map(({ label }) => (
          <button
            key={label}
            onClick={() => setRange(label)}
            className={clsx(
              'px-3 py-1 text-xs font-semibold rounded-lg transition-all duration-150',
              range === label
                ? 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                : 'text-white/40 hover:text-white/70 hover:bg-white/5'
            )}
          >
            {label}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={filteredData} margin={{ top: 5, right: 0, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="portfolioGainGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00d4aa" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#00d4aa" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="portfolioLossGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ff4757" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#ff4757" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11, fontFamily: 'Inter' }}
            axisLine={false}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11, fontFamily: 'JetBrains Mono' }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
            width={52}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: color, strokeWidth: 1, strokeDasharray: '4 4' }} />
          <ReferenceLine y={firstVal} stroke="rgba(255,255,255,0.1)" strokeDasharray="4 4" />
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            fill={`url(#${gradientId})`}
            dot={false}
            activeDot={{ r: 4, fill: color, stroke: '#0a0a0f', strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </motion.div>
  )
}
