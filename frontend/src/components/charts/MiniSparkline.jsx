import { useMemo } from 'react'
import { LineChart, Line, ResponsiveContainer } from 'recharts'

export default function MiniSparkline({ prices, width = '100%', height = 40, positive }) {
  const data = useMemo(() => {
    if (!prices || prices.length === 0) {
      // Generate fake sparkline
      let v = 100 + Math.random() * 50
      return Array.from({ length: 14 }, (_, i) => {
        v = v + (Math.random() - 0.49) * 3
        return { v: parseFloat(v.toFixed(2)) }
      })
    }
    return prices.map((p) => ({ v: typeof p === 'object' ? p.close || p.value || p : p }))
  }, [prices])

  const first = data[0]?.v || 0
  const last = data[data.length - 1]?.v || 0
  const isUp = positive !== undefined ? positive : last >= first
  const color = isUp ? '#00d4aa' : '#ff4757'

  return (
    <ResponsiveContainer width={width} height={height}>
      <LineChart data={data}>
        <Line
          type="monotone"
          dataKey="v"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
