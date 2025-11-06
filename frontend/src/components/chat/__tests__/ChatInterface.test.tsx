import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatInterface } from '../ChatInterface'

// Mock the API config
jest.mock('@/lib/api-config', () => ({
  getApiUrl: () => 'http://localhost:8000',
}))

describe('ChatInterface', () => {
  beforeEach(() => {
    global.fetch = jest.fn()
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('renders initial welcome message', () => {
    render(<ChatInterface />)
    
    expect(screen.getByText(/Hello! I'm your AI customer service assistant/i)).toBeInTheDocument()
  })

  it('renders input field', () => {
    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText(/type your message/i)
    expect(input).toBeInTheDocument()
  })

  it('allows user to type a message', async () => {
    const user = userEvent.setup()
    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText(/type your message/i) as HTMLTextAreaElement
    await user.type(input, 'Hello, test message')
    
    expect(input.value).toBe('Hello, test message')
  })

  it('submits message on form submit', async () => {
    const user = userEvent.setup()
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        response: 'Test response',
        agent_used: 'billing',
        session_id: 'test-session',
      }),
    })

    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText(/type your message/i)
    const submitButton = screen.getByRole('button', { name: /send/i })
    
    await user.type(input, 'Test message')
    await user.click(submitButton)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled()
    })
  })

  it('displays loading state while processing', async () => {
    const user = userEvent.setup()
    global.fetch = jest.fn().mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: async () => ({
          response: 'Response',
          agent_used: 'billing',
          session_id: 'test-session',
        }),
      }), 100))
    )

    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText(/type your message/i)
    const submitButton = screen.getByRole('button', { name: /send/i })
    
    await user.type(input, 'Test message')
    await user.click(submitButton)

    // Check for loading indicator
    await waitFor(() => {
      expect(screen.getByRole('button')).toBeDisabled()
    })
  })

  it('handles API errors gracefully', async () => {
    const user = userEvent.setup()
    global.fetch = jest.fn().mockRejectedValue(new Error('API Error'))

    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText(/type your message/i)
    const submitButton = screen.getByRole('button', { name: /send/i })
    
    await user.type(input, 'Test message')
    await user.click(submitButton)

    await waitFor(() => {
      // Should show error message or handle gracefully
      expect(global.fetch).toHaveBeenCalled()
    })
  })

  it('prevents empty message submission', async () => {
    const user = userEvent.setup()
    render(<ChatInterface />)
    
    const submitButton = screen.getByRole('button', { name: /send/i })
    await user.click(submitButton)

    expect(global.fetch).not.toHaveBeenCalled()
  })

  it('clears input after message submission', async () => {
    const user = userEvent.setup()
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        response: 'Response',
        agent_used: 'billing',
        session_id: 'test-session',
      }),
    })

    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText(/type your message/i) as HTMLTextAreaElement
    const submitButton = screen.getByRole('button', { name: /send/i })
    
    await user.type(input, 'Test message')
    await user.click(submitButton)

    await waitFor(() => {
      expect(input.value).toBe('')
    })
  })
})

