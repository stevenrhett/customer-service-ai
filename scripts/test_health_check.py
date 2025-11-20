#!/usr/bin/env python3
"""
Production Health Check Validator

Tests all health check endpoints and validates production configuration.

Usage:
    python scripts/test_health_check.py [--url https://yourdomain.com]
"""
import argparse
import sys
import json
import urllib.request
import urllib.error
from typing import Dict, List, Tuple


class Colors:
    """Terminal colors for output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def check_endpoint(url: str, api_key: str = None) -> Tuple[bool, Dict, str]:
    """
    Check an endpoint and return status.

    Args:
        url: Endpoint URL
        api_key: Optional API key for authentication

    Returns:
        Tuple of (success, response_data, error_message)
    """
    try:
        req = urllib.request.Request(url)

        if api_key:
            req.add_header('X-API-Key', api_key)

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return True, data, ""

    except urllib.error.HTTPError as e:
        try:
            error_data = json.loads(e.read().decode())
            return False, error_data, f"HTTP {e.code}: {error_data.get('error', str(e))}"
        except:
            return False, {}, f"HTTP {e.code}: {str(e)}"

    except urllib.error.URLError as e:
        return False, {}, f"Connection error: {str(e.reason)}"

    except Exception as e:
        return False, {}, f"Error: {str(e)}"


def validate_health_response(data: Dict) -> List[str]:
    """
    Validate health check response data.

    Args:
        data: Health check response

    Returns:
        List of validation issues (empty if all good)
    """
    issues = []

    # Check status
    if data.get('status') != 'healthy':
        issues.append(f"Status is '{data.get('status')}', expected 'healthy'")

    # Check environment
    if data.get('environment') != 'production':
        issues.append(f"Environment is '{data.get('environment')}', should be 'production'")

    # Check security settings
    security = data.get('security', {})

    if not security.get('authentication_required'):
        issues.append("⚠️  Authentication is not required (CRITICAL)")

    if not security.get('https_enforced'):
        issues.append("⚠️  HTTPS is not enforced (CRITICAL)")

    if not security.get('rate_limiting_enabled'):
        issues.append("⚠️  Rate limiting is not enabled")

    if not security.get('pii_masking_enabled'):
        issues.append("⚠️  PII masking is not enabled")

    # Check services
    services = data.get('services', {})
    for service, status in services.items():
        if 'error' in str(status).lower():
            issues.append(f"Service '{service}' has error: {status}")

    return issues


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test health check endpoint and validate production configuration"
    )
    parser.add_argument(
        '--url',
        default='http://localhost:8000',
        help='Base URL of the API (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--api-key',
        help='API key for authentication (if required)'
    )

    args = parser.parse_args()

    print(f"{Colors.BOLD}=" * 60)
    print("🏥 Production Health Check Validator")
    print("=" * 60 + Colors.ENDC)
    print()

    base_url = args.url.rstrip('/')

    # Test 1: Root endpoint
    print(f"{Colors.BOLD}Test 1: Root Endpoint{Colors.ENDC}")
    print(f"URL: {base_url}/")
    success, data, error = check_endpoint(f"{base_url}/", args.api_key)

    if success:
        print(f"{Colors.GREEN}✅ Root endpoint accessible{Colors.ENDC}")
        print(f"   Status: {data.get('status')}")
        print(f"   Message: {data.get('message')}")
    else:
        print(f"{Colors.RED}❌ Root endpoint failed: {error}{Colors.ENDC}")
    print()

    # Test 2: Health endpoint
    print(f"{Colors.BOLD}Test 2: Health Check Endpoint{Colors.ENDC}")
    print(f"URL: {base_url}/health")
    success, data, error = check_endpoint(f"{base_url}/health", args.api_key)

    if success:
        print(f"{Colors.GREEN}✅ Health endpoint accessible{Colors.ENDC}")
        print()
        print(f"{Colors.BOLD}Health Status:{Colors.ENDC}")
        print(f"   Overall: {data.get('status')}")
        print(f"   Environment: {data.get('environment')}")
        print(f"   Version: {data.get('version')}")
        print()

        print(f"{Colors.BOLD}Services:{Colors.ENDC}")
        for service, status in data.get('services', {}).items():
            color = Colors.GREEN if 'operational' in str(status).lower() else Colors.RED
            print(f"   {service}: {color}{status}{Colors.ENDC}")
        print()

        print(f"{Colors.BOLD}Security Configuration:{Colors.ENDC}")
        security = data.get('security', {})
        for setting, value in security.items():
            color = Colors.GREEN if value else Colors.YELLOW
            print(f"   {setting}: {color}{value}{Colors.ENDC}")
        print()

        print(f"{Colors.BOLD}Metrics:{Colors.ENDC}")
        metrics = data.get('metrics', {})
        print(f"   Active sessions: {metrics.get('active_sessions', 'N/A')}")
        cache_stats = metrics.get('cache_stats', {})
        print(f"   Cache hit rate: {cache_stats.get('hit_rate', 'N/A')}")
        print()

        # Validate response
        issues = validate_health_response(data)

        if issues:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Validation Issues Found:{Colors.ENDC}")
            for issue in issues:
                print(f"   • {issue}")
            print()
        else:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ All validation checks passed!{Colors.ENDC}")
            print()

    else:
        print(f"{Colors.RED}❌ Health endpoint failed: {error}{Colors.ENDC}")
        print()

    # Test 3: HTTPS check
    if args.url.startswith('https://'):
        print(f"{Colors.GREEN}✅ Using HTTPS{Colors.ENDC}")
    else:
        print(f"{Colors.YELLOW}⚠️  Not using HTTPS - recommended for production{Colors.ENDC}")
    print()

    # Test 4: Authentication check
    print(f"{Colors.BOLD}Test 3: Authentication Check{Colors.ENDC}")
    print(f"URL: {base_url}/api/v1/chat")

    # Try without API key
    success, data, error = check_endpoint(f"{base_url}/api/v1/chat")

    if not success and '401' in error:
        print(f"{Colors.GREEN}✅ Authentication is required (endpoint rejected unauthenticated request){Colors.ENDC}")
    elif not success:
        print(f"{Colors.YELLOW}⚠️  Endpoint rejected request: {error}{Colors.ENDC}")
    else:
        print(f"{Colors.RED}❌ CRITICAL: Authentication not enforced!{Colors.ENDC}")
    print()

    # Summary
    print(f"{Colors.BOLD}=" * 60)
    print("📊 Summary")
    print("=" * 60 + Colors.ENDC)

    if success and not issues:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ All checks passed! Application is production-ready.{Colors.ENDC}")
        sys.exit(0)
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Some issues found. Review and fix before production deployment.{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
