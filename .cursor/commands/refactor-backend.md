.cursor/commands/refactor-backend.md
# depends_on: .cursor/rules/architecture-guardrails.mdc
# name: refactor-backend
# description: Clean and layer the FastAPI/LangGraph backend per project rules.
Refactor code under `backend/app` to this structure:
- api/v1/chat.py routes only (no business logic)
- services/* business rules (router_service, billing_service, technical_service, policy_service)
- agents/* model adapters only
- chains/orchestrator.py builds the LangGraph graph
- utils/* logging + chroma loader
Move logic accordingly, add type hints, and fix imports.
Acceptance:
- server boots
- /api/v1/chat (JSON) and /api/v1/chat/stream (SSE) work
- ruff/black pass

