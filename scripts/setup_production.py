#!/usr/bin/env python3
"""
Production Environment Setup Script

Generates secure credentials and creates production-ready .env file.
Run this script to prepare your environment for production deployment.

Usage:
    python scripts/setup_production.py [--output .env.production]
"""
import secrets
import argparse
import sys
from pathlib import Path


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def generate_jwt_secret() -> str:
    """Generate a secure JWT secret (64 characters)."""
    return secrets.token_urlsafe(64)


def generate_encryption_key() -> str:
    """Generate a secure encryption key."""
    return secrets.token_urlsafe(32)


def create_production_env(output_path: str = ".env.production") -> None:
    """
    Create a production .env file with secure generated credentials.

    Args:
        output_path: Path to output .env file
    """
    print("🔐 Generating secure production credentials...")
    print()

    # Generate credentials
    api_key_1 = generate_api_key()
    api_key_2 = generate_api_key()
    jwt_secret = generate_jwt_secret()
    encryption_key = generate_encryption_key()

    print("✅ Generated credentials:")
    print(f"   - API Key 1: {api_key_1[:20]}... (44 characters)")
    print(f"   - API Key 2: {api_key_2[:20]}... (44 characters)")
    print(f"   - JWT Secret: {jwt_secret[:20]}... (88 characters)")
    print(f"   - Encryption Key: {encryption_key[:20]}... (44 characters)")
    print()

    # Create .env content
    env_content = f"""# ============================================
# PRODUCTION ENVIRONMENT CONFIGURATION
# ============================================
# Generated: {Path(__file__).name}
# WARNING: Keep this file secure! Never commit to git!
# ============================================

# ============================================
# Environment Settings
# ============================================
ENVIRONMENT=production
LOG_LEVEL=INFO

# ============================================
# AWS Configuration
# ============================================
# IMPORTANT: Use IAM roles in production instead of access keys!
# Only set these if you cannot use IAM roles
# AWS_ACCESS_KEY_ID=your-aws-access-key-id
# AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-west-2

# Optional: If using AWS SSO or temporary credentials
# AWS_SESSION_TOKEN=your-session-token

# Bedrock Model Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_SERVICE_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# ============================================
# OpenAI Configuration (if not using Bedrock exclusively)
# ============================================
# OPENAI_API_KEY=sk-your-openai-api-key-here
# OPENAI_MODEL=gpt-4o

# ============================================
# API Configuration
# ============================================
API_HOST=0.0.0.0
API_PORT=8000

# ============================================
# CRITICAL: Authentication & Security
# ============================================
# Enable authentication (REQUIRED for production)
REQUIRE_AUTHENTICATION=true

# API Keys for X-API-Key header authentication
# IMPORTANT: Store these securely and share only with authorized clients
API_KEYS={api_key_1},{api_key_2}

# JWT Configuration
JWT_SECRET_KEY={jwt_secret}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# ============================================
# HTTPS & Transport Security
# ============================================
# Enable HTTPS enforcement (REQUIRED for production)
ENFORCE_HTTPS=true

# Allowed hostnames (comma-separated, no wildcards)
# Replace with your actual domain(s)
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# ============================================
# CORS Configuration
# ============================================
# IMPORTANT: Set to your actual frontend URL(s) - NO wildcards!
# Replace with your actual frontend domain
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=Content-Type,Authorization,X-API-Key

# Frontend URL
FRONTEND_URL=https://yourdomain.com

# ============================================
# Rate Limiting
# ============================================
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=500

# ============================================
# Request Security
# ============================================
MAX_REQUEST_SIZE=10485760

# ============================================
# Data Security & Privacy
# ============================================
# Enable encryption for sensitive data at rest
ENABLE_ENCRYPTION_AT_REST=true
ENCRYPTION_KEY={encryption_key}

# Mask PII in logs (REQUIRED for production)
MASK_PII_IN_LOGS=true

# ============================================
# Vector Database
# ============================================
CHROMA_PERSIST_DIRECTORY=/var/lib/customer-service-ai/chroma_db

# ============================================
# AWS Secrets Manager (Recommended)
# ============================================
# Enable for automatic secret rotation and better security
ENABLE_SECRETS_MANAGER=false
SECRETS_MANAGER_REGION=us-west-2
SECRETS_MANAGER_SECRET_NAME=customer-service-ai-prod-secrets

# ============================================
# PRODUCTION VALIDATION CHECKLIST
# ============================================
# ✓ ENVIRONMENT=production
# ✓ REQUIRE_AUTHENTICATION=true
# ✓ API_KEYS set with secure random values (GENERATED)
# ✓ JWT_SECRET_KEY set with secure random value (GENERATED)
# ✓ ENFORCE_HTTPS=true
# ✓ CORS_ORIGINS set to specific domains (UPDATE WITH YOUR DOMAIN!)
# ✓ MASK_PII_IN_LOGS=true
# ✓ LOG_LEVEL=INFO
# ⚠️  SSL/TLS certificates configured (DO THIS NEXT)
# ⚠️  Update ALLOWED_HOSTS with your domain
# ⚠️  Update CORS_ORIGINS with your frontend URL
# ⚠️  Configure monitoring and alerts
# ⚠️  Set up backup for /var/lib/customer-service-ai

# ============================================
# NEXT STEPS
# ============================================
# 1. Update domain-specific settings:
#    - ALLOWED_HOSTS
#    - CORS_ORIGINS
#    - FRONTEND_URL
#
# 2. Configure SSL/TLS certificates:
#    - Option A: Use AWS Certificate Manager (ACM)
#    - Option B: Use Let's Encrypt with certbot
#
# 3. Set up AWS IAM role (recommended over access keys):
#    - Create IAM role with Bedrock permissions
#    - Attach role to EC2/ECS/Lambda
#    - Remove AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
#
# 4. Configure monitoring:
#    - Set up CloudWatch logs
#    - Configure alerts for errors
#    - Set up APM (e.g., Datadog, New Relic)
#
# 5. Test the deployment:
#    - Run: curl https://yourdomain.com/health
#    - Verify authentication works
#    - Check logs for any errors
#
# 6. Run security scans:
#    - python scripts/run_security_scan.py
#    - Fix any issues found
"""

    # Write to file
    output_file = Path(output_path)

    # Check if file exists
    if output_file.exists():
        response = input(f"⚠️  {output_path} already exists. Overwrite? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Aborted. File not modified.")
            sys.exit(1)

    output_file.write_text(env_content)

    # Set secure permissions (owner read/write only)
    output_file.chmod(0o600)

    print(f"✅ Production environment file created: {output_path}")
    print(f"   Permissions set to 0o600 (owner read/write only)")
    print()
    print("📋 CRITICAL NEXT STEPS:")
    print("   1. Edit the file and update domain-specific settings:")
    print("      - ALLOWED_HOSTS")
    print("      - CORS_ORIGINS")
    print("      - FRONTEND_URL")
    print()
    print("   2. Configure SSL/TLS certificates for HTTPS")
    print()
    print("   3. Set up AWS IAM role (preferred over access keys)")
    print()
    print("   4. NEVER commit this file to git!")
    print(f"      Add '{output_path}' to .gitignore if not already there")
    print()
    print("🔒 Store these credentials securely:")
    print(f"   - API Key 1: {api_key_1}")
    print(f"   - API Key 2: {api_key_2}")
    print()
    print("   Share API keys only with authorized API clients.")
    print("   Consider using a password manager or secrets vault.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate production environment configuration with secure credentials"
    )
    parser.add_argument(
        '--output',
        default='.env.production',
        help='Output file path (default: .env.production)'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🚀 Production Environment Setup")
    print("=" * 60)
    print()

    create_production_env(args.output)

    print()
    print("=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
