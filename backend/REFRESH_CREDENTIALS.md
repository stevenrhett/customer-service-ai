# Quick Guide: Refreshing Expired AWS Credentials

## Problem
You're seeing this error:
```
ExpiredTokenException: The security token included in the request is expired
```

This happens because AWS SSO credentials are temporary (usually valid for 12 hours).

## Solution: Refresh Your Credentials

### Step 1: Get New Credentials from AWS Console

1. **Log into AWS Console**
   - Go to: https://links.asu.edu/aznext-bedrock
   - Sign in with username: `sjohn430`

2. **Get Command Line Credentials**
   - Click on your username in the top-right corner
   - Click "Command line or programmatic access"
   - You'll see three export commands:
     ```bash
     export AWS_ACCESS_KEY_ID="ASIA..."
     export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI..."
     export AWS_SESSION_TOKEN="IQoJb3JpZ2luX2..."
     ```

### Step 2: Update Your Credentials

**Option A: Update `load_env.sh` (if you're using it)**
```bash
# Edit backend/load_env.sh
# Replace the three AWS credential values with the new ones from Step 1
```

**Option B: Update `.env` file (recommended)**
```bash
# Edit backend/.env
# Add or update these lines:
AWS_ACCESS_KEY_ID=ASIA...
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI...
AWS_SESSION_TOKEN=IQoJb3JpZ2luX2...
AWS_REGION=us-west-2
```

### Step 3: Reload Environment Variables

**If using `load_env.sh`:**
```bash
cd backend
source load_env.sh
```

**If using `.env` file:**
The application will automatically load from `.env` when you restart it.

### Step 4: Restart Your Application

```bash
# Stop the current server (Ctrl+C)
# Then restart:
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

## Verification

Test your credentials:
```bash
cd backend
source venv/bin/activate
python scripts/test_credentials.py
```

You should see:
```
✓ AWS Region: us-west-2
✓ AWS Credentials: Loaded
✓ Bedrock Access: Granted
```

## Note About sentence-transformers Warning

The `sentence-transformers` package is already installed. If you still see warnings, they're harmless - the vector stores will work once the embeddings are loaded. The warnings may appear on first import but won't affect functionality.

## Pro Tip

Set a reminder to refresh credentials every 12 hours, or use AWS CLI SSO for automatic credential refresh:
```bash
pip install awscli
aws configure sso
```

