import { forwardRef, useState } from 'react'
import clsx from 'clsx'
import { Eye, EyeOff, AlertCircle } from 'lucide-react'

const Input = forwardRef(({
  label,
  error,
  hint,
  icon: Icon,
  iconRight,
  type = 'text',
  className,
  inputClassName,
  placeholder,
  disabled,
  required,
  value,
  onChange,
  onBlur,
  onFocus,
  ...props
}, ref) => {
  const [focused, setFocused] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const isPassword = type === 'password'
  const inputType = isPassword ? (showPassword ? 'text' : 'password') : type
  const hasValue = value !== undefined && value !== ''

  return (
    <div className={clsx('w-full', className)}>
      {label && (
        <label className="block text-sm font-medium text-white/70 mb-2">
          {label}
          {required && <span className="text-loss ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <div className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none">
            <Icon size={16} className={clsx(
              'transition-colors duration-200',
              focused ? 'text-brand-400' : 'text-white/30'
            )} />
          </div>
        )}

        <input
          ref={ref}
          type={inputType}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          onFocus={(e) => { setFocused(true); onFocus?.(e) }}
          onBlur={(e) => { setFocused(false); onBlur?.(e) }}
          className={clsx(
            'w-full bg-white/5 border rounded-xl text-white placeholder-white/25 transition-all duration-200',
            'py-3 text-sm',
            Icon ? 'pl-10 pr-4' : 'px-4',
            (isPassword || iconRight) && 'pr-11',
            focused
              ? 'border-brand-500/60 bg-white/8 ring-2 ring-brand-500/15'
              : error
                ? 'border-loss/50 bg-white/5'
                : 'border-white/10 hover:border-white/20',
            disabled && 'opacity-50 cursor-not-allowed',
            inputClassName
          )}
          {...props}
        />

        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/70 transition-colors"
          >
            {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}

        {!isPassword && iconRight && (
          <div className="absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none text-white/30">
            {iconRight}
          </div>
        )}

        {error && !isPassword && !iconRight && (
          <div className="absolute right-3.5 top-1/2 -translate-y-1/2 text-loss">
            <AlertCircle size={16} />
          </div>
        )}
      </div>

      {error && (
        <p className="mt-1.5 text-xs text-loss flex items-center gap-1">
          <AlertCircle size={12} />
          {error}
        </p>
      )}
      {!error && hint && (
        <p className="mt-1.5 text-xs text-white/40">{hint}</p>
      )}
    </div>
  )
})

Input.displayName = 'Input'
export default Input
