"use client"

import { useEffect, useRef } from 'react'
import { ScrollArea } from "@/components/ui/scroll-area"
import { MessageItem } from "./MessageItem"
import { LoadingDots } from "./LoadingDots"
import type { Message } from "@/lib/types"

interface MessageListProps {
  messages: Message[]
  isStreaming: boolean
}

/**
 * Message list component with auto-scroll
 */
export function MessageList({ messages, isStreaming }: MessageListProps) {
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive or streaming updates
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }, [messages, isStreaming])

  return (
    <ScrollArea className="flex-1 px-4" ref={scrollAreaRef}>
      <div className="max-w-4xl mx-auto py-4 space-y-4">
        {messages.map((message, index) => (
          <MessageItem
            key={message.id}
            message={message}
            isStreaming={isStreaming && message.role === 'assistant' && index === messages.length - 1}
          />
        ))}
        {isStreaming && (
          <div className="flex gap-3 p-4">
            <LoadingDots className="text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Thinking...</p>
          </div>
        )}
      </div>
    </ScrollArea>
  )
}

