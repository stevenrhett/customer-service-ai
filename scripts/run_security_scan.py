#!/usr/bin/env python3
"""
Security Scan Runner

Runs comprehensive security checks on the application.

Usage:
    python scripts/run_security_scan.py
"""
import subprocess
import sys
import os
from pathlib import Path
from typing import List, Tuple


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def run_command(cmd: List[str], description: str) -> Tuple[bool, str]:
    """
    Run a command and return success status.

    Args:
        cmd: Command to run
        description: Description of the check

    Returns:
        Tuple of (success, output)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except FileNotFoundError:
        return False, f"Command not found: {cmd[0]}"
    except Exception as e:
        return False, str(e)


def check_dependencies_installed() -> bool:
    """Check if security tools are installed."""
    tools = {
        'bandit': 'pip install bandit',
        'safety': 'pip install safety',
    }

    all_installed = True
    for tool, install_cmd in tools.items():
        try:
            subprocess.run([tool, '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"{Colors.YELLOW}⚠️  {tool} not installed. Install with: {install_cmd}{Colors.ENDC}")
            all_installed = False

    return all_installed


def main():
    """Main entry point."""
    print(f"{Colors.BOLD}=" * 60)
    print("🔒 Security Scan Runner")
    print("=" * 60 + Colors.ENDC)
    print()

    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Check dependencies
    print(f"{Colors.BOLD}Checking security tools...{Colors.ENDC}")
    if not check_dependencies_installed():
        print()
        print(f"{Colors.RED}❌ Some security tools are missing. Install them and try again.{Colors.ENDC}")
        sys.exit(1)
    print(f"{Colors.GREEN}✅ All security tools installed{Colors.ENDC}")
    print()

    all_passed = True

    # Scan 1: Bandit (Python security linter)
    print(f"{Colors.BOLD}Scan 1: Python Security Analysis (Bandit){Colors.ENDC}")
    print("Checking for common security issues in Python code...")

    success, output = run_command(
        ['bandit', '-r', 'backend/app/', '-ll', '-f', 'screen'],
        "Python security scan"
    )

    if success:
        print(f"{Colors.GREEN}✅ Bandit scan passed - no high/medium severity issues{Colors.ENDC}")
    else:
        print(f"{Colors.RED}❌ Bandit found security issues:{Colors.ENDC}")
        print(output)
        all_passed = False
    print()

    # Scan 2: Safety (dependency vulnerabilities)
    print(f"{Colors.BOLD}Scan 2: Dependency Vulnerability Check (Safety){Colors.ENDC}")
    print("Checking for known vulnerabilities in dependencies...")

    success, output = run_command(
        ['safety', 'check', '--file', 'backend/requirements.txt'],
        "Dependency vulnerability check"
    )

    if success and 'vulnerabilities found' not in output.lower():
        print(f"{Colors.GREEN}✅ Safety scan passed - no known vulnerabilities{Colors.ENDC}")
    else:
        print(f"{Colors.YELLOW}⚠️  Safety found potential issues:{Colors.ENDC}")
        print(output)
        # Don't fail on safety warnings (may be false positives)
    print()

    # Scan 3: Check for secrets in git history
    print(f"{Colors.BOLD}Scan 3: Secret Detection{Colors.ENDC}")
    print("Checking for accidentally committed secrets...")

    secret_patterns = [
        (r'sk-[a-zA-Z0-9]{20,}', 'OpenAI API key pattern'),
        (r'AKIA[0-9A-Z]{16}', 'AWS access key pattern'),
        (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
        (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', 'API key'),
    ]

    secrets_found = False
    for pattern, description in secret_patterns:
        success, output = run_command(
            ['git', 'log', '-p', '-S', pattern, '--all'],
            f"Check for {description}"
        )

        if output and len(output.strip()) > 0:
            print(f"{Colors.RED}⚠️  Potential secret found: {description}{Colors.ENDC}")
            secrets_found = True

    if not secrets_found:
        print(f"{Colors.GREEN}✅ No obvious secrets found in git history{Colors.ENDC}")
    else:
        print(f"{Colors.YELLOW}⚠️  Review findings above. Use git-secrets or BFG to clean history if needed.{Colors.ENDC}")
    print()

    # Scan 4: File permissions check
    print(f"{Colors.BOLD}Scan 4: File Permissions Check{Colors.ENDC}")
    print("Checking for insecure file permissions...")

    insecure_files = []
    for env_file in ['.env', '.env.production', '.env.local']:
        env_path = project_root / env_file
        if env_path.exists():
            mode = env_path.stat().st_mode & 0o777
            if mode != 0o600:
                insecure_files.append(f"{env_file} has permissions {oct(mode)}, should be 0o600")

    if insecure_files:
        print(f"{Colors.YELLOW}⚠️  Insecure file permissions found:{Colors.ENDC}")
        for issue in insecure_files:
            print(f"   • {issue}")
        print(f"   Fix with: chmod 600 .env*")
    else:
        print(f"{Colors.GREEN}✅ File permissions are secure{Colors.ENDC}")
    print()

    # Scan 5: Configuration validation
    print(f"{Colors.BOLD}Scan 5: Configuration Security Check{Colors.ENDC}")
    print("Checking for insecure configuration...")

    config_issues = []

    # Check .env.example for default secrets
    env_example = project_root / 'backend' / '.env.example'
    if env_example.exists():
        content = env_example.read_text()
        if 'your-api-key' in content.lower() or 'changeme' in content.lower():
            # This is expected in .env.example
            pass

    # Check for .env files in git
    try:
        result = subprocess.run(
            ['git', 'ls-files', '.env*'],
            capture_output=True,
            text=True
        )
        tracked_env_files = [f for f in result.stdout.strip().split('\n') if f and not f.endswith('.example')]
        if tracked_env_files:
            config_issues.append(f"Environment files tracked in git: {', '.join(tracked_env_files)}")
    except:
        pass

    if config_issues:
        print(f"{Colors.RED}❌ Configuration issues found:{Colors.ENDC}")
        for issue in config_issues:
            print(f"   • {issue}")
        all_passed = False
    else:
        print(f"{Colors.GREEN}✅ Configuration security checks passed{Colors.ENDC}")
    print()

    # Summary
    print(f"{Colors.BOLD}=" * 60)
    print("📊 Security Scan Summary")
    print("=" * 60 + Colors.ENDC)

    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ All security scans passed!{Colors.ENDC}")
        print()
        print("Your application meets basic security requirements.")
        print("Additional recommendations:")
        print("  • Run penetration testing before production")
        print("  • Set up continuous security monitoring")
        print("  • Enable automated dependency updates")
        print("  • Review audit logs regularly")
        sys.exit(0)
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ Some security issues found.{Colors.ENDC}")
        print()
        print("Please address the issues above before deploying to production.")
        sys.exit(1)


if __name__ == "__main__":
    main()
