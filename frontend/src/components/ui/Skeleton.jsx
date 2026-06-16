import clsx from 'clsx'

function SkeletonBase({ className }) {
  return <div className={clsx('skeleton', className)} />
}

export function SkeletonText({ lines = 1, className }) {
  return (
    <div className={clsx('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonBase
          key={i}
          className={clsx('h-4 rounded', i === lines - 1 && lines > 1 ? 'w-3/4' : 'w-full')}
        />
      ))}
    </div>
  )
}

export function SkeletonCard({ className }) {
  return (
    <div className={clsx('glass-card p-5 space-y-4', className)}>
      <div className="flex items-center gap-3">
        <SkeletonBase className="w-10 h-10 rounded-xl flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <SkeletonBase className="h-4 w-1/3" />
          <SkeletonBase className="h-3 w-1/2" />
        </div>
        <SkeletonBase className="h-6 w-16 rounded-full" />
      </div>
      <SkeletonBase className="h-12 w-full rounded-lg" />
      <div className="flex gap-4">
        <SkeletonBase className="h-4 w-1/4" />
        <SkeletonBase className="h-4 w-1/4" />
        <SkeletonBase className="h-4 w-1/4" />
      </div>
    </div>
  )
}

export function SkeletonStatCard({ className }) {
  return (
    <div className={clsx('glass-card p-5 space-y-3', className)}>
      <SkeletonBase className="h-4 w-1/3" />
      <SkeletonBase className="h-8 w-2/3" />
      <SkeletonBase className="h-3 w-1/2" />
    </div>
  )
}

export function SkeletonTable({ rows = 5, cols = 5 }) {
  return (
    <div className="space-y-0">
      {/* Header */}
      <div className="flex gap-4 px-4 py-3 border-b border-white/6">
        {Array.from({ length: cols }).map((_, i) => (
          <SkeletonBase key={i} className="h-3 flex-1 rounded" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 px-4 py-3.5 border-b border-white/4">
          {Array.from({ length: cols }).map((_, j) => (
            <SkeletonBase key={j} className={clsx('h-4 rounded', j === 0 ? 'w-20' : 'flex-1')} />
          ))}
        </div>
      ))}
    </div>
  )
}

export function SkeletonChart({ className }) {
  return (
    <div className={clsx('relative overflow-hidden rounded-xl', className)}>
      <SkeletonBase className="w-full h-full absolute inset-0" />
      <div className="absolute inset-0 flex items-end justify-around px-4 pb-4 gap-1">
        {Array.from({ length: 20 }).map((_, i) => (
          <div
            key={i}
            className="flex-1 bg-white/5 rounded-t"
            style={{ height: `${20 + Math.random() * 60}%` }}
          />
        ))}
      </div>
    </div>
  )
}

export function SkeletonAvatar({ size = 40, className }) {
  return <SkeletonBase className={clsx('rounded-full flex-shrink-0', className)} style={{ width: size, height: size }} />
}

export function SkeletonRow({ className }) {
  return (
    <div className={clsx('flex items-center gap-4 py-3 px-4 border-b border-white/4', className)}>
      <SkeletonBase className="w-8 h-8 rounded-lg" />
      <div className="flex-1 space-y-1.5">
        <SkeletonBase className="h-4 w-1/4" />
        <SkeletonBase className="h-3 w-1/3" />
      </div>
      <SkeletonBase className="h-5 w-16 rounded" />
      <SkeletonBase className="h-5 w-20 rounded" />
    </div>
  )
}

export default SkeletonBase
export { SkeletonBase as Skeleton }
