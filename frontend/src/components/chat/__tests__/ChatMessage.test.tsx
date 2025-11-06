import { render, screen } from '@testing-library/react'
import { ChatMessage } from '../ChatMessage'

describe('ChatMessage', () => {
  it('renders user message correctly', () => {
    render(
      <ChatMessage
        role="user"
        content="Hello, how can I help?"
      />
    )

    expect(screen.getByText('You')).toBeInTheDocument()
    expect(screen.getByText('Hello, how can I help?')).toBeInTheDocument()
  })

  it('renders assistant message correctly', () => {
    render(
      <ChatMessage
        role="assistant"
        content="I can help you with that!"
      />
    )

    expect(screen.getByText('AI Assistant')).toBeInTheDocument()
    expect(screen.getByText('I can help you with that!')).toBeInTheDocument()
  })

  it('displays agent badge for assistant messages', () => {
    render(
      <ChatMessage
        role="assistant"
        content="Billing information"
        agentUsed="billing"
      />
    )

    expect(screen.getByText('billing')).toBeInTheDocument()
  })

  it('does not display agent badge for user messages', () => {
    render(
      <ChatMessage
        role="user"
        content="What are your pricing plans?"
        agentUsed="billing"
      />
    )

    expect(screen.queryByText('billing')).not.toBeInTheDocument()
  })

  it('handles long messages correctly', () => {
    const longMessage = 'A'.repeat(1000)
    render(
      <ChatMessage
        role="assistant"
        content={longMessage}
      />
    )

    expect(screen.getByText(longMessage)).toBeInTheDocument()
  })

  it('handles empty content gracefully', () => {
    render(
      <ChatMessage
        role="assistant"
        content=""
      />
    )

    expect(screen.getByText('AI Assistant')).toBeInTheDocument()
  })
})

