# Deployment Guide

This guide covers deploying the Customer Service AI application to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Backend Deployment](#backend-deployment)
4. [Frontend Deployment](#frontend-deployment)
5. [Database Setup](#database-setup)
6. [Monitoring & Logging](#monitoring--logging)
7. [Scaling Considerations](#scaling-considerations)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:

- Python 3.10+ installed
- Node.js 18+ and npm installed
- AWS account with Bedrock access configured
- OpenAI API key
- Domain name (optional, for production)
- SSL certificate (for HTTPS)

---

## Environment Setup

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-key

# AWS Bedrock Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-west-2

# Application Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO

# Vector Database
CHROMA_PERSIST_DIRECTORY=/app/chroma_db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# CORS Configuration (comma-separated)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Frontend URL
FRONTEND_URL=https://yourdomain.com
```

### Frontend Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

---

## Backend Deployment

### Option 1: Docker Deployment (Recommended)

#### 1. Create Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Build and Run

```bash
cd backend
docker build -t customer-service-ai-backend .
docker run -d \
  --name customer-service-ai \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/chroma_db:/app/chroma_db \
  customer-service-ai-backend
```

### Option 2: Direct Deployment

#### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Run Data Ingestion

```bash
python scripts/ingest_data.py
```

#### 3. Start with Uvicorn

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 4. Production with Gunicorn (Recommended)

```bash
pip install gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

### Option 3: Cloud Platform Deployment

#### AWS Elastic Beanstalk

1. Install EB CLI:
```bash
pip install awsebcli
```

2. Initialize EB:
```bash
cd backend
eb init -p python-3.10 customer-service-ai
eb create customer-service-ai-env
```

3. Configure environment variables in AWS Console or via CLI:
```bash
eb setenv OPENAI_API_KEY=sk-xxx AWS_ACCESS_KEY_ID=xxx ...
```

#### Heroku

1. Create `Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

2. Deploy:
```bash
heroku create customer-service-ai
heroku config:set OPENAI_API_KEY=sk-xxx ...
git push heroku main
```

#### Railway

1. Connect repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on push

---

## Frontend Deployment

### Option 1: Vercel (Recommended for Next.js)

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Deploy:
```bash
cd frontend
vercel
```

3. Configure environment variables in Vercel dashboard

### Option 2: Next.js Standalone

1. Build:
```bash
cd frontend
npm run build
```

2. Start:
```bash
npm start
```

### Option 3: Docker

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
CMD ["npm", "start"]
```

---

## Database Setup

### ChromaDB Persistence

ChromaDB stores data in the `chroma_db/` directory. For production:

1. **Use persistent volumes** (Docker/Kubernetes):
```yaml
volumes:
  - ./chroma_db:/app/chroma_db
```

2. **Backup regularly**:
```bash
# Backup ChromaDB
tar -czf chroma_db_backup_$(date +%Y%m%d).tar.gz chroma_db/
```

3. **Restore from backup**:
```bash
tar -xzf chroma_db_backup_YYYYMMDD.tar.gz
```

### Optional: Redis for Session Storage

Replace in-memory session storage with Redis:

1. Install Redis:
```bash
docker run -d -p 6379:6379 redis:alpine
```

2. Update `session_manager.py` to use Redis:
```python
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)
```

---

## Monitoring & Logging

### Application Logs

The application logs to stdout. Configure log aggregation:

- **CloudWatch** (AWS)
- **Datadog**
- **Sentry** (error tracking)
- **ELK Stack** (Elasticsearch, Logstash, Kibana)

### Health Checks

The application provides health check endpoints:

- `GET /health` - Detailed health status
- `GET /` - Basic status

Configure your load balancer to check these endpoints.

### Metrics

Monitor:
- Request rate and latency
- LLM API costs (OpenAI + AWS Bedrock)
- Cache hit rates (available via `/health`)
- Error rates
- Active sessions

---

## Scaling Considerations

### Horizontal Scaling

1. **Backend**: Stateless, can scale horizontally
   - Use load balancer (ALB, NLB, or Cloudflare)
   - Session storage must be external (Redis)

2. **Frontend**: Next.js can be scaled horizontally
   - Use CDN for static assets
   - Consider ISR (Incremental Static Regeneration)

### Vertical Scaling

- Increase workers for Gunicorn
- Increase memory for ChromaDB operations
- Consider GPU for embeddings (if needed)

### Caching Strategy

- Redis for distributed caching (replace in-memory cache)
- CDN for static assets
- HTTP caching headers

### Database Optimization

- ChromaDB: Single instance limitation
- Consider PostgreSQL + pgvector for distributed vector search
- Index optimization for large document sets

---

## Security Checklist

- [ ] Use HTTPS everywhere
- [ ] Set secure CORS origins
- [ ] Enable rate limiting
- [ ] Use environment variables for secrets
- [ ] Implement API authentication (optional)
- [ ] Regular security updates
- [ ] Input validation (already implemented)
- [ ] Sanitize user inputs (already implemented)
- [ ] Monitor for abuse

---

## Troubleshooting

### Common Issues

#### 1. ChromaDB Not Found

**Error**: `Could not load vector store`

**Solution**:
```bash
cd backend
python scripts/ingest_data.py
```

#### 2. CORS Errors

**Error**: `CORS policy blocked`

**Solution**: Update `CORS_ORIGINS` environment variable with your frontend URL

#### 3. Rate Limiting Issues

**Error**: `429 Too Many Requests`

**Solution**: Adjust `RATE_LIMIT_PER_MINUTE` in environment variables

#### 4. LLM API Errors

**Error**: `OpenAI API error` or `AWS Bedrock error`

**Solutions**:
- Verify API keys are correct
- Check AWS credentials and permissions
- Verify AWS region supports Bedrock
- Check API rate limits

#### 5. Session Not Persisting

**Issue**: Sessions reset on restart

**Solution**: Use Redis for session storage instead of in-memory

---

## Production Checklist

- [ ] Environment variables configured
- [ ] Data ingestion completed
- [ ] HTTPS enabled
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Monitoring set up
- [ ] Logging configured
- [ ] Backup strategy in place
- [ ] Health checks configured
- [ ] Error tracking set up
- [ ] Performance testing completed
- [ ] Security audit completed

---

## Quick Start Commands

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/ingest_data.py
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

---

## Support

For issues or questions:
1. Check logs: `docker logs customer-service-ai`
2. Check health endpoint: `curl http://localhost:8000/health`
3. Review PROJECT_REVIEW.md for known issues
4. Check FIXES_APPLIED.md for recent fixes

---

*Last Updated: Post-fix implementation*

