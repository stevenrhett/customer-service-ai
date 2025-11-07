"use client"

import { useChat } from "@/hooks/useChat"
import { MessageList } from "./MessageList"
import { MessageInput } from "./MessageInput"

/**
 * Main chat window component that composes all chat UI elements
 */
export function ChatWindow() {
  const { messages, isStreaming, error, sendMessage } = useChat()

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <div className="border-b px-6 py-4 bg-card">
        <h1 className="text-2xl font-bold">Customer Service AI</h1>
        <p className="text-sm text-muted-foreground">
          Multi-agent support system with specialized agents
        </p>
        {error && (
          <div className="mt-2 p-2 bg-destructive/10 text-destructive text-sm rounded">
            {error}
          </div>
        )}
      </div>

      {/* Messages */}
      <MessageList messages={messages} isStreaming={isStreaming} />

      {/* Input */}
      <div className="border-t bg-card px-4 py-4">
        <div className="max-w-4xl mx-auto">
          <MessageInput onSend={sendMessage} disabled={isStreaming} />
        </div>
      </div>
    </div>
  )
}

