"use client"

import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import { Bot, User } from "lucide-react"
import { StreamingText } from "./StreamingText"
import type { Message } from "@/lib/types"

interface MessageItemProps {
  message: Message
  isStreaming?: boolean
}

/**
 * Individual message item component with role-aware styling
 */
export function MessageItem({ message, isStreaming = false }: MessageItemProps) {
  const isUser = message.role === 'user'

  return (
    <div
      className={cn(
        "flex gap-3 p-4 rounded-lg",
        isUser ? "bg-muted/50 ml-12" : "bg-background"
      )}
    >
      {!isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback className="bg-primary text-primary-foreground">
            <Bot className="h-5 w-5" />
          </AvatarFallback>
        </Avatar>
      )}
      
      <div className="flex-1 space-y-2 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="font-semibold text-sm">
            {isUser ? "You" : "AI Assistant"}
          </p>
          {message.agentUsed && !isUser && (
            <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
              {message.agentUsed}
            </span>
          )}
        </div>
        {isStreaming && !isUser ? (
          <StreamingText
            text={message.content}
            className="text-sm leading-relaxed whitespace-pre-wrap"
          />
        ) : (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.content || '\u00A0'}
          </p>
        )}
      </div>

      {isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          <AvatarFallback className="bg-secondary">
            <User className="h-5 w-5" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  )
}

