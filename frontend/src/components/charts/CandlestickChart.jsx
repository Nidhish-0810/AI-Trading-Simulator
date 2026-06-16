import { useState, useMemo } from 'react'
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, ReferenceLine
} from 'recharts'
import { format } from 'date-fns'
import clsx from 'clsx'

// Generate mock OHLCV data
function generateCandleData(basePrice, count, interval) {
  const data = []
  let price = basePrice
  const now = Date.now()
  const intervalMs = {
    '1m': 60_000, '5m': 300_000, '15m': 900_000,
    '1h': 3_600_000, '1D': 86_400_000, '1W': 604_800_000,
  }[interval] || 86_400_000

  for (let i = count; i >= 0; i--) {
    const open = price
    const change = (Math.random() - 0.49) * price * 0.025
    const close = Math.max(0.01, open + change)
    const high = Math.max(open, close) * (1 + Math.random() * 0.01)
    const low = Math.min(open, close) * (1 - Math.random() * 0.01)
    const volume = Math.round(500_000 + Math.random() * 5_000_000)
    const ts = now - i * intervalMs
    data.push({
      date: new Date(ts).toISOString(),
      open: parseFloat(open.toFixed(2)),
      close: parseFloat(close.toFixed(2)),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      volume,
      isUp: close >= open,
    })
    price = close
  }
  return data
}

// Custom Candlestick shape
function CandlestickShape(props) {
  const { x, y, width, height, open, close, high, low, isUp } = props
  if (!x || !y || !width) return null

  const color = isUp ? '#00d4aa' : '#ff4757'
  const bodyTop = Math.min(y, y + height)
  const bodyBottom = Math.max(y, y + height)
  const bodyHeight = Math.max(1, Math.abs(height))
  const centerX = x + width / 2

  return (
    <g>
      {/* Wick top */}
      <line x1={centerX} y1={props.top} x2={centerX} y2={bodyTop} stroke={color} strokeWidth={1.5} />
      {/* Wick bottom */}
      <line x1={centerX} y1={bodyBottom} x2={centerX} y2={props.bottom} stroke={color} strokeWidth={1.5} />
      {/* Body */}
      <rect
        x={x + 1}
        y={bodyTop}
        width={Math.max(2, width - 2)}
        height={bodyHeight}
        fill={isUp ? 'rgba(0,212,170,0.85)' : 'rgba(255,71,87,0.85)'}
        stroke={color}
        strokeWidth={0.5}
        rx={1}
      />
    </g>
  )
}

function CustomCandlestick(props) {
  const { x, y, width, height, payload, yScale } = props
  if (!payload || !yScale) return null
  const { open, close, high, low, isUp } = payload
  const top = yScale(high)
  const bottom = yScale(low)
  const openY = yScale(open)
  const closeY = yScale(close)
  const bodyY = Math.min(openY, closeY)
  const bodyH = Math.abs(openY - closeY)

  return (
    <CandlestickShape
      x={x}
      y={bodyY}
      width={width}
      height={bodyH}
      top={top}
      bottom={bottom}
      open={open}
      close={close}
      isUp={isUp}
    />
  )
}

function OHLCTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload
  if (!d) return null

  return (
    <div className="glass-dark p-3 rounded-xl border border-white/10 shadow-glass text-xs font-price">
      <p className="text-white/50 mb-2 font-sans">{label}</p>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1">
        {[
          ['Open', d.open, 'text-white/80'],
          ['Close', d.close, d.isUp ? 'text-gain' : 'text-loss'],
          ['High', d.high, 'text-gain'],
          ['Low', d.low, 'text-loss'],
        ].map(([label, val, cls]) => (
          <div key={label} className="flex justify-between gap-2">
            <span className="text-white/40">{label}</span>
            <span className={cls}>${val?.toFixed(2)}</span>
          </div>
        ))}
      </div>
      <div className="border-t border-white/8 mt-2 pt-2 flex justify-between">
        <span className="text-white/40">Vol</span>
        <span className="text-white/70">{(d.volume / 1_000_000).toFixed(1)}M</span>
      </div>
    </div>
  )
}

const INTERVALS = ['1m', '5m', '15m', '1h', '1D', '1W']
const INTERVAL_COUNT = { '1m': 60, '5m': 78, '15m': 96, '1h': 72, '1D': 90, '1W': 52 }

export default function CandlestickChart({ symbol, basePrice = 185, height = 360 }) {
  const [interval, setInterval_] = useState('1D')

  const data = useMemo(
    () => generateCandleData(basePrice, INTERVAL_COUNT[interval] || 90, interval),
    [basePrice, interval]
  )

  const sma20 = useMemo(() => {
    return data.map((_, i) => {
      if (i < 19) return { ...data[i], sma20: null }
      const slice = data.slice(i - 19, i + 1)
      const avg = slice.reduce((s, d) => s + d.close, 0) / 20
      return { ...data[i], sma20: parseFloat(avg.toFixed(2)) }
    })
  }, [data])

  const formatDate = (val) => {
    try {
      const d = new Date(val)
      if (interval === '1m' || interval === '5m' || interval === '15m') return format(d, 'HH:mm')
      if (interval === '1h') return format(d, 'MMM d HH:mm')
      if (interval === '1W') return format(d, 'MMM yyyy')
      return format(d, 'MMM d')
    } catch { return val }
  }

  const prices = sma20.map((d) => [d.high, d.low]).flat().filter(Boolean)
  const [yMin, yMax] = prices.length ? [Math.min(...prices) * 0.997, Math.max(...prices) * 1.003] : [0, 100]

  return (
    <div>
      {/* Interval Selector */}
      <div className="flex items-center gap-1 mb-4">
        {INTERVALS.map((iv) => (
          <button
            key={iv}
            onClick={() => setInterval_(iv)}
            className={clsx(
              'px-3 py-1 text-xs font-semibold rounded-lg transition-all duration-150',
              interval === iv
                ? 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                : 'text-white/40 hover:text-white/70 hover:bg-white/5'
            )}
          >
            {iv}
          </button>
        ))}
      </div>

      {/* Main Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={sma20} margin={{ top: 5, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10, fontFamily: 'Inter' }}
            axisLine={false}
            tickLine={false}
            interval={Math.floor(sma20.length / 6)}
          />
          <YAxis
            domain={[yMin, yMax]}
            tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => `$${v.toFixed(0)}`}
            width={56}
            orientation="right"
          />
          <Tooltip content={<OHLCTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeDasharray: '4 4' }} />

          {/* Candlesticks as Bars with custom shape */}
          <Bar
            dataKey="close"
            shape={(props) => {
              const { x, y, width, height, payload } = props
              if (!payload) return null
              const yScale = (val) => {
                const range = yMax - yMin
                const chartHeight = height
                return y + chartHeight - ((val - yMin) / range) * chartHeight
              }
              const openY = yScale(payload.open)
              const closeY = yScale(payload.close)
              const highY = yScale(payload.high)
              const lowY = yScale(payload.low)
              const color = payload.isUp ? '#00d4aa' : '#ff4757'
              const bodyTop = Math.min(openY, closeY)
              const bodyH = Math.max(1, Math.abs(openY - closeY))
              const cx = x + width / 2
              return (
                <g key={`candle-${x}`}>
                  <line x1={cx} y1={highY} x2={cx} y2={bodyTop} stroke={color} strokeWidth={1.5} />
                  <line x1={cx} y1={bodyTop + bodyH} x2={cx} y2={lowY} stroke={color} strokeWidth={1.5} />
                  <rect x={x + 1} y={bodyTop} width={Math.max(1, width - 2)} height={bodyH} fill={payload.isUp ? 'rgba(0,212,170,0.8)' : 'rgba(255,71,87,0.8)'} stroke={color} strokeWidth={0.5} rx={1} />
                </g>
              )
            }}
          >
            {sma20.map((entry, i) => (
              <Cell key={i} fill={entry.isUp ? '#00d4aa' : '#ff4757'} />
            ))}
          </Bar>

          {/* SMA 20 line */}
          <Line
            type="monotone"
            dataKey="sma20"
            stroke="#7c3aed"
            strokeWidth={1.5}
            dot={false}
            strokeDasharray="4 2"
            connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Volume Chart */}
      <div className="mt-1">
        <ResponsiveContainer width="100%" height={60}>
          <ComposedChart data={sma20} margin={{ top: 0, right: 8, left: 0, bottom: 0 }}>
            <YAxis hide domain={['auto', 'auto']} />
            <Bar dataKey="volume" radius={[1, 1, 0, 0]}>
              {sma20.map((entry, i) => (
                <Cell key={i} fill={entry.isUp ? 'rgba(0,212,170,0.3)' : 'rgba(255,71,87,0.3)'} />
              ))}
            </Bar>
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-2 text-xs text-white/40">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-0.5 bg-accent-400" style={{ border: '1px dashed #7c3aed' }} />
          <span>SMA 20</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-gain/70" />
          <span>Bullish</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-loss/70" />
          <span>Bearish</span>
        </div>
      </div>
    </div>
  )
}
