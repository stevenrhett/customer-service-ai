"""Basic tests to verify application structure and imports."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    # Test config
    from app.config import Settings, get_settings
    print("✓ Config imports successful")
    
    # Test models
    from app.models.schemas import ChatRequest, ChatResponse, DocumentUploadResponse
    print("✓ Models imports successful")
    
    # Test base agent
    from app.agents.base_agent import BaseAgent
    print("✓ Base agent imports successful")
    
    # Test services (without API key)
    print("✓ All imports successful!")
    
    return True

def test_models():
    """Test Pydantic models."""
    from app.models.schemas import ChatRequest, ChatResponse
    
    print("\nTesting Pydantic models...")
    
    # Test ChatRequest
    request = ChatRequest(message="Test message")
    assert request.message == "Test message"
    assert request.conversation_id is None
    print("✓ ChatRequest model works")
    
    # Test ChatResponse
    response = ChatResponse(
        response="Test response",
        conversation_id="123",
        agent_used="Test Agent"
    )
    assert response.response == "Test response"
    assert response.conversation_id == "123"
    print("✓ ChatResponse model works")
    
    return True

def test_base_agent():
    """Test base agent structure."""
    from app.agents.base_agent import BaseAgent
    
    print("\nTesting base agent...")
    
    class TestAgent(BaseAgent):
        def process(self, query: str, context: dict) -> str:
            return "Test response"
    
    agent = TestAgent("Test Agent", "A test agent")
    assert agent.name == "Test Agent"
    assert agent.description == "A test agent"
    assert agent.can_handle("test") is True
    assert agent.process("test", {}) == "Test response"
    print("✓ Base agent structure works")
    
    return True

def test_config():
    """Test configuration."""
    from app.config import Settings
    
    print("\nTesting configuration...")
    
    settings = Settings()
    assert hasattr(settings, 'openai_api_key')
    assert hasattr(settings, 'chroma_db_path')
    assert hasattr(settings, 'environment')
    print("✓ Configuration structure works")
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("Running Backend Tests")
    print("=" * 50)
    
    try:
        test_imports()
        test_models()
        test_base_agent()
        test_config()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
