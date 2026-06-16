import { forwardRef } from 'react'
import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'
import clsx from 'clsx'

const variants = {
  primary: 'bg-gradient-to-r from-accent-600 to-brand-500 text-white shadow-accent hover:brightness-110 hover:shadow-lg',
  secondary: 'glass-card text-white/90 hover:bg-white/8 hover:border-white/20',
  danger: 'bg-gradient-to-r from-red-600 to-loss text-white hover:brightness-110',
  ghost: 'text-white/70 hover:text-white hover:bg-white/6',
  outline: 'border border-white/20 text-white/80 hover:border-white/40 hover:text-white hover:bg-white/5',
  gain: 'bg-gradient-to-r from-brand-600 to-brand-500 text-dark-900 font-bold hover:brightness-110 shadow-gain',
  loss: 'bg-gradient-to-r from-red-600 to-loss text-white font-bold hover:brightness-110 shadow-loss',
  gold: 'bg-gradient-to-r from-gold-dark to-gold text-dark-900 font-bold hover:brightness-110',
}

const sizes = {
  xs: 'text-xs px-3 py-1.5 rounded-lg gap-1',
  sm: 'text-sm px-4 py-2 rounded-xl gap-1.5',
  md: 'text-sm px-5 py-2.5 rounded-xl gap-2',
  lg: 'text-base px-6 py-3 rounded-xl gap-2',
  xl: 'text-base px-8 py-4 rounded-2xl gap-2.5 font-semibold',
}

const Button = forwardRef(({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon: Icon,
  iconRight: IconRight,
  className,
  onClick,
  type = 'button',
  fullWidth = false,
  animate = true,
  ...props
}, ref) => {
  const isDisabled = disabled || loading

  const content = (
    <button
      ref={ref}
      type={type}
      disabled={isDisabled}
      onClick={onClick}
      className={clsx(
        'inline-flex items-center justify-center font-semibold transition-all duration-200 cursor-pointer select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/50',
        variants[variant],
        sizes[size],
        fullWidth && 'w-full',
        isDisabled && 'opacity-50 cursor-not-allowed pointer-events-none',
        className
      )}
      {...props}
    >
      {loading ? (
        <Loader2 className="animate-spin" size={size === 'xs' ? 12 : size === 'sm' ? 14 : 16} />
      ) : Icon ? (
        <Icon size={size === 'xs' ? 12 : size === 'sm' ? 14 : size === 'lg' || size === 'xl' ? 20 : 16} />
      ) : null}
      {children}
      {!loading && IconRight && (
        <IconRight size={size === 'xs' ? 12 : size === 'sm' ? 14 : size === 'lg' || size === 'xl' ? 20 : 16} />
      )}
    </button>
  )

  if (animate && !isDisabled) {
    return (
      <motion.div
        whileHover={{ scale: 1.02, y: -1 }}
        whileTap={{ scale: 0.97, y: 0 }}
        style={{ display: fullWidth ? 'block' : 'inline-block' }}
      >
        {content}
      </motion.div>
    )
  }

  return content
})

Button.displayName = 'Button'
export default Button
