#!/usr/bin/env python3
"""
Quick setup checker - verifies all prerequisites are met.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.services.vector_store import vector_store_service
from app.utils.logging import get_logger

logger = get_logger(__name__)


def check_environment():
    """Check environment variables."""
    print("🔍 Checking Environment Variables...")
    try:
        settings = get_settings()
        print("  ✅ Configuration loaded successfully")
        print(f"     Environment: {settings.environment}")
        print(f"     AWS Region: {settings.aws_region}")
        print(f"     OpenAI Model: {settings.openai_model}")
        print(f"     Bedrock Model: {settings.bedrock_model_id}")
        return True
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False


def check_vector_stores():
    """Check if vector stores are initialized."""
    print("\n🔍 Checking Vector Stores...")
    issues = []
    
    try:
        billing_store = vector_store_service.get_billing_store()
        if billing_store and hasattr(billing_store, '_collection'):
            count = billing_store._collection.count()
            print(f"  ✅ Billing store: {count} documents")
        else:
            print("  ⚠️  Billing store: Not fully initialized")
            issues.append("billing")
    except Exception as e:
        print(f"  ❌ Billing store error: {e}")
        issues.append("billing")
    
    try:
        technical_store = vector_store_service.get_technical_store()
        if technical_store and hasattr(technical_store, '_collection'):
            count = technical_store._collection.count()
            print(f"  ✅ Technical store: {count} documents")
        else:
            print("  ⚠️  Technical store: Not fully initialized")
            issues.append("technical")
    except Exception as e:
        print(f"  ❌ Technical store error: {e}")
        issues.append("technical")
    
    # Policy service uses Pure CAG (static documents), not vector store
    # Check if policy documents exist instead
    try:
        policy_docs_path = Path(__file__).parent.parent / "data" / "raw" / "policy"
        if policy_docs_path.exists() and list(policy_docs_path.glob("*.txt")):
            print(f"  ✅ Policy documents: Found in {policy_docs_path}")
        else:
            print(f"  ⚠️  Policy documents: Not found in {policy_docs_path}")
            issues.append("policy")
    except Exception as e:
        print(f"  ❌ Policy documents error: {e}")
        issues.append("policy")
    
    if issues:
        print(f"\n  ⚠️  Missing stores: {', '.join(issues)}")
        print("  💡 Run: python scripts/ingest_data.py")
        return False
    
    return True


def check_chroma_db():
    """Check if ChromaDB directory exists."""
    print("\n🔍 Checking ChromaDB Directory...")
    chroma_dir = Path(__file__).parent.parent / "chroma_db"
    if chroma_dir.exists():
        print(f"  ✅ ChromaDB directory exists: {chroma_dir}")
        return True
    else:
        print(f"  ⚠️  ChromaDB directory not found: {chroma_dir}")
        print("  💡 Run: python scripts/ingest_data.py")
        return False


def main():
    """Run all checks."""
    print("=" * 50)
    print("Customer Service AI - Setup Checker")
    print("=" * 50)
    print()
    
    results = []
    
    # Check environment
    results.append(("Environment", check_environment()))
    
    # Check ChromaDB directory
    results.append(("ChromaDB Directory", check_chroma_db()))
    
    # Check vector stores
    results.append(("Vector Stores", check_vector_stores()))
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All checks passed! Your setup is ready.")
        return 0
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

