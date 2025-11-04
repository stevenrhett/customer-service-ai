# ✅ SETUP CHECKLIST - Print This Out!

## Pre-Setup
- [ ] Project downloaded/extracted
- [ ] Python 3.10+ installed (check: `python3 --version`)
- [ ] Node.js 18+ installed (check: `node --version`)
- [ ] Two terminal windows ready

## AWS Credentials (5 min)
- [ ] Opened https://links.asu.edu/aznext-bedrock
- [ ] Signed in with username: sjohn430
- [ ] Found "Command line or programmatic access"
- [ ] Copied AWS_ACCESS_KEY_ID
- [ ] Copied AWS_SECRET_ACCESS_KEY  
- [ ] Copied AWS_SESSION_TOKEN
- [ ] Pasted all three into backend/.env
- [ ] Saved backend/.env file

## Backend Setup (10 min)
- [ ] Navigated to backend folder: `cd backend`
- [ ] Created venv: `python3 -m venv venv`
- [ ] Activated venv: `source venv/bin/activate`
- [ ] Installed requirements: `pip install -r requirements.txt`
- [ ] Tested credentials: `python scripts/test_credentials.py`
  - [ ] OpenAI: PASS
  - [ ] AWS Bedrock: PASS
  - [ ] ChromaDB: Needs data (expected)
- [ ] Ingested data: `python scripts/ingest_data.py`
  - [ ] Billing collection created
  - [ ] Technical collection created
  - [ ] Policy collection created
- [ ] Verified: `python scripts/test_credentials.py`
  - [ ] All three tests PASS

## Frontend Setup (5 min)
- [ ] Opened new terminal
- [ ] Navigated to frontend: `cd frontend`
- [ ] Installed packages: `npm install`
- [ ] Checked for errors (should see "added XXX packages")

## Start Application (2 min)

### Terminal 1 - Backend
- [ ] In backend folder
- [ ] Activated venv: `source venv/bin/activate`
- [ ] Started server: `python -m app.main`
- [ ] Server running on http://localhost:8000
- [ ] Checked health: http://localhost:8000/health in browser

### Terminal 2 - Frontend
- [ ] In frontend folder
- [ ] Started dev server: `npm run dev`
- [ ] Server running on http://localhost:3000
- [ ] Opened browser to http://localhost:3000

## Test Each Agent (5 min)

### Billing Agent
- [ ] Asked: "What are your pricing plans?"
- [ ] Got response with pricing information
- [ ] Badge shows: "billing"
- [ ] Response mentions Basic/Pro/Enterprise plans

### Technical Agent  
- [ ] Asked: "How do I enable 2FA?"
- [ ] Got response with 2FA setup steps
- [ ] Badge shows: "technical"
- [ ] Response includes authentication instructions

### Policy Agent
- [ ] Asked: "What is your privacy policy?"
- [ ] Got response about privacy
- [ ] Badge shows: "policy"
- [ ] Response mentions data collection/rights

## Additional Tests

### Multi-turn Conversation
- [ ] Asked follow-up question
- [ ] Agent remembered context
- [ ] Response was relevant

### Mixed Questions
- [ ] Asked billing question
- [ ] Asked technical question  
- [ ] Routing worked correctly for each

## Pre-Recording Checks

### Code Quality
- [ ] Reviewed orchestrator.py - understand routing
- [ ] Reviewed billing_agent.py - understand hybrid approach
- [ ] Reviewed technical_agent.py - understand pure RAG
- [ ] Reviewed policy_agent.py - understand pure CAG
- [ ] Can explain each agent's retrieval strategy

### Demo Preparation
- [ ] Prepared 3 example queries (one per agent)
- [ ] Practiced explaining the architecture
- [ ] Reviewed code sections to show
- [ ] Tested screen recording software
- [ ] Have PROJECT_CHECKLIST.md open for demo script

## Recording Checklist (During Video)

- [ ] Introduction: Name + project overview (30s)
- [ ] Architecture: Explained multi-agent system (1m)
- [ ] Live Demo: 
  - [ ] Showed billing query with badge
  - [ ] Showed technical query with badge
  - [ ] Showed policy query with badge
  - [ ] Explained why routing matters (5-6m)
- [ ] Code Walkthrough:
  - [ ] Showed orchestrator.py routing logic
  - [ ] Showed one agent's retrieval strategy
  - [ ] Showed frontend integration
  - [ ] Explained LangGraph workflow (3-4m)
- [ ] Conclusion: Summarized key features (30s)
- [ ] Total time: 5-10 minutes

## Submission

- [ ] Code committed to GitHub
- [ ] Repository is public
- [ ] README.md is clear and complete
- [ ] Video uploaded to YouTube (unlisted)
- [ ] Video link tested (can view while logged out)
- [ ] Repository link submitted
- [ ] Video link submitted

## Troubleshooting Reference

If something breaks:
1. Check backend/.env has all credentials
2. Try: python scripts/test_credentials.py
3. Restart backend server
4. Clear browser cache and reload
5. Check AWS_CREDENTIALS_GUIDE.md
6. Review error messages in terminal

---

## Notes Section (For Your Use)

AWS Credentials Expiry: _________________ (time/date)

Things to Remember:
_________________________________________________
_________________________________________________
_________________________________________________

Questions for Instructor:
_________________________________________________
_________________________________________________
_________________________________________________

---

**Date Completed**: _________________
**Time Taken**: _________________
**Ready to Record**: [ ] YES  [ ] NO

Good luck! 🚀
