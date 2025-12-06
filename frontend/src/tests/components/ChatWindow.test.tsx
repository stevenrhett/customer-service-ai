/**
 * Tests for ChatWindow component
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatWindow } from '@/components/chat/ChatWindow'

import { useChat } from '@/hooks/useChat'

// Mock the useChat hook
jest.mock('@/hooks/useChat', () => ({
  useChat: jest.fn(),
}))

const mockUseChat = useChat as jest.MockedFunction<typeof useChat>

describe('ChatWindow', () => {
  const mockSendMessage = jest.fn()
  const defaultReturn = {
    messages: [
      {
        id: '1',
        role: 'assistant' as const,
        content: 'Hello! How can I help you?',
        createdAt: new Date().toISOString(),
      },
    ],
    isStreaming: false,
    error: null,
    sessionId: undefined,
    sendMessage: mockSendMessage,
    clearMessages: jest.fn(),
    clearError: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
    mockUseChat.mockReturnValue(defaultReturn)
  })

  it('renders the chat window with header', () => {
    render(<ChatWindow />)
    
    expect(screen.getByText('Customer Service AI')).toBeInTheDocument()
    expect(screen.getByText(/Multi-agent support system/)).toBeInTheDocument()
  })

  it('renders initial assistant message', () => {
    render(<ChatWindow />)
    
    expect(screen.getByText('Hello! How can I help you?')).toBeInTheDocument()
  })

  it('renders user messages', () => {
    mockUseChat.mockReturnValue({
      ...defaultReturn,
      messages: [
        {
          id: '1',
          role: 'assistant' as const,
          content: 'Hello!',
          createdAt: new Date().toISOString(),
        },
        {
          id: '2',
          role: 'user' as const,
          content: 'Test message',
          createdAt: new Date().toISOString(),
        },
      ],
    })

    render(<ChatWindow />)
    
    expect(screen.getByText('Test message')).toBeInTheDocument()
  })

  it('displays error message when error exists', () => {
    mockUseChat.mockReturnValue({
      ...defaultReturn,
      error: 'Network error occurred',
    })

    render(<ChatWindow />)
    
    expect(screen.getByText('Network error occurred')).toBeInTheDocument()
  })

  it('sends message when user submits', async () => {
    const user = userEvent.setup()
    render(<ChatWindow />)

    const input = screen.getByLabelText(/message input/i)
    const sendButton = screen.getByLabelText(/send message/i)

    await user.type(input, 'Hello, AI!')
    await user.click(sendButton)

    await waitFor(() => {
      expect(mockSendMessage).toHaveBeenCalledWith('Hello, AI!')
    })
  })

  it('disables input during streaming', () => {
    mockUseChat.mockReturnValue({
      ...defaultReturn,
      isStreaming: true,
    })

    render(<ChatWindow />)
    
    const input = screen.getByLabelText(/message input/i)
    expect(input).toBeDisabled()
  })

  it('shows loading indicator during streaming', () => {
    mockUseChat.mockReturnValue({
      ...defaultReturn,
      isStreaming: true,
    })

    render(<ChatWindow />)
    
    expect(screen.getByText(/Thinking.../i)).toBeInTheDocument()
  })
})

