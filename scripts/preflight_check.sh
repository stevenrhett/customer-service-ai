#!/bin/bash
# Production Pre-Flight Checklist
#
# Run this script before deploying to production to ensure everything is configured correctly.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}============================================================${NC}"
echo -e "${BOLD}🚀 Production Pre-Flight Checklist${NC}"
echo -e "${BOLD}============================================================${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Function to print success
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error
error() {
    echo -e "${RED}❌ $1${NC}"
    ((ERRORS++))
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

# Function to print info
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo -e "${BOLD}Step 1: Environment Configuration${NC}"
echo "----------------------------------------"

# Check for .env.production file
if [ -f "$PROJECT_ROOT/.env.production" ]; then
    success ".env.production file exists"

    # Check critical environment variables
    source "$PROJECT_ROOT/.env.production"

    if [ "$ENVIRONMENT" = "production" ]; then
        success "ENVIRONMENT set to production"
    else
        error "ENVIRONMENT is '$ENVIRONMENT', should be 'production'"
    fi

    if [ "$REQUIRE_AUTHENTICATION" = "true" ]; then
        success "Authentication is enabled"
    else
        error "REQUIRE_AUTHENTICATION must be 'true' for production"
    fi

    if [ "$ENFORCE_HTTPS" = "true" ]; then
        success "HTTPS enforcement is enabled"
    else
        error "ENFORCE_HTTPS must be 'true' for production"
    fi

    if [ "$MASK_PII_IN_LOGS" = "true" ]; then
        success "PII masking in logs is enabled"
    else
        warning "PII masking should be enabled for production"
    fi

    # Check for default/example credentials
    if echo "$API_KEYS" | grep -q "your-api-key"; then
        error "API_KEYS contains default values - generate secure keys!"
    elif [ -n "$API_KEYS" ]; then
        success "API_KEYS are configured (not default values)"
    else
        error "API_KEYS not set"
    fi

    if echo "$JWT_SECRET_KEY" | grep -q "your-jwt-secret"; then
        error "JWT_SECRET_KEY contains default value - generate secure secret!"
    elif [ -n "$JWT_SECRET_KEY" ] && [ ${#JWT_SECRET_KEY} -ge 32 ]; then
        success "JWT_SECRET_KEY is configured and sufficient length"
    else
        error "JWT_SECRET_KEY not set or too short (minimum 32 characters)"
    fi

    # Check CORS configuration
    if echo "$CORS_ORIGINS" | grep -q "\*"; then
        error "CORS_ORIGINS contains wildcard (*) - specify exact domains!"
    elif echo "$CORS_ORIGINS" | grep -q "localhost"; then
        warning "CORS_ORIGINS contains localhost - should be removed for production"
    elif [ -n "$CORS_ORIGINS" ]; then
        success "CORS_ORIGINS properly configured"
    else
        error "CORS_ORIGINS not set"
    fi

else
    error ".env.production file not found"
    info "Run: python scripts/setup_production.py to create it"
fi
echo ""

echo -e "${BOLD}Step 2: Security Scans${NC}"
echo "----------------------------------------"

# Check if security tools are installed
if command -v bandit &> /dev/null; then
    success "Bandit is installed"
else
    warning "Bandit not installed (pip install bandit)"
fi

if command -v safety &> /dev/null; then
    success "Safety is installed"
else
    warning "Safety not installed (pip install safety)"
fi

# Run security scan if tools are available
if command -v python3 &> /dev/null && [ -f "$SCRIPT_DIR/run_security_scan.py" ]; then
    info "Running security scan..."
    if python3 "$SCRIPT_DIR/run_security_scan.py"; then
        success "Security scan passed"
    else
        error "Security scan found issues"
    fi
else
    warning "Security scan script not found or Python not installed"
fi
echo ""

echo -e "${BOLD}Step 3: SSL/TLS Configuration${NC}"
echo "----------------------------------------"

# Check if SSL certificates exist (common locations)
SSL_DIRS=(
    "/etc/letsencrypt/live"
    "/etc/ssl/certs"
    "/etc/pki/tls/certs"
)

SSL_FOUND=false
for dir in "${SSL_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        info "SSL directory found: $dir"
        SSL_FOUND=true
    fi
done

if [ "$SSL_FOUND" = false ]; then
    warning "No SSL certificates found in common locations"
    info "Make sure to configure SSL/TLS certificates before deployment"
fi
echo ""

echo -e "${BOLD}Step 4: Docker Configuration${NC}"
echo "----------------------------------------"

if command -v docker &> /dev/null; then
    success "Docker is installed"

    # Check if docker-compose exists
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        success "Docker Compose is available"
    else
        warning "Docker Compose not found"
    fi
else
    warning "Docker not installed - required for containerized deployment"
fi
echo ""

echo -e "${BOLD}Step 5: Dependencies${NC}"
echo "----------------------------------------"

# Check backend dependencies
if [ -f "$PROJECT_ROOT/backend/requirements.txt" ]; then
    success "Backend requirements.txt found"

    # Check for any packages with known vulnerabilities
    if command -v safety &> /dev/null; then
        cd "$PROJECT_ROOT/backend"
        if safety check --file requirements.txt --json > /dev/null 2>&1; then
            success "No known vulnerabilities in dependencies"
        else
            warning "Some dependencies may have known vulnerabilities"
        fi
        cd "$PROJECT_ROOT"
    fi
else
    error "Backend requirements.txt not found"
fi

# Check frontend dependencies
if [ -f "$PROJECT_ROOT/frontend/package.json" ]; then
    success "Frontend package.json found"

    if [ -f "$PROJECT_ROOT/frontend/package-lock.json" ]; then
        success "Frontend package-lock.json found (dependencies locked)"
    else
        warning "Frontend package-lock.json not found - run 'npm install' to generate"
    fi
else
    error "Frontend package.json not found"
fi
echo ""

echo -e "${BOLD}Step 6: Git Configuration${NC}"
echo "----------------------------------------"

# Check if .env files are in .gitignore
if [ -f "$PROJECT_ROOT/.gitignore" ]; then
    if grep -q ".env" "$PROJECT_ROOT/.gitignore"; then
        success ".env files are in .gitignore"
    else
        error ".env files not in .gitignore - secrets could be committed!"
    fi
else
    warning ".gitignore file not found"
fi

# Check if any .env files are tracked by git
cd "$PROJECT_ROOT"
TRACKED_ENV=$(git ls-files | grep -E "^\.env($|\.)" | grep -v ".env.example" || true)
if [ -z "$TRACKED_ENV" ]; then
    success "No sensitive .env files tracked in git"
else
    error "Environment files tracked in git: $TRACKED_ENV"
    info "Remove with: git rm --cached $TRACKED_ENV"
fi
echo ""

echo -e "${BOLD}Step 7: File Permissions${NC}"
echo "----------------------------------------"

# Check permissions on .env files
for env_file in .env .env.production .env.local; do
    if [ -f "$PROJECT_ROOT/$env_file" ]; then
        PERMS=$(stat -c "%a" "$PROJECT_ROOT/$env_file" 2>/dev/null || stat -f "%Lp" "$PROJECT_ROOT/$env_file" 2>/dev/null)
        if [ "$PERMS" = "600" ]; then
            success "$env_file has secure permissions (600)"
        else
            warning "$env_file has permissions $PERMS, should be 600"
            info "Fix with: chmod 600 $PROJECT_ROOT/$env_file"
        fi
    fi
done
echo ""

echo -e "${BOLD}============================================================${NC}"
echo -e "${BOLD}📊 Pre-Flight Summary${NC}"
echo -e "${BOLD}============================================================${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ All checks passed! Ready for production deployment.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review and update domain-specific settings in .env.production"
    echo "  2. Configure SSL/TLS certificates"
    echo "  3. Deploy using Docker Compose or your preferred method"
    echo "  4. Run health check: curl https://yourdomain.com/health"
    echo "  5. Set up monitoring and alerts"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}${BOLD}⚠️  $WARNINGS warnings found.${NC}"
    echo ""
    echo "Review the warnings above. You may proceed with caution."
    echo ""
    exit 0
else
    echo -e "${RED}${BOLD}❌ $ERRORS errors found!${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}   $WARNINGS warnings found.${NC}"
    fi
    echo ""
    echo "❌ DO NOT deploy to production until all errors are fixed!"
    echo ""
    echo "Common fixes:"
    echo "  • Generate production config: python scripts/setup_production.py"
    echo "  • Update domain settings in .env.production"
    echo "  • Ensure all security settings are enabled"
    echo "  • Remove any tracked .env files from git"
    echo ""
    exit 1
fi
