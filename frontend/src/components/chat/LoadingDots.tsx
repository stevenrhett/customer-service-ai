"use client"

interface LoadingDotsProps {
  className?: string
}

/**
 * Loading dots animation component
 */
export function LoadingDots({ className = '' }: LoadingDotsProps) {
  return (
    <div className={`flex items-center gap-1 ${className}`} aria-label="Loading">
      <span className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:-0.3s]" />
      <span className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:-0.15s]" />
      <span className="w-2 h-2 bg-current rounded-full animate-bounce" />
    </div>
  )
}

