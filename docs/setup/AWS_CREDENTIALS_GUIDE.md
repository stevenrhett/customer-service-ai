# Getting Your AWS Bedrock Credentials

## Your AWS Account Info
- **Username**: sjohn430
- **Sign-in Portal**: https://links.asu.edu/aznext-bedrock-login
- **Console**: https://links.asu.edu/aznext-bedrock
- **Region**: us-west-2 (already configured in .env)

## Step-by-Step: Get Your Credentials

### Method 1: Temporary Credentials (Recommended for SSO)

1. **Log into AWS Console**
   - Go to: https://links.asu.edu/aznext-bedrock
   - Sign in with username: `sjohn430`
   - Use the password you created during activation

2. **Access Command Line Credentials**
   - Look in the top-right corner of the AWS Console
   - Click on your username or "Command line or programmatic access"
   - You'll see a section with credentials that look like this:

   ```bash
   export AWS_ACCESS_KEY_ID="ASIA..."
   export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI..."
   export AWS_SESSION_TOKEN="IQoJb3JpZ2luX2..."
   ```

3. **Copy to .env File**
   - Copy these three values
   - Open `backend/.env`
   - Replace the placeholder values:
   ```
   AWS_ACCESS_KEY_ID=ASIA...
   AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI...
   AWS_SESSION_TOKEN=IQoJb3JpZ2luX2...
   ```

4. **Important Notes**
   - These credentials are **temporary** (usually valid for 12 hours)
   - You'll need to refresh them when they expire
   - The console will show you the expiration time

### Method 2: If Temporary Credentials Don't Work

If the SSO doesn't provide programmatic access, try this:

1. **Create IAM Access Keys**
   - In AWS Console, search for "IAM"
   - Go to "Users" → Find your user
   - Click "Security credentials" tab
   - Click "Create access key"
   - Choose "Command Line Interface (CLI)"
   - Download the credentials

2. **Add to .env**
   ```
   AWS_ACCESS_KEY_ID=AKIA...
   AWS_SECRET_ACCESS_KEY=...
   # Leave AWS_SESSION_TOKEN commented out for permanent keys
   ```

### Verifying AWS Bedrock Access

Once you have credentials configured, test them:

```bash
cd backend
source venv/bin/activate
python -c "import boto3; client = boto3.client('bedrock-runtime', region_name='us-west-2'); print('✓ AWS Bedrock connection successful!')"
```

If you see any errors about:
- **Credentials not found**: Double-check your .env file
- **Access denied**: Your account may need Bedrock permissions enabled
- **Region not available**: Try changing region in .env

### Checking Bedrock Model Access

To verify you can access Claude models:

```python
import boto3

client = boto3.client('bedrock', region_name='us-west-2')
models = client.list_foundation_models()

for model in models['modelSummaries']:
    if 'claude' in model['modelId'].lower():
        print(f"✓ {model['modelId']}")
```

You should see models like:
- `anthropic.claude-3-haiku-20240307-v1:0`
- `anthropic.claude-3-sonnet-20240229-v1:0`

### Troubleshooting

**Problem**: "Credentials not found"
- **Solution**: Make sure .env file is in `backend/` directory
- Check that the file is named exactly `.env` (not `.env.txt`)

**Problem**: "Access Denied to Bedrock"
- **Solution**: Contact your instructor - they may need to enable Bedrock access
- Or try a different region (change AWS_REGION in .env)

**Problem**: "Session token expired"
- **Solution**: Get new temporary credentials from AWS Console
- Update your .env file with the new values

### Alternative: Use AWS CLI Configuration

If you prefer, you can use AWS CLI instead of .env:

1. Install AWS CLI: `pip install awscli`
2. Configure: `aws configure sso`
3. Follow prompts with your AZNext credentials
4. The code will automatically use these credentials

Then in your .env, you can comment out AWS credentials:
```
# AWS credentials configured via AWS CLI SSO
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
```

## Need Help?

If you're having trouble getting AWS credentials:
1. Check the ASU AZNext documentation
2. Contact your instructor (Professor Charles Jester)
3. Reach out to ASU Technology Support

Your OpenAI key is already configured and ready to use! ✅
