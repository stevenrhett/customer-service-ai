# Cursor Commands

This directory contains project-specific Cursor commands that can be executed directly from Cursor's command palette.

## Available Commands

### Development Commands

- **start-backend.sh** - Starts the FastAPI backend server with hot reload
- **start-frontend.sh** - Starts the Next.js frontend development server
- **start-all.sh** - Starts both backend and frontend servers concurrently

### Setup & Maintenance Commands

- **setup-project.sh** - Installs dependencies for both backend and frontend
- **ingest-data.sh** - Runs the data ingestion script to populate ChromaDB vector stores
- **verify-ingestion.sh** - Verifies that ChromaDB collections exist and contain data

### Testing & Quality Commands

- **test-backend.sh** - Runs pytest tests for the backend
- **test-chat-api.sh** - Tests the chat endpoint with a sample message
- **lint-backend.sh** - Runs linting checks on backend Python code
- **format-backend.sh** - Formats Python code using black

### Utility Commands

- **check-status.sh** - Checks if backend and frontend are running and verifies setup
- **clean.sh** - Removes generated files and caches

## Usage

1. Open Cursor's command palette (`Cmd+Shift+P` on Mac, `Ctrl+Shift+P` on Windows/Linux)
2. Type "Cursor: Run Command" or search for the command name
3. Select the command you want to run

## Environment Variables

Make sure you have the following environment variables set:

**Backend (.env):**
- `OPENAI_API_KEY`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `CORS_ORIGINS`

**Frontend (.env.local):**
- `NEXT_PUBLIC_API_URL`

## Example Workflow

1. First time setup:
   ```bash
   setup-project.sh
   ```

2. Ingest data:
   ```bash
   ingest-data.sh
   ```

3. Check status:
   ```bash
   check-status.sh
   ```

4. Start development:
   ```bash
   start-all.sh
   ```

