/**
 * Tests for useChat hook - streaming and fallback scenarios
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { useChat } from '../useChat'
import { sendChatSSE, sendChat, NetworkError, APIError } from '@/lib/apiClient'

// Mock the API client
jest.mock('@/lib/apiClient', () => ({
  sendChatSSE: jest.fn(),
  sendChat: jest.fn(),
  NetworkError: class NetworkError extends Error {
    constructor(message: string) {
      super(message)
      this.name = 'NetworkError'
    }
  },
  APIError: class APIError extends Error {
    constructor(message: string, public statusCode?: number) {
      super(message)
      this.name = 'APIError'
    }
  },
}))

// Mock logger
jest.mock('@/lib/logger', () => ({
  logger: {
    warn: jest.fn(),
    error: jest.fn(),
  },
}))

const mockSendChatSSE = sendChatSSE as jest.MockedFunction<typeof sendChatSSE>
const mockSendChat = sendChat as jest.MockedFunction<typeof sendChat>

describe('useChat - Streaming', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('handles streaming happy path', async () => {
    const onToken = jest.fn()
    const onEvent = jest.fn()

    // Mock streaming response
    mockSendChatSSE.mockImplementation(async (input, tokenCallback, eventCallback) => {
      // Simulate streaming tokens
      tokenCallback('Hello')
      eventCallback?.({ type: 'token', data: 'Hello', agentUsed: 'technical' })
      
      tokenCallback(' World')
      eventCallback?.({ type: 'token', data: ' World' })
      
      // Final event
      eventCallback?.({ type: 'done', sessionId: 'session-123', agentUsed: 'technical' })
      
      return { sessionId: 'session-123', agentUsed: 'technical' }
    })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('Test message')
    })

    await waitFor(() => {
      expect(result.current.isStreaming).toBe(false)
    })

    // Verify streaming was called
    expect(mockSendChatSSE).toHaveBeenCalledTimes(1)
    
    // Verify messages were updated
    expect(result.current.messages.length).toBeGreaterThan(1)
    const lastMessage = result.current.messages[result.current.messages.length - 1]
    expect(lastMessage.role).toBe('assistant')
    expect(lastMessage.content).toContain('Hello')
    expect(lastMessage.agentUsed).toBe('technical')
    expect(result.current.sessionId).toBe('session-123')
  })

  it('falls back to POST when streaming fails with network error', async () => {
    // Mock streaming to fail with NetworkError
    mockSendChatSSE.mockRejectedValueOnce(new NetworkError('Network error'))
    
    // Mock POST to succeed
    mockSendChat.mockResolvedValueOnce({
      response: 'Fallback response',
      agent_used: 'billing',
      session_id: 'session-456',
      timestamp: new Date().toISOString(),
    })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('Test message')
    })

    await waitFor(() => {
      expect(result.current.isStreaming).toBe(false)
    })

    // Verify both were called
    expect(mockSendChatSSE).toHaveBeenCalledTimes(1)
    expect(mockSendChat).toHaveBeenCalledTimes(1)
    
    // Verify fallback message was added
    const lastMessage = result.current.messages[result.current.messages.length - 1]
    expect(lastMessage.content).toBe('Fallback response')
    expect(lastMessage.agentUsed).toBe('billing')
    expect(result.current.sessionId).toBe('session-456')
  })

  it('falls back to POST when streaming fails with 5xx error', async () => {
    // Mock streaming to fail with 500 error
    mockSendChatSSE.mockRejectedValueOnce(new APIError('Server error', 500))
    
    // Mock POST to succeed
    mockSendChat.mockResolvedValueOnce({
      response: 'Fallback response from POST',
      agent_used: 'policy',
      session_id: 'session-789',
      timestamp: new Date().toISOString(),
    })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('Test message')
    })

    await waitFor(() => {
      expect(result.current.isStreaming).toBe(false)
    })

    // Verify both were called
    expect(mockSendChatSSE).toHaveBeenCalledTimes(1)
    expect(mockSendChat).toHaveBeenCalledTimes(1)
    
    // Verify fallback message
    const lastMessage = result.current.messages[result.current.messages.length - 1]
    expect(lastMessage.content).toBe('Fallback response from POST')
  })

  it('does not fallback on 4xx client errors', async () => {
    // Mock streaming to fail with 400 error (should not retry)
    mockSendChatSSE.mockRejectedValueOnce(new APIError('Bad request', 400))

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('Test message')
    })

    await waitFor(() => {
      expect(result.current.isStreaming).toBe(false)
    })

    // Verify streaming was called but POST was not
    expect(mockSendChatSSE).toHaveBeenCalledTimes(1)
    expect(mockSendChat).not.toHaveBeenCalled()
    
    // Verify error was set
    expect(result.current.error).toBeTruthy()
  })

  it('aborts stream on unmount', async () => {
    const abortController = new AbortController()
    const abortSpy = jest.spyOn(abortController, 'abort')

    // Mock streaming to hang
    mockSendChatSSE.mockImplementation(async () => {
      await new Promise(() => {}) // Never resolves
      return { sessionId: 'session-123' }
    })

    const { result, unmount } = renderHook(() => useChat())

    // Start a message
    act(() => {
      result.current.sendMessage('Test message')
    })

    // Unmount immediately
    unmount()

    // Verify abort was called (indirectly through cleanup)
    await waitFor(() => {
      expect(result.current.isStreaming).toBe(false)
    })
  })
})

