"use client"

import { useEffect, useRef } from 'react'

interface StreamingTextProps {
  text: string
  className?: string
}

/**
 * Component for rendering streaming text with accessibility support
 */
export function StreamingText({ text, className = '' }: StreamingTextProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom as text streams
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [text])

  return (
    <div
      ref={containerRef}
      className={className}
      aria-live="polite"
      aria-atomic="false"
    >
      {text || '\u00A0'} {/* Non-breaking space to maintain height */}
    </div>
  )
}

