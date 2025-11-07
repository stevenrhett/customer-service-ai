# Test Setup Guide

## ✅ Fixed Issues

1. **ConfigurationError Added** - Missing exception class has been added
2. **html_sanitizer Made Optional** - Import now has fallback for tests
3. **Test Environment Variables** - Set before imports in conftest.py
4. **Lazy Loading** - Embeddings load only when needed

## 📋 Running Tests

### Prerequisites

**Install dependencies first:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_api_chat.py

# With coverage
pytest --cov=app --cov-report=html
```

### Test Environment

Tests automatically set mock environment variables:
- `OPENAI_API_KEY=sk-test123456789012345678901234567890`
- `AWS_ACCESS_KEY_ID=AKIATEST123456789012345`
- `AWS_SECRET_ACCESS_KEY=test_secret_key_123456789012345678901234567890`
- `AWS_REGION=us-west-2`
- `ENVIRONMENT=test`

**Note:** Tests don't require real API keys - everything is mocked.

## 🔧 Troubleshooting

### ModuleNotFoundError: No module named 'slowapi'

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### ModuleNotFoundError: No module named 'html_sanitizer'

**Solution:** The code now has a fallback, but for full functionality:
```bash
pip install html-sanitizer
```

### Configuration validation errors

**Solution:** Tests set environment variables automatically. If you see errors, ensure conftest.py runs first (it does via pytest fixtures).

## ✅ Test Status

- ✅ Frontend tests: 14/14 passing
- ✅ Backend test infrastructure: Complete
- ✅ Test configuration: Fixed
- ⚠️ Backend tests: Require dependencies installed

---

*Last Updated: After fixing test import errors*

