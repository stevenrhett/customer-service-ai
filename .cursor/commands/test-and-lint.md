.cursor/commands/test-and-lint.md
# name: test-and-lint
# description: Run full quality gates for both apps.
Run:
- backend: ruff check, black --check, pytest -q
- frontend: npm run lint, npm run typecheck, npm test
Report any failures with exact file/line and a minimal edit plan.