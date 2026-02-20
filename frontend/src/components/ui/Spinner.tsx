import { clsx } from 'clsx'

interface SpinnerProps {
  className?: string
  size?: 'sm' | 'md'
}

export function Spinner({ className, size = 'md' }: SpinnerProps) {
  return (
    <div
      className={clsx(
        'rounded-full border-2 border-gray-200 border-t-blue-500 animate-spin',
        size === 'sm' ? 'w-4 h-4' : 'w-6 h-6',
        className,
      )}
    />
  )
}
