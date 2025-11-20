# Production Deployment Guide

This guide covers deploying the Customer Service AI system to production with proper security configurations.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Security Configuration](#security-configuration)
3. [Environment Setup](#environment-setup)
4. [Deployment Steps](#deployment-steps)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Incident Response](#incident-response)

---

## Pre-Deployment Checklist

### Critical Security Requirements

Before deploying to production, verify ALL of these requirements:

- [ ] **Authentication enabled** (`REQUIRE_AUTHENTICATION=true`)
- [ ] **HTTPS enforced** (`ENFORCE_HTTPS=true`)
- [ ] **Secure API keys generated** (not default values)
- [ ] **JWT secret key set** (32+ characters, random)
- [ ] **CORS origins restricted** (no wildcards, HTTPS only)
- [ ] **PII masking enabled** (`MASK_PII_IN_LOGS=true`)
- [ ] **Rate limiting enabled** with appropriate limits
- [ ] **Log level set to INFO or WARNING** (not DEBUG)
- [ ] **All secrets excluded from git** (.env in .gitignore)
- [ ] **AWS IAM roles configured** (not hardcoded credentials)
- [ ] **Dependencies updated** to latest secure versions

### Infrastructure Requirements

- [ ] SSL/TLS certificates obtained and configured
- [ ] Load balancer with health checks configured
- [ ] Database backups enabled (if using persistent storage)
- [ ] Monitoring and alerting configured
- [ ] Log aggregation system configured
- [ ] WAF (Web Application Firewall) configured (recommended)

---

## Security Configuration

### 1. Generate Secure Credentials

#### API Keys
```bash
# Generate secure API keys
python3 -c "import secrets; print('API_KEY_1:', secrets.token_urlsafe(32))"
python3 -c "import secrets; print('API_KEY_2:', secrets.token_urlsafe(32))"
```

#### JWT Secret
```bash
# Generate JWT secret key (64 characters recommended)
python3 -c "import secrets; print('JWT_SECRET_KEY:', secrets.token_urlsafe(64))"
```

#### Encryption Key
```bash
# Generate encryption key for data at rest
python3 -c "import secrets; print('ENCRYPTION_KEY:', secrets.token_urlsafe(32))"
```

### 2. AWS Configuration

#### Option A: IAM Roles (Recommended)
```bash
# Use IAM roles for EC2/ECS/Lambda
# No AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY needed
# Configure role with permissions for:
# - Bedrock API access
# - Secrets Manager (if enabled)
# - CloudWatch Logs
```

#### Option B: Temporary Credentials
```bash
# Use AWS SSO or STS for temporary credentials
AWS_SESSION_TOKEN=<temporary-token>
AWS_ACCESS_KEY_ID=<temporary-access-key>
AWS_SECRET_ACCESS_KEY=<temporary-secret-key>
```

#### Option C: Secrets Manager
```bash
# Enable AWS Secrets Manager for credential rotation
ENABLE_SECRETS_MANAGER=true
SECRETS_MANAGER_REGION=us-west-2
SECRETS_MANAGER_SECRET_NAME=customer-service-ai-prod-secrets
```

### 3. HTTPS/TLS Configuration

#### SSL Certificate Setup
```bash
# For AWS (using ACM)
# 1. Request certificate in AWS Certificate Manager
# 2. Validate domain ownership
# 3. Attach to load balancer

# For Let's Encrypt
sudo certbot certonly --standalone -d yourdomain.com
```

#### Environment Configuration
```bash
ENFORCE_HTTPS=true
CORS_ORIGINS=https://yourdomain.com
FRONTEND_URL=https://yourdomain.com
```

---

## Environment Setup

### Production Environment Variables

Create a `.env` file (NEVER commit this to git):

```bash
# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO

# AWS Configuration (use IAM roles in production)
AWS_REGION=us-west-2
# AWS_ACCESS_KEY_ID - Use IAM roles instead
# AWS_SECRET_ACCESS_KEY - Use IAM roles instead

# OpenAI (if using)
OPENAI_API_KEY=sk-your-actual-openai-key

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Security - Authentication
REQUIRE_AUTHENTICATION=true
API_KEYS=<generated-key-1>,<generated-key-2>
JWT_SECRET_KEY=<generated-jwt-secret>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Security - HTTPS
ENFORCE_HTTPS=true
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Security - Data Protection
MASK_PII_IN_LOGS=true
ENABLE_ENCRYPTION_AT_REST=true
ENCRYPTION_KEY=<generated-encryption-key>

# CORS (HTTPS only, no wildcards!)
CORS_ORIGINS=https://yourdomain.com
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE
CORS_ALLOW_HEADERS=Content-Type,Authorization,X-API-Key

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=500

# Request Security
MAX_REQUEST_SIZE=10485760

# Vector Database
CHROMA_PERSIST_DIRECTORY=/var/lib/customer-service-ai/chroma_db
```

---

## Deployment Steps

### Option 1: Docker Deployment (Recommended)

#### 1. Build Production Image
```bash
# Build optimized production image
docker build -t customer-service-ai:production -f backend/Dockerfile.prod backend/

# Tag for registry
docker tag customer-service-ai:production your-registry.com/customer-service-ai:v1.0.0
docker push your-registry.com/customer-service-ai:v1.0.0
```

#### 2. Run with Docker Compose
```bash
# Use production docker-compose configuration
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose logs -f backend

# Verify health
curl https://yourdomain.com/health
```

### Option 2: Kubernetes Deployment

#### 1. Create Secrets
```bash
# Create Kubernetes secrets
kubectl create secret generic customer-service-ai-secrets \
  --from-literal=api-keys="<key1>,<key2>" \
  --from-literal=jwt-secret="<jwt-secret>" \
  --from-literal=encryption-key="<encryption-key>" \
  --namespace=production
```

#### 2. Deploy Application
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Check deployment
kubectl get pods -n production
kubectl logs -f deployment/customer-service-ai -n production
```

### Option 3: AWS ECS/Fargate

#### 1. Create Task Definition
```bash
# Use ECS task definition with:
# - IAM role for Bedrock access
# - Secrets from AWS Secrets Manager
# - Health checks configured
# - Resource limits set

aws ecs register-task-definition --cli-input-json file://task-definition.json
```

#### 2. Deploy Service
```bash
aws ecs create-service \
  --cluster production-cluster \
  --service-name customer-service-ai \
  --task-definition customer-service-ai:1 \
  --desired-count 2 \
  --load-balancers targetGroupArn=<tg-arn>,containerName=backend,containerPort=8000
```

---

## Post-Deployment Verification

### 1. Health Checks

```bash
# Basic health check
curl https://yourdomain.com/health

# Expected response:
{
  "status": "healthy",
  "environment": "production",
  "services": {
    "api": "operational",
    "vector_db": "operational",
    "cache": "operational"
  },
  "security": {
    "authentication_required": true,
    "https_enforced": true,
    "rate_limiting_enabled": true,
    "pii_masking_enabled": true
  }
}
```

### 2. Security Verification

```bash
# Test authentication (should fail without API key)
curl https://yourdomain.com/api/v1/chat

# Test with valid API key (should succeed)
curl -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"message": "test", "session_id": "test"}' \
     https://yourdomain.com/api/v1/chat

# Verify HTTPS redirect
curl -I http://yourdomain.com
# Should return 301 redirect to https://

# Check security headers
curl -I https://yourdomain.com
# Should include:
# - Strict-Transport-Security
# - X-Content-Type-Options: nosniff
# - X-Frame-Options: DENY
# - Content-Security-Policy
```

### 3. Production Validation

The application automatically validates production configuration on startup:

```bash
# Check logs for validation results
docker logs customer-service-ai-backend | grep "validation"

# Should see:
# ✓ Production validation passed
```

If validation fails, the application will not start and will log specific errors.

---

## Monitoring & Maintenance

### 1. Application Monitoring

#### Health Check Monitoring
```bash
# Set up automated health checks every 30 seconds
# Alert if status != "healthy" for 2+ consecutive checks

# Example with monitoring tool:
/health endpoint -> 200 OK
  - Check response time < 500ms
  - Check status == "healthy"
  - Alert on degraded or error states
```

#### Metrics to Monitor
- Request rate and response times
- Error rates (4xx, 5xx)
- Cache hit rate
- Active session count
- Rate limit violations
- Authentication failures

### 2. Log Monitoring

```bash
# Centralized logging (e.g., CloudWatch, ELK, Datadog)
# Monitor for:
# - ERROR and CRITICAL log levels
# - Authentication failures
# - Rate limit exceeded
# - Security violations
# - System errors

# Example CloudWatch Logs Insights query:
fields @timestamp, @message
| filter level == "ERROR" or level == "CRITICAL"
| sort @timestamp desc
| limit 100
```

### 3. Security Monitoring

Monitor audit logs for:
- Failed authentication attempts
- Authorization denials
- Unusual access patterns
- Security violations
- Configuration changes

```bash
# Audit log format:
{
  "timestamp": "2025-11-20T10:30:00Z",
  "event_type": "auth.failure",
  "severity": "high",
  "ip_address": "192.168.1.1",
  "details": {"reason": "Invalid API key"}
}
```

### 4. Regular Maintenance

#### Daily
- [ ] Check error logs
- [ ] Monitor performance metrics
- [ ] Verify backup completion

#### Weekly
- [ ] Review security audit logs
- [ ] Check for dependency updates
- [ ] Review rate limit patterns

#### Monthly
- [ ] Rotate API keys and secrets
- [ ] Review and update security policies
- [ ] Perform security scan
- [ ] Update dependencies

---

## Incident Response

### Security Incident Procedure

#### 1. Detection
- Automated alerts from monitoring
- Audit log anomalies
- User reports

#### 2. Immediate Response
```bash
# If credentials compromised:
# 1. Immediately rotate all API keys
# 2. Invalidate all JWT tokens
# 3. Review audit logs for unauthorized access
# 4. Block suspicious IP addresses

# Emergency credential rotation:
# Update .env with new credentials
docker-compose restart backend

# Or for Kubernetes:
kubectl rollout restart deployment/customer-service-ai -n production
```

#### 3. Investigation
- Review audit logs
- Check access patterns
- Identify scope of breach
- Document findings

#### 4. Remediation
- Patch vulnerabilities
- Update security configurations
- Implement additional controls
- Update documentation

#### 5. Post-Incident
- Conduct post-mortem
- Update incident response procedures
- Implement preventive measures
- Communicate with stakeholders

---

## Performance Tuning

### Backend Optimization

```bash
# Uvicorn workers (CPU cores * 2 + 1)
# For 4 CPU cores:
uvicorn app.main:app --workers 9 --host 0.0.0.0 --port 8000

# Or in Docker:
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "9"]
```

### Scaling Considerations

#### Horizontal Scaling
- Deploy multiple backend instances
- Use load balancer with sticky sessions
- Consider Redis for shared session storage
- Implement distributed caching

#### Vertical Scaling
- Monitor CPU and memory usage
- Adjust container resource limits
- Optimize vector database performance

---

## Compliance & Data Protection

### GDPR Compliance

1. **Data Minimization**: Only collect necessary data
2. **Data Retention**: Automatic cleanup after 24 hours
3. **User Rights**: Implement data deletion API
4. **Privacy by Design**: PII masking enabled by default

### Data Handling

- **PII Detection**: Automatic detection and masking in logs
- **Encryption**: Data encrypted at rest and in transit
- **Access Control**: Authentication required for all endpoints
- **Audit Trail**: Complete audit logs for all data access

---

## Support & Troubleshooting

### Common Issues

#### Issue: Production validation fails on startup
**Solution**: Check all required environment variables are set correctly
```bash
# Review validation errors in logs
docker logs customer-service-ai-backend 2>&1 | grep "validation"
```

#### Issue: Authentication not working
**Solution**: Verify API key format and configuration
```bash
# Test API key
echo $API_KEYS | tr ',' '\n'

# Ensure REQUIRE_AUTHENTICATION=true
grep REQUIRE_AUTHENTICATION .env
```

#### Issue: HTTPS redirect not working
**Solution**: Check ENFORCE_HTTPS setting and load balancer configuration
```bash
# Verify setting
grep ENFORCE_HTTPS .env

# Check if load balancer is terminating SSL
# Ensure X-Forwarded-Proto header is set
```

### Getting Help

- Review application logs: `docker logs customer-service-ai-backend`
- Check health endpoint: `curl https://yourdomain.com/health`
- Review audit logs for security issues
- Contact support with error details and logs

---

## Security Best Practices Summary

✅ **DO:**
- Use HTTPS everywhere
- Enable authentication in production
- Rotate credentials regularly
- Monitor security logs
- Keep dependencies updated
- Use secure random values for secrets
- Implement rate limiting
- Mask PII in logs
- Use IAM roles instead of hardcoded credentials

❌ **DON'T:**
- Commit secrets to git
- Use default credentials
- Disable security features
- Allow wildcard CORS origins
- Run with DEBUG logging in production
- Use HTTP in production
- Hardcode API keys in code
- Ignore security alerts

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [AWS Security Best Practices](https://aws.amazon.com/security/security-resources/)
- [Docker Security](https://docs.docker.com/engine/security/)

---

**Last Updated**: 2025-11-20
**Version**: 1.0.0
