# name: harden-frontend-networking

# description: Improve SSE robustness, timeouts, and typing; add tests.

Apply to frontend/:

- Update apiClient.ts to support multi-line SSE events with 'event:' fields, CRLF handling, and a 90s timeout using AbortController.

- Reconcile ChatResponse and StreamChunk types with useChat usage.

- Apply withRetry to SSE path for network/5xx only.

- In useChat, finalize the streaming message once and guard against race conditions during setState.

- Add aria-live="polite" to the streaming message container.

- Add tests: streaming happy-path and fallback-to-POST.

Acceptance: npm run lint && npm run typecheck && npm test pass.

