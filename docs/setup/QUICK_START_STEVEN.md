# 🚀 YOUR PERSONALIZED QUICK START GUIDE

Hi Steven! Here's your customized setup guide with your API keys already configured.

## ✅ What You Already Have

1. **OpenAI API Key** - Already configured in `backend/.env` ✅
2. **AWS Bedrock Access** - Through ASU AZNext (credentials needed) ⏳
3. **Project Scaffolding** - Complete and ready ✅

## 🔧 Setup Steps (15 minutes)

### Step 1: Get AWS Credentials (5 minutes)

You need to grab your AWS credentials from the AZNext portal:

1. **Go to**: https://links.asu.edu/aznext-bedrock
2. **Sign in** with:
   - Username: `sjohn430`
   - Password: (the one you created)
3. **Get credentials**:
   - Look for "Command line or programmatic access" in top-right
   - Copy the three values (ACCESS_KEY_ID, SECRET_ACCESS_KEY, SESSION_TOKEN)
4. **Update** `backend/.env`:
   - Replace the `your_aws_access_key_here` placeholders with your actual values

📖 **Detailed instructions**: See `AWS_CREDENTIALS_GUIDE.md`

### Step 2: Install Backend Dependencies (5 minutes)

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### Step 3: Test Your Credentials (1 minute)

```bash
# Still in backend directory with venv activated
python scripts/test_credentials.py
```

This will verify:
- ✅ OpenAI key works
- ✅ AWS credentials work
- ⚠️ ChromaDB needs data (next step)

### Step 4: Ingest Mock Data (3 minutes)

```bash
# Still in backend directory
python scripts/ingest_data.py
```

You should see:
```
✓ Successfully ingested billing documents
✓ Successfully ingested technical documents
✓ Successfully ingested policy documents
```

### Step 5: Install Frontend Dependencies (2 minutes)

```bash
# Open a new terminal
cd frontend
npm install
```

### Step 6: Start Everything! (30 seconds)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python -m app.main
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Open browser:** http://localhost:3000

## 🎯 Test It Out!

Try these queries to see each agent in action:

1. **Billing Agent**: "What are your pricing plans?"
2. **Technical Agent**: "I can't log in to my account"
3. **Policy Agent**: "What is your privacy policy?"

Each response will show which agent handled it!

## 🆘 Troubleshooting

### "AWS credentials not found"
- Run: `python scripts/test_credentials.py`
- Check your `.env` file has all three AWS variables
- See: `AWS_CREDENTIALS_GUIDE.md`

### "Session token expired"
- AWS SSO tokens expire after ~12 hours
- Go back to AWS Console → Get new credentials
- Update `.env` with new values

### "OpenAI error"
- Your key is already configured
- Check you're not over quota
- Verify key hasn't been revoked

### "No module named 'app'"
- Make sure you're in the `backend` directory
- Check virtual environment is activated: `source venv/bin/activate`

### Frontend can't connect
- Make sure backend is running on port 8000
- Check: http://localhost:8000/health
- Look for CORS errors in browser console

## 📊 Project Structure Reminder

```
customer-service-ai/
├── backend/
│   ├── .env                 ← Your API keys go here
│   ├── app/
│   │   ├── agents/          ← The AI agents
│   │   ├── api/             ← FastAPI endpoints
│   │   └── main.py          ← Start server here
│   └── scripts/
│       ├── ingest_data.py   ← Run this to load data
│       └── test_credentials.py  ← Test your setup
├── frontend/
│   └── src/                 ← React components
└── AWS_CREDENTIALS_GUIDE.md ← Detailed AWS help
```

## 🎬 Recording Your Demo Video

When you're ready to record, follow the script in `PROJECT_CHECKLIST.md`:

1. **Introduction** (30s) - Project overview
2. **Architecture** (1m) - Explain multi-agent system
3. **Live Demo** (5-6m) - Show all three agents working
4. **Code Tour** (3-4m) - Walk through key files
5. **Conclusion** (30s) - Wrap up

**Total**: 5-10 minutes

## 📝 Important Files

- `README.md` - Complete documentation
- `AWS_CREDENTIALS_GUIDE.md` - AWS setup help
- `PROJECT_CHECKLIST.md` - Testing checklist & demo script
- `backend/.env` - Your API keys (OpenAI already configured!)

## 🎓 For Your Course

This project demonstrates:
- ✅ Multi-agent orchestration (LangGraph)
- ✅ Three retrieval strategies (RAG, CAG, Hybrid)
- ✅ Multi-provider LLM (OpenAI + AWS Bedrock)
- ✅ Full-stack implementation
- ✅ Production-ready architecture
- ✅ Vibe Coding methodology

## 💡 Pro Tips

1. **Keep terminals open**: You'll need both backend and frontend running
2. **Watch the logs**: Backend shows which agent is handling each query
3. **Test thoroughly**: Use the checklist before recording
4. **AWS credentials expire**: Refresh them if you get auth errors
5. **Save often**: Commit to git frequently

## ✨ You're Almost There!

Just need to:
1. ⏳ Get AWS credentials (5 min)
2. ⏳ Run setup commands (10 min)

Then you're ready to demo! 🚀

---

**Questions?** Check the main README.md or the troubleshooting sections above.

**Ready to start?** Begin with Step 1 - Get AWS Credentials!
