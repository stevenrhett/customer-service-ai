# Production Quick Start Guide

**Complete this checklist to get production-ready in 30 minutes.**

---

## ✅ Step 1: Generate Production Configuration (5 minutes)

Generate secure credentials and create production environment file:

```bash
# Run the setup script
python scripts/setup_production.py

# This will create .env.production with secure random credentials
```

**What this does:**
- ✅ Generates secure API keys (44 characters)
- ✅ Generates JWT secret (88 characters)
- ✅ Generates encryption key
- ✅ Sets all security settings to production defaults
- ✅ Sets file permissions to 0o600 (secure)

**Output:** `.env.production` file with all security settings configured

---

## ✅ Step 2: Update Domain Settings (2 minutes)

Edit `.env.production` and update these settings with your actual domains:

```bash
# Open the file
nano .env.production

# Update these lines:
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
FRONTEND_URL=https://yourdomain.com
```

**Critical:** Remove any `localhost` references and wildcards (`*`)

---

## ✅ Step 3: Configure HTTPS/SSL (5 minutes)

### Option A: AWS Certificate Manager (Recommended for AWS)

```bash
# 1. Request certificate in ACM
aws acm request-certificate \
  --domain-name yourdomain.com \
  --subject-alternative-names www.yourdomain.com \
  --validation-method DNS

# 2. Add DNS validation records
# 3. Attach certificate to load balancer
```

### Option B: Let's Encrypt (For other platforms)

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certificates will be in /etc/letsencrypt/live/yourdomain.com/
```

---

## ✅ Step 4: Set Up AWS IAM Role (3 minutes)

**Best Practice:** Use IAM roles instead of access keys

```bash
# 1. Create IAM role with Bedrock permissions
aws iam create-role \
  --role-name CustomerServiceAIRole \
  --assume-role-policy-document file://trust-policy.json

# 2. Attach Bedrock policy
aws iam attach-role-policy \
  --role-name CustomerServiceAIRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

# 3. Attach role to EC2/ECS/Lambda
```

**Then remove from `.env.production`:**
```bash
# Comment out or remove these lines:
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
```

---

## ✅ Step 5: Run Pre-Flight Checks (3 minutes)

Run the automated pre-flight checklist:

```bash
# This checks all security settings, dependencies, and configuration
bash scripts/preflight_check.sh
```

**Expected output:**
```
✅ All checks passed! Ready for production deployment.
```

**If you see errors:** Fix them before continuing. The script will tell you exactly what to fix.

---

## ✅ Step 6: Deploy Application (5 minutes)

### Docker Deployment (Recommended)

```bash
# Copy production env file
cp .env.production backend/.env

# Build and start services
docker-compose up -d

# Check logs
docker-compose logs -f backend
```

### Manual Deployment

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Start application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## ✅ Step 7: Verify Deployment (3 minutes)

Test the health endpoint:

```bash
# Test health check
python scripts/test_health_check.py --url https://yourdomain.com

# Or use curl
curl https://yourdomain.com/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "environment": "production",
  "security": {
    "authentication_required": true,
    "https_enforced": true,
    "rate_limiting_enabled": true,
    "pii_masking_enabled": true
  }
}
```

---

## ✅ Step 8: Test Authentication (2 minutes)

Verify authentication is working:

```bash
# This should FAIL (no API key)
curl https://yourdomain.com/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "session_id": "test"}'

# Expected: 401 Unauthorized

# This should SUCCEED (with API key)
curl https://yourdomain.com/api/v1/chat \
  -H "X-API-Key: YOUR-API-KEY-HERE" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test123"}'

# Expected: 200 OK with response
```

---

## ✅ Step 9: Run Security Scans (2 minutes)

```bash
# Install security tools
pip install bandit safety

# Run comprehensive security scan
python scripts/run_security_scan.py
```

**Expected output:**
```
✅ All security scans passed!
```

---

## ✅ Step 10: Set Up Monitoring (5 minutes)

### CloudWatch (AWS)

```bash
# Create log group
aws logs create-log-group --log-group-name /customer-service-ai/production

# Create metric alarm for errors
aws cloudwatch put-metric-alarm \
  --alarm-name customer-service-ai-errors \
  --alarm-description "Alert on application errors" \
  --metric-name Errors \
  --namespace AWS/Logs \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

### Health Check Monitoring

Set up automated health checks (every 30 seconds):

```bash
# Add to crontab or monitoring service
*/1 * * * * curl -f https://yourdomain.com/health || echo "Health check failed"
```

---

## 🎉 Production Checklist Complete!

Your application is now production-ready with:

- ✅ **Authentication** enabled
- ✅ **HTTPS** enforced
- ✅ **Secure credentials** generated
- ✅ **Security headers** configured
- ✅ **PII masking** enabled
- ✅ **Rate limiting** active
- ✅ **Audit logging** running
- ✅ **Health checks** configured
- ✅ **Monitoring** set up

---

## 📊 Daily Operations

### Check Application Status

```bash
# Health check
curl https://yourdomain.com/health | jq

# Check logs
docker-compose logs --tail=100 backend

# Check metrics
curl https://yourdomain.com/health | jq '.metrics'
```

### Rotate API Keys (Monthly)

```bash
# Generate new keys
python scripts/setup_production.py --output .env.new

# Update .env.production with new keys
# Restart application
docker-compose restart backend

# Share new keys with authorized clients
```

### Review Security (Weekly)

```bash
# Run security scan
python scripts/run_security_scan.py

# Check for dependency updates
cd backend && pip list --outdated

# Review audit logs
docker-compose logs backend | grep "audit"
```

---

## 🚨 Troubleshooting

### Issue: Health check fails

```bash
# Check logs
docker-compose logs backend

# Check environment variables
docker-compose exec backend env | grep -E "ENVIRONMENT|AUTHENTICATION"

# Verify production validation
docker-compose logs backend | grep "validation"
```

### Issue: Authentication not working

```bash
# Verify API key is set
grep API_KEYS .env.production

# Test with correct header
curl -H "X-API-Key: your-key" https://yourdomain.com/api/v1/chat
```

### Issue: HTTPS redirect not working

```bash
# Check ENFORCE_HTTPS setting
grep ENFORCE_HTTPS .env.production

# Should be: ENFORCE_HTTPS=true

# Restart application
docker-compose restart backend
```

---

## 📚 Additional Resources

- **Full deployment guide:** [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
- **Security policy:** [SECURITY.md](SECURITY.md)
- **Environment reference:** [backend/.env.example](backend/.env.example)

---

## 🆘 Need Help?

1. Check logs: `docker-compose logs backend`
2. Run health check: `python scripts/test_health_check.py`
3. Review troubleshooting section above
4. Check documentation in PRODUCTION_DEPLOYMENT.md

---

**Total Time:** ~30 minutes
**Result:** Production-ready, secure application! 🎉
