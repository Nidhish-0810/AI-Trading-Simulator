import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'

const SECTOR_COLORS = [
  '#7c3aed', '#00d4aa', '#f59e0b', '#ff4757', '#3b82f6',
  '#ec4899', '#10b981', '#f97316', '#8b5cf6', '#06b6d4',
]

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const d = payload[0]
  return (
    <div className="glass-dark px-4 py-3 rounded-xl border border-white/10 text-sm">
      <p className="text-white font-semibold">{d.name}</p>
      <p className="text-white/60 mt-0.5">
        ${d.payload.value?.toLocaleString('en-US', { maximumFractionDigits: 0 })}
      </p>
      <p className="font-price text-sm mt-0.5" style={{ color: d.payload.fill }}>
        {(d.payload.percent * 100).toFixed(1)}%
      </p>
    </div>
  )
}

function CustomLegend({ payload }) {
  return (
    <div className="flex flex-wrap gap-2 mt-3 justify-center">
      {payload?.map((entry, i) => (
        <div key={i} className="flex items-center gap-1.5 text-xs text-white/60">
          <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: entry.color }} />
          <span>{entry.value}</span>
        </div>
      ))}
    </div>
  )
}

export default function SectorAllocationChart({ data = [], height = 200 }) {
  const chartData = data.length > 0 ? data : [
    { name: 'Technology', value: 45200 },
    { name: 'Consumer Disc.', value: 12800 },
    { name: 'Communication', value: 9400 },
    { name: 'Financials', value: 7200 },
    { name: 'Healthcare', value: 5100 },
    { name: 'Other', value: 3800 },
  ]

  const total = chartData.reduce((s, d) => s + d.value, 0)
  const withPct = chartData.map((d) => ({ ...d, percent: d.value / total }))

  return (
    <ResponsiveContainer width="100%" height={height + 60}>
      <PieChart>
        <Pie
          data={withPct}
          cx="50%"
          cy="45%"
          innerRadius={height * 0.28}
          outerRadius={height * 0.45}
          paddingAngle={3}
          dataKey="value"
          strokeWidth={0}
        >
          {withPct.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={SECTOR_COLORS[index % SECTOR_COLORS.length]}
              opacity={0.85}
            />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend content={<CustomLegend />} />
      </PieChart>
    </ResponsiveContainer>
  )
}
