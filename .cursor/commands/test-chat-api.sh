# Test Chat API
# Tests the chat endpoint with a sample message

curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are your pricing plans?",
    "session_id": "test-session"
  }' | python -m json.tool

