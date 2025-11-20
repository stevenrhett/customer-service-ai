# Production Scripts

Automated scripts to help you deploy and maintain a production-ready application.

## 📋 Quick Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `setup_production.py` | Generate secure production config | `python scripts/setup_production.py` |
| `preflight_check.sh` | Pre-deployment validation | `bash scripts/preflight_check.sh` |
| `test_health_check.py` | Test health endpoints | `python scripts/test_health_check.py --url https://yourdomain.com` |
| `run_security_scan.py` | Security vulnerability scan | `python scripts/run_security_scan.py` |

---

## 1. setup_production.py

**Generates production environment configuration with secure credentials.**

### Usage

```bash
# Create .env.production with secure credentials
python scripts/setup_production.py

# Specify custom output file
python scripts/setup_production.py --output .env.staging
```

### What it does

- ✅ Generates cryptographically secure API keys (44 chars each)
- ✅ Generates JWT secret key (88 chars)
- ✅ Generates encryption key for data at rest
- ✅ Creates `.env.production` with all required settings
- ✅ Sets secure file permissions (0o600)
- ✅ Provides production checklist

### Output

```
🔐 Generating secure production credentials...

✅ Generated credentials:
   - API Key 1: XYZ... (44 characters)
   - API Key 2: ABC... (44 characters)
   - JWT Secret: DEF... (88 characters)
   - Encryption Key: GHI... (44 characters)

✅ Production environment file created: .env.production
   Permissions set to 0o600 (owner read/write only)

📋 CRITICAL NEXT STEPS:
   1. Edit the file and update domain-specific settings
   2. Configure SSL/TLS certificates for HTTPS
   3. Set up AWS IAM role (preferred over access keys)
   4. NEVER commit this file to git!
```

### Important Notes

- **Store credentials securely** - Share only with authorized personnel
- **Never commit to git** - Add to .gitignore
- **Update domain settings** - Replace placeholder domains with actual ones
- **Rotate regularly** - Change credentials monthly in production

---

## 2. preflight_check.sh

**Comprehensive pre-deployment validation checklist.**

### Usage

```bash
# Run all pre-flight checks
bash scripts/preflight_check.sh

# Check specific environment file
ENV_FILE=.env.staging bash scripts/preflight_check.sh
```

### What it checks

#### ✅ Environment Configuration
- `.env.production` exists
- `ENVIRONMENT=production`
- `REQUIRE_AUTHENTICATION=true`
- `ENFORCE_HTTPS=true`
- API keys not using default values
- JWT secret is secure (32+ characters)
- CORS properly configured (no wildcards)

#### ✅ Security Scans
- Bandit (Python security linter) installed
- Safety (dependency vulnerabilities) installed
- Security scan executed

#### ✅ SSL/TLS Configuration
- SSL certificate directories exist
- Certificates properly configured

#### ✅ Docker Configuration
- Docker installed
- Docker Compose available

#### ✅ Dependencies
- Backend requirements.txt exists
- No known vulnerabilities in dependencies
- Frontend package.json exists
- package-lock.json present

#### ✅ Git Configuration
- .env files in .gitignore
- No .env files tracked by git

#### ✅ File Permissions
- .env files have secure permissions (600)

### Exit Codes

- `0` - All checks passed ✅
- `0` - Warnings only (safe to deploy with caution) ⚠️
- `1` - Errors found (DO NOT deploy) ❌

### Example Output

```
✅ All checks passed! Ready for production deployment.

Next steps:
  1. Review and update domain-specific settings in .env.production
  2. Configure SSL/TLS certificates
  3. Deploy using Docker Compose or your preferred method
  4. Run health check: curl https://yourdomain.com/health
  5. Set up monitoring and alerts
```

---

## 3. test_health_check.py

**Validates health endpoints and production configuration.**

### Usage

```bash
# Test local deployment
python scripts/test_health_check.py

# Test production deployment
python scripts/test_health_check.py --url https://yourdomain.com

# Test with authentication
python scripts/test_health_check.py --url https://yourdomain.com --api-key YOUR_API_KEY
```

### What it tests

#### Test 1: Root Endpoint
- ✅ Endpoint accessible
- ✅ Returns valid status

#### Test 2: Health Check Endpoint
- ✅ Comprehensive health data
- ✅ All services operational
- ✅ Security settings correct
- ✅ Cache metrics available

#### Test 3: HTTPS Check
- ✅ Using HTTPS (not HTTP)

#### Test 4: Authentication Check
- ✅ Authentication enforced
- ✅ Rejects unauthenticated requests

### Validation

Checks these production requirements:
- Status is "healthy"
- Environment is "production"
- Authentication required
- HTTPS enforced
- Rate limiting enabled
- PII masking enabled
- All services operational

### Example Output

```
🏥 Production Health Check Validator

Test 1: Root Endpoint
✅ Root endpoint accessible
   Status: online
   Message: Customer Service AI API is running

Test 2: Health Check Endpoint
✅ Health endpoint accessible

Health Status:
   Overall: healthy
   Environment: production
   Version: 1.0.0

Services:
   api: operational
   vector_db: operational
   cache: operational

Security Configuration:
   authentication_required: true
   https_enforced: true
   rate_limiting_enabled: true
   pii_masking_enabled: true

✅ All validation checks passed!

✅ All checks passed! Application is production-ready.
```

---

## 4. run_security_scan.py

**Runs comprehensive security vulnerability scans.**

### Usage

```bash
# Install security tools first
pip install bandit safety

# Run security scan
python scripts/run_security_scan.py
```

### What it scans

#### Scan 1: Python Security Analysis (Bandit)
- SQL injection vulnerabilities
- Command injection risks
- Hard-coded passwords
- Insecure function usage
- Security misconfigurations

#### Scan 2: Dependency Vulnerabilities (Safety)
- Known CVEs in dependencies
- Outdated packages with security issues
- Vulnerability severity ratings

#### Scan 3: Secret Detection
- API keys in git history
- AWS access keys
- Hardcoded passwords
- Tokens and secrets

#### Scan 4: File Permissions
- .env files have secure permissions (600)
- No world-readable sensitive files

#### Scan 5: Configuration Security
- No .env files tracked in git
- No default/example secrets in production config

### Exit Codes

- `0` - All scans passed ✅
- `1` - Security issues found ❌

### Example Output

```
🔒 Security Scan Runner

✅ All security tools installed

Scan 1: Python Security Analysis (Bandit)
✅ Bandit scan passed - no high/medium severity issues

Scan 2: Dependency Vulnerability Check (Safety)
✅ Safety scan passed - no known vulnerabilities

Scan 3: Secret Detection
✅ No obvious secrets found in git history

Scan 4: File Permissions Check
✅ File permissions are secure

Scan 5: Configuration Security Check
✅ Configuration security checks passed

📊 Security Scan Summary
✅ All security scans passed!

Your application meets basic security requirements.
Additional recommendations:
  • Run penetration testing before production
  • Set up continuous security monitoring
  • Enable automated dependency updates
  • Review audit logs regularly
```

---

## 🚀 Production Deployment Workflow

Follow this workflow for production deployment:

```bash
# Step 1: Generate production configuration
python scripts/setup_production.py

# Step 2: Update domain settings in .env.production
nano .env.production

# Step 3: Run pre-flight checks
bash scripts/preflight_check.sh

# Step 4: Deploy application
docker-compose up -d

# Step 5: Test deployment
python scripts/test_health_check.py --url https://yourdomain.com

# Step 6: Run security scans
python scripts/run_security_scan.py

# Step 7: Monitor logs
docker-compose logs -f backend
```

---

## 🔄 Regular Maintenance

### Daily

```bash
# Check application health
python scripts/test_health_check.py --url https://yourdomain.com

# Review logs for errors
docker-compose logs --tail=100 backend | grep ERROR
```

### Weekly

```bash
# Run security scan
python scripts/run_security_scan.py

# Check for dependency updates
cd backend && pip list --outdated
```

### Monthly

```bash
# Rotate credentials
python scripts/setup_production.py --output .env.new
# Review and replace credentials in .env.production

# Full security audit
bash scripts/preflight_check.sh
python scripts/run_security_scan.py
```

---

## ❓ Troubleshooting

### "Permission denied" when running scripts

```bash
# Make scripts executable
chmod +x scripts/*.py scripts/*.sh
```

### "Module not found" errors

```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Install security tools
pip install bandit safety
```

### Pre-flight check fails

1. Review error messages
2. Fix identified issues
3. Run again until all checks pass

### Health check fails

1. Check logs: `docker-compose logs backend`
2. Verify environment variables
3. Check network/firewall settings
4. Ensure certificates are valid

---

## 📚 Additional Resources

- **Full Deployment Guide**: [PRODUCTION_DEPLOYMENT.md](../PRODUCTION_DEPLOYMENT.md)
- **Quick Start**: [PRODUCTION_QUICKSTART.md](../PRODUCTION_QUICKSTART.md)
- **Security Policy**: [SECURITY.md](../SECURITY.md)

---

## 🆘 Support

For issues or questions:
1. Check script output for specific error messages
2. Review documentation in this directory
3. Check application logs
4. Consult PRODUCTION_DEPLOYMENT.md

---

**Last Updated**: 2025-11-20
