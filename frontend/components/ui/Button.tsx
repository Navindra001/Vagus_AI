import { forwardRef } from 'react'
import { clsx } from 'clsx'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
}

/**
 * WCAG compliance:
 * - Minimum 44×44px touch target (WCAG 2.5.5)
 * - Focus ring via :focus-visible in globals.css (WCAG 2.4.7)
 * - aria-disabled + aria-busy when loading (WCAG 4.1.2)
 * - Loading state announced to screen readers
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', isLoading, children, className, disabled, ...props }, ref) => {
    const base = 'inline-flex items-center justify-center font-medium rounded-lg transition-colors gap-2'

    const variants = {
      primary:   'bg-[--color-accent] text-[--color-bg-deep] hover:bg-[--color-accent-hover]',
      secondary: 'bg-[--color-bg-surface] text-[--color-text-primary] border border-[--color-border] hover:bg-[--color-bg-elevated]',
      ghost:     'text-[--color-text-secondary] hover:text-[--color-text-primary] hover:bg-[--color-bg-surface]',
      danger:    'bg-[--color-error] text-white hover:opacity-90',
    }

    const sizes = {
      sm: 'px-3 py-2 text-sm min-h-[44px]',
      md: 'px-4 py-2.5 text-base min-h-[44px]',
      lg: 'px-6 py-3 text-lg min-h-[44px]',
    }

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        aria-disabled={disabled || isLoading}
        aria-busy={isLoading}
        className={clsx(
          base,
          variants[variant],
          sizes[size],
          (disabled || isLoading) && 'opacity-50 cursor-not-allowed',
          className
        )}
        {...props}
      >
        {isLoading && <span className="sr-only">Loading...</span>}
        {children}
      </button>
    )
  }
)
Button.displayName = 'Button'
