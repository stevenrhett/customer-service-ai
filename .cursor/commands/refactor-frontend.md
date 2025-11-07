.cursor/commands/refactor-frontend.md
# name: refactor-frontend
# description: Normalize Next.js app; centralize API + streaming; strong typing.
Restructure `frontend/`:
- src/lib/apiClient.ts (SSE + POST fallback)
- src/hooks/useChat.ts (chat state + sendMessage)
- src/hooks/useEventSource.ts (generic SSE with auto-retry)
- src/components/{ChatWindow,MessageList,MessageItem,MessageInput,StreamingText,LoadingDots}.tsx
- app/page.tsx renders <ChatWindow/>
Ensure strict TS, mobile-first Tailwind, no secrets, and Jest + RTL tests pass.
