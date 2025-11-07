"""
Credential Test Script
Run this to verify your OpenAI and AWS credentials are working correctly.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import get_settings


def test_openai():
    """Test OpenAI API connection"""
    print("\n" + "=" * 60)
    print("Testing OpenAI Connection")
    print("=" * 60)

    try:
        from langchain_openai import ChatOpenAI

        settings = get_settings()

        llm = ChatOpenAI(
            model="gpt-3.5-turbo", temperature=0, openai_api_key=settings.openai_api_key
        )

        response = llm.invoke("Say 'OpenAI connection successful!'")
        print("✓ OpenAI API Key: Valid")
        print(f"✓ Response: {response.content}")
        return True

    except Exception as e:
        print(f"✗ OpenAI Error: {e}")
        return False


def test_aws_bedrock():
    """Test AWS Bedrock connection"""
    print("\n" + "=" * 60)
    print("Testing AWS Bedrock Connection")
    print("=" * 60)

    try:
        import boto3

        settings = get_settings()

        # Test basic AWS connection
        client = boto3.client("bedrock", region_name=settings.aws_region)

        print(f"✓ AWS Region: {settings.aws_region}")
        print("✓ AWS Credentials: Loaded")

        # Try to list models
        try:
            response = client.list_foundation_models()
            claude_models = [
                m["modelId"]
                for m in response["modelSummaries"]
                if "claude" in m["modelId"].lower()
            ]

            print("✓ Bedrock Access: Granted")
            print("✓ Available Claude Models:")
            for model in claude_models[:3]:  # Show first 3
                print(f"  - {model}")

            return True

        except Exception as e:
            if "AccessDeniedException" in str(e):
                print("⚠ Bedrock Access: Credentials work, but Bedrock not enabled")
                print("  Contact your instructor to enable Bedrock access")
            else:
                print(f"⚠ Bedrock Error: {e}")
            return False

    except Exception as e:
        print(f"✗ AWS Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure AWS credentials are in .env file")
        print("2. Check AWS_CREDENTIALS_GUIDE.md for setup instructions")
        print("3. Verify credentials haven't expired (if using temporary)")
        return False


def test_chroma_setup():
    """Test ChromaDB setup"""
    print("\n" + "=" * 60)
    print("Testing ChromaDB Setup")
    print("=" * 60)

    try:
        settings = get_settings()
        db_path = Path(settings.chroma_persist_directory)

        if db_path.exists():
            print(f"✓ ChromaDB Directory: {db_path}")

            # Check for collections
            import chromadb

            client = chromadb.PersistentClient(path=str(db_path))
            collections = client.list_collections()

            if collections:
                print(f"✓ Collections Found: {len(collections)}")
                for col in collections:
                    count = col.count()
                    print(f"  - {col.name}: {count} documents")
                return True
            else:
                print("⚠ No collections found")
                print("  Run: python scripts/ingest_data.py")
                return False
        else:
            print("⚠ ChromaDB not initialized")
            print("  Run: python scripts/ingest_data.py")
            return False

    except Exception as e:
        print(f"✗ ChromaDB Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("CUSTOMER SERVICE AI - CREDENTIAL TEST")
    print("=" * 60)

    results = {
        "OpenAI": test_openai(),
        "AWS Bedrock": test_aws_bedrock(),
        "ChromaDB": test_chroma_setup(),
    }

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for service, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{service:.<30} {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 All tests passed! You're ready to run the application.")
        print("\nNext steps:")
        print("1. Start backend: python -m app.main")
        print("2. Start frontend: cd ../frontend && npm run dev")
        print("3. Open browser: http://localhost:3000")
    else:
        print("\n⚠️  Some tests failed. Review the errors above.")
        print("\nQuick fixes:")
        if not results["OpenAI"]:
            print("- Check OPENAI_API_KEY in .env")
        if not results["AWS Bedrock"]:
            print("- Follow AWS_CREDENTIALS_GUIDE.md to get AWS credentials")
        if not results["ChromaDB"]:
            print("- Run: python scripts/ingest_data.py")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
