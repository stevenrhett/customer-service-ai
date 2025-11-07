/**
 * Generic SSE hook with auto-reconnect and error handling
 * Note: This is a lower-level hook. For chat, use useChat which wraps this.
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import { SSE_CONFIG } from '@/lib/constants'
import { logger } from '@/lib/logger'

export interface UseEventSourceOptions {
  onMessage?: (event: MessageEvent) => void
  onError?: (error: Event) => void
  onOpen?: (event: Event) => void
  enabled?: boolean
  reconnect?: boolean
  maxReconnectAttempts?: number
}

export interface UseEventSourceReturn {
  isConnected: boolean
  error: Error | null
  reconnect: () => void
  disconnect: () => void
}

/**
 * Generic EventSource hook with auto-reconnect
 * Note: EventSource only supports GET requests, so for POST SSE we use fetch + ReadableStream
 * This hook is kept for reference but chat uses apiClient.sendChatSSE instead
 */
export function useEventSource(
  url: string | null,
  options: UseEventSourceOptions = {}
): UseEventSourceReturn {
  const {
    onMessage,
    onError,
    onOpen,
    enabled = true,
    reconnect: shouldReconnect = true,
    maxReconnectAttempts = SSE_CONFIG.MAX_RECONNECT_ATTEMPTS,
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    setIsConnected(false)
    reconnectAttemptsRef.current = 0
  }, [])

  const connect = useCallback(() => {
    if (!url || !enabled) {
      return
    }

    disconnect()

    try {
      const eventSource = new EventSource(url)
      eventSourceRef.current = eventSource

      eventSource.onopen = (event) => {
        setIsConnected(true)
        setError(null)
        reconnectAttemptsRef.current = 0
        onOpen?.(event)
        logger.debug('EventSource connected', url)
      }

      eventSource.onmessage = (event) => {
        onMessage?.(event)
      }

      eventSource.onerror = (event) => {
        setIsConnected(false)
        const error = new Error('EventSource error')
        setError(error)
        onError?.(event)

        // Auto-reconnect logic
        if (shouldReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          const delay = SSE_CONFIG.RECONNECT_DELAY_MS * reconnectAttemptsRef.current
          
          logger.warn(
            `EventSource error, reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`
          )

          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, delay)
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          logger.error('EventSource max reconnect attempts reached')
          disconnect()
        }
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      setError(error)
      logger.error('Failed to create EventSource', error)
    }
  }, [url, enabled, shouldReconnect, maxReconnectAttempts, onMessage, onError, onOpen, disconnect])

  const reconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0
    connect()
  }, [connect])

  useEffect(() => {
    if (enabled && url) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [enabled, url, connect, disconnect])

  return {
    isConnected,
    error,
    reconnect,
    disconnect,
  }
}

