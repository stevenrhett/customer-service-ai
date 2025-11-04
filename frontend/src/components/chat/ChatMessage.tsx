"use client"

import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import { Bot, User } from "lucide-react"

interface ChatMessageProps {
  role: "user" | "assistant"
  content: string
  agentUsed?: string
}

export function ChatMessage({ role, content, agentUsed }: ChatMessageProps) {
  const isUser = role === "user"

  return (
    <div
      className={cn(
        "flex gap-3 p-4 rounded-lg",
        isUser ? "bg-muted/50 ml-12" : "bg-background"
      )}
    >
      {!isUser && (
        <Avatar className="h-8 w-8">
          <AvatarFallback className="bg-primary text-primary-foreground">
            <Bot className="h-5 w-5" />
          </AvatarFallback>
        </Avatar>
      )}
      
      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <p className="font-semibold text-sm">
            {isUser ? "You" : "AI Assistant"}
          </p>
          {agentUsed && !isUser && (
            <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
              {agentUsed}
            </span>
          )}
        </div>
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
      </div>

      {isUser && (
        <Avatar className="h-8 w-8">
          <AvatarFallback className="bg-secondary">
            <User className="h-5 w-5" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  )
}
