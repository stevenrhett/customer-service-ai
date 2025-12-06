/**
 * Chat hook that manages local state and handles streaming/non-streaming messages
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { sendChatSSE, sendChat, APIError, NetworkError } from '@/lib/apiClient'
import { logger } from '@/lib/logger'
import type { Message, ChatRequest, StreamEvent, ChatHistoryItem } from '@/lib/types'

export interface UseChatReturn {
  messages: Message[]
  isStreaming: boolean
  error: string | null
  sessionId: string | undefined
  sendMessage: (text: string) => Promise<void>
  clearMessages: () => void
  clearError: () => void
}

/**
 * Generate a unique message ID
 */
const generateMessageId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Chat hook with streaming support and fallback
 */
export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: generateMessageId(),
      role: 'assistant',
      content: "Hello! I'm your AI customer service assistant. I can help you with billing questions, technical support, and policy information. How can I assist you today?",
      createdAt: new Date().toISOString(),
    },
  ])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | undefined>()
  
  const abortControllerRef = useRef<AbortController | null>(null)
  const streamingMessageIdRef = useRef<string | null>(null)

  // Cleanup on unmount/route change
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([
      {
        id: generateMessageId(),
        role: 'assistant',
        content: "Hello! I'm your AI customer service assistant. I can help you with billing questions, technical support, and policy information. How can I assist you today?",
        createdAt: new Date().toISOString(),
      },
    ])
    setSessionId(undefined)
  }, [])

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isStreaming) {
      return
    }

    // Cancel any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    const userMessage: Message = {
      id: generateMessageId(),
      role: 'user',
      content: text.trim(),
      createdAt: new Date().toISOString(),
    }

    // Add user message immediately
    setMessages(prev => [...prev, userMessage])
    setIsStreaming(true)
    setError(null)

    // Create new abort controller
    const abortController = new AbortController()
    abortControllerRef.current = abortController

    // Create streaming message placeholder
    const streamingMessageId = generateMessageId()
    streamingMessageIdRef.current = streamingMessageId
    
    const assistantMessage: Message = {
      id: streamingMessageId,
      role: 'assistant',
      content: '',
      createdAt: new Date().toISOString(),
    }
    setMessages(prev => [...prev, assistantMessage])

    // Build request
    const request: ChatRequest = {
      message: text.trim(),
      session_id: sessionId,
      conversation_history: messages.map((msg): ChatHistoryItem => ({
        role: msg.role,
        content: msg.content,
      })),
    }

    let agentUsed: string | undefined
    let accumulatedContent = ''

    try {
      // Try streaming first
      try {
        const result = await sendChatSSE(
          request,
          (token: string) => {
            // Accumulate content but don't update state every token (will finalize once at end)
            accumulatedContent += token
            // Update streaming message with accumulated content for real-time display
            setMessages(prev =>
              prev.map(msg =>
                msg.id === streamingMessageId
                  ? { ...msg, content: accumulatedContent, agentUsed }
                  : msg
              )
            )
          },
          (event: StreamEvent) => {
            if (event.type === 'token' && event.agentUsed) {
              agentUsed = event.agentUsed
            }
            if (event.type === 'done') {
              if (event.sessionId) {
                setSessionId(event.sessionId)
              }
              if (event.agentUsed) {
                agentUsed = event.agentUsed
              }
            }
          },
          abortController
        )

        if (result.sessionId) {
          setSessionId(result.sessionId)
        }
        if (result.agentUsed) {
          agentUsed = result.agentUsed
        }

        // Finalize message once with accumulated content and agent info
        setMessages(prev =>
          prev.map(msg =>
            msg.id === streamingMessageId
              ? { ...msg, content: accumulatedContent, agentUsed }
              : msg
          )
        )
        
        // Clear accumulated content to avoid race conditions
        accumulatedContent = ''
      } catch (streamError) {
        // If streaming fails, try non-streaming fallback
        if (streamError instanceof NetworkError || 
            (streamError instanceof APIError && streamError.statusCode && streamError.statusCode >= 500)) {
          
          logger.warn('Streaming failed, falling back to non-streaming', streamError)
          
          // Remove streaming placeholder
          setMessages(prev => prev.filter(msg => msg.id !== streamingMessageId))
          
          // Try non-streaming POST
          const response = await sendChat(request)
          
          // Add final assistant message
          const finalMessage: Message = {
            id: generateMessageId(),
            role: 'assistant',
            content: response.response,
            agentUsed: response.agent_used,
            createdAt: response.timestamp,
          }
          
          setMessages(prev => [...prev, finalMessage])
          
          if (response.session_id) {
            setSessionId(response.session_id)
          }
        } else {
          // Re-throw non-retryable errors
          throw streamError
        }
      }
    } catch (err) {
      // Handle errors
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred'
      
      if (err instanceof APIError) {
        setError(`API Error: ${errorMessage}`)
      } else if (err instanceof NetworkError) {
        setError(`Network Error: ${errorMessage}. Please check your connection.`)
      } else {
        setError(`Error: ${errorMessage}`)
      }

      // Remove streaming placeholder and add error message
      setMessages(prev => {
        const filtered = prev.filter(msg => msg.id !== streamingMessageId)
        return [
          ...filtered,
          {
            id: generateMessageId(),
            role: 'assistant',
            content: `I apologize, but I encountered an error: ${errorMessage}. Please try again.`,
            createdAt: new Date().toISOString(),
          },
        ]
      })

      // Log error but don't expose full error details (might contain PII)
      logger.error('Chat error', {
        message: err instanceof Error ? err.message : 'Unknown error',
        type: err instanceof APIError ? 'APIError' : err instanceof NetworkError ? 'NetworkError' : 'Error',
        statusCode: err instanceof APIError ? err.statusCode : undefined,
      })
    } finally {
      setIsStreaming(false)
      streamingMessageIdRef.current = null
      abortControllerRef.current = null
    }
  }, [messages, sessionId, isStreaming])

  return {
    messages,
    isStreaming,
    error,
    sessionId,
    sendMessage,
    clearMessages,
    clearError,
  }
}

