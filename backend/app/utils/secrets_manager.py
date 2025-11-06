"""
AWS Secrets Manager integration for secure credential management.
"""
import json
import logging
from typing import Optional, Dict
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def load_secrets_from_manager() -> Optional[Dict[str, str]]:
    """
    Load secrets from AWS Secrets Manager.
    
    Returns:
        Dictionary of secrets or None if not enabled/available
    """
    if not settings.enable_secrets_manager:
        return None
    
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        if not settings.secrets_manager_secret_name:
            logger.warning("Secrets Manager enabled but secret name not configured")
            return None
        
        region = settings.secrets_manager_region or settings.aws_region
        client = boto3.client('secretsmanager', region_name=region)
        
        try:
            response = client.get_secret_value(SecretId=settings.secrets_manager_secret_name)
            secret_string = response.get('SecretString', '{}')
            
            # Parse JSON secrets
            secrets = json.loads(secret_string)
            logger.info("Successfully loaded secrets from AWS Secrets Manager")
            return secrets
        except ClientError as e:
            logger.error(f"Error retrieving secret from AWS Secrets Manager: {e}")
            return None
    except ImportError:
        logger.warning("boto3 not available for Secrets Manager integration")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading secrets: {e}")
        return None

def get_secret_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a secret value, checking Secrets Manager first, then environment.
    
    Args:
        key: Secret key name
        default: Default value if not found
        
    Returns:
        Secret value or default
    """
    secrets = load_secrets_from_manager()
    if secrets and key in secrets:
        return secrets[key]
    
    # Fallback to environment variable
    import os
    return os.getenv(key, default)

