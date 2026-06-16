import { forwardRef } from 'react'
import { motion } from 'framer-motion'
import clsx from 'clsx'

const Card = forwardRef(({
  children,
  className,
  variant = 'default',
  padding = 'md',
  hover = false,
  glow = false,
  glowColor = 'brand',
  animate = false,
  onClick,
  ...props
}, ref) => {
  const paddings = {
    none: '',
    sm: 'p-4',
    md: 'p-5',
    lg: 'p-6',
    xl: 'p-8',
  }

  const variantStyles = {
    default: 'glass-card',
    dark: 'glass-dark',
    brand: 'glass-card-brand',
    accent: 'glass-card-accent',
    solid: 'bg-dark-800 border border-white/8',
    transparent: 'bg-transparent border border-white/6',
  }

  const glowStyles = {
    brand: 'shadow-brand',
    accent: 'shadow-accent',
    gain: 'shadow-gain',
    loss: 'shadow-loss',
    gold: 'shadow-gold',
  }

  const Wrapper = animate ? motion.div : 'div'
  const motionProps = animate ? {
    initial: { opacity: 0, y: 16 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] },
  } : {}

  return (
    <Wrapper
      ref={ref}
      onClick={onClick}
      className={clsx(
        variantStyles[variant],
        paddings[padding],
        hover && 'glass-hover cursor-pointer',
        glow && glowStyles[glowColor],
        onClick && 'cursor-pointer',
        className
      )}
      {...motionProps}
      {...props}
    >
      {children}
    </Wrapper>
  )
})

Card.displayName = 'Card'

// Card sub-components
Card.Header = function CardHeader({ children, className, divider = true }) {
  return (
    <div className={clsx('flex items-center justify-between', divider && 'pb-4 mb-4 border-b border-white/6', className)}>
      {children}
    </div>
  )
}

Card.Title = function CardTitle({ children, className }) {
  return (
    <h3 className={clsx('text-base font-semibold text-white flex items-center gap-2', className)}>
      {children}
    </h3>
  )
}

Card.Body = function CardBody({ children, className }) {
  return <div className={clsx('flex-1', className)}>{children}</div>
}

Card.Footer = function CardFooter({ children, className }) {
  return (
    <div className={clsx('pt-4 mt-4 border-t border-white/6', className)}>
      {children}
    </div>
  )
}

export default Card
