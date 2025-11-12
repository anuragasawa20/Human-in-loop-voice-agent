# Installation Guide

> Choose your preferred installation method below.

---

## 🎯 Choose Your Path

<table>
<tr>
<td width="33%">

### ⚡ Quick Start
**Time:** 10 minutes  
**Detail:** Minimal

For experienced developers who want to get running fast.

**→ [SETUP.md](./SETUP.md)**

</td>
<td width="33%">

### 📚 Complete Guide
**Time:** 30 minutes  
**Detail:** Comprehensive

For first-time setup with full explanations.

**→ [COMPLETE_INSTALLATION_GUIDE.md](./COMPLETE_INSTALLATION_GUIDE.md)**

</td>
<td width="33%">

### 🤖 Automated Script
**Time:** 5 minutes  
**Detail:** Scripted

Automated dependency installation.

**→ [quick_install.sh](./quick_install.sh)**

</td>
</tr>
</table>

---

## 📊 Installation Overview

```
┌─────────────────────────────────────────────────────────┐
│                   PREREQUISITES                         │
│  • Python 3.9+    • Firebase Account                   │
│  • uv installer   • LiveKit Account                    │
│  • Git            • OpenAI API Key                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              INSTALL DEPENDENCIES                        │
│                                                          │
│  Agent:     cd agent/ && uv sync                        │
│  Backend:   cd backend/ && uv sync                      │
│  Frontend:  cd frontend/ && uv sync                     │
│                                                          │
│  Installs: LiveKit, OpenAI, ChromaDB, Firebase,        │
│            FastAPI, Streamlit, and more                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│           CONFIGURE ENVIRONMENT                          │
│                                                          │
│  1. Download firebase-credentials.json                  │
│  2. Run: lk app env -w (generates LiveKit config)      │
│  3. Create .env.local files in:                         │
│     • agent/                                             │
│     • backend/                                           │
│     • frontend/                                          │
│  4. Add API keys and credentials                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│          INITIALIZE DATABASE                             │
│                                                          │
│  1. Start backend: uv run uvicorn main:app --reload    │
│  2. Seed knowledge base with initial data              │
│  3. Sync to vector store for semantic search           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│             RUN THE SYSTEM                               │
│                                                          │
│  Terminal 1: Backend  → http://localhost:8000          │
│  Terminal 2: Agent    → Console mode                    │
│  Terminal 3: Dashboard → http://localhost:8501         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                TEST & VERIFY                             │
│                                                          │
│  ✅ Known questions answered                            │
│  ✅ Semantic search working                             │
│  ✅ Unknown questions escalate                          │
│  ✅ Dashboard receives requests                         │
│  ✅ System learns from responses                        │
└─────────────────────────────────────────────────────────┘
                          ↓
                   🎉 SUCCESS!
```

---

## 🚀 Quick Install Commands

```bash
# Navigate to project
cd /Users/mavens/Human-in-the-loop-Agent


#  Manual install
cd agent && uv sync
cd ../backend && uv sync
cd ../frontend && uv sync

# Configure environment (see guides)
# Then run:
cd backend && uv run uvicorn main:app --reload     # Terminal 1
cd agent && uv run agent.py console                 # Terminal 2
cd frontend && streamlit run dashboard.py           # Terminal 3
```

---

## 📋 Prerequisites Checklist

Before starting installation:

### Accounts (Free Tiers Available)
- [ ] **Firebase account** - [console.firebase.google.com](https://console.firebase.google.com/)
- [ ] **LiveKit account** - [cloud.livekit.io](https://cloud.livekit.io/)
- [ ] **OpenAI account** - [platform.openai.com](https://platform.openai.com/)

### Software
- [ ] **Python 3.9+** - `python3 --version`
- [ ] **uv** - `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [ ] **LiveKit CLI** - `brew install livekit-cli`
- [ ] **Git** - `git --version`

### Credentials Ready
- [ ] Firebase `firebase-credentials.json` downloaded
- [ ] Firebase Project ID noted
- [ ] OpenAI API key copied
- [ ] LiveKit credentials generated (`lk app env -w`)

---

## 📦 What Gets Installed

### Agent Components
- **livekit-agents** - Voice AI framework
- **openai** - LLM + embeddings API
- **chromadb** - Vector database for semantic search
- **firebase-admin** - Database client
- **httpx** - HTTP client
- **python-dotenv** - Environment management

### Backend Components
- **fastapi** - REST API framework
- **uvicorn** - ASGI server
- **firebase-admin** - Database client
- **pydantic** - Data validation

### Frontend Components
- **streamlit** - Dashboard framework
- **firebase-admin** - Real-time database
- **httpx** - API client

**Total size:** ~500 MB  
**Installation time:** ~5 minutes on fast connection

---

## 🎯 Installation Paths

### Path 1: Quick Setup (Experienced Users)

```bash
1. Create accounts (Firebase, LiveKit, OpenAI)
2. Run: ./quick_install.sh
3. Configure .env.local files
4. Seed database
5. Run system (3 terminals)
```

**Time:** 10 minutes  
**Guide:** [SETUP.md](./SETUP.md)

### Path 2: Complete Setup (First Time)

```bash
1. Follow detailed Firebase setup
2. Follow detailed LiveKit setup
3. Follow detailed OpenAI setup
4. Install agent, backend, frontend
5. Configure environment step-by-step
6. Initialize database with guidance
7. Test each component
8. Verify complete flow
```

**Time:** 30 minutes  
**Guide:** [COMPLETE_INSTALLATION_GUIDE.md](./COMPLETE_INSTALLATION_GUIDE.md)

## 🔧 Configuration Summary

### Environment Variables Needed

| Component | Variables | Purpose |
|-----------|-----------|---------|
| **Agent** | `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` | Voice AI connection |
| | `OPENAI_API_KEY` | LLM + embeddings |
| | `FIREBASE_PROJECT_ID`, `FIREBASE_CREDENTIALS_PATH` | Database |
| | `CONFIDENCE_THRESHOLD` | Semantic search threshold |
| **Backend** | `FIREBASE_PROJECT_ID`, `FIREBASE_CREDENTIALS_PATH` | Database |
| | `PORT`, `HOST` | Server config |
| | `REQUEST_TIMEOUT_MINUTES` | Request lifecycle |
| **Frontend** | `BACKEND_URL` | API connection |
| | `FIREBASE_PROJECT_ID`, `FIREBASE_CREDENTIALS_PATH` | Real-time updates |
| | `STREAMLIT_SERVER_PORT` | Dashboard port |

---

## ✅ Verification Steps

After installation, verify:

1. **Dependencies installed**
   ```bash
   cd agent && uv run python -c "import chromadb; print('✅ ChromaDB')"
   cd ../backend && uv run python -c "import fastapi; print('✅ FastAPI')"
   cd ../frontend && uv run python -c "import streamlit; print('✅ Streamlit')"
   ```

2. **Environment configured**
   ```bash
   cd agent && cat .env.local | grep OPENAI_API_KEY
   cd ../backend && ls firebase-credentials.json
   ```

3. **Services start**
   ```bash
   # Backend
   curl http://localhost:8000/health
   
   # Agent (check console output)
   # Dashboard (check browser loads)
   ```

4. **Functionality works**
   - Ask known question → Immediate answer
   - Ask similar question → Semantic search finds it
   - Ask unknown question → Escalates to dashboard
   - Respond via dashboard → System learns

---

## 🐛 Common Installation Issues

| Problem | Solution |
|---------|----------|
| `uv: command not found` | Install: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `lk: command not found` | Install: `brew install livekit-cli` |
| `Python version too old` | Upgrade: Download from python.org |
| `chromadb install fails` | Try: `pip install chromadb` manually |
| `Firebase auth error` | Check credentials path in `.env.local` |
| `Port already in use` | Kill process: `lsof -ti:8000 \| xargs kill -9` |

See [COMPLETE_INSTALLATION_GUIDE.md](./COMPLETE_INSTALLATION_GUIDE.md#troubleshooting) for detailed troubleshooting.

---

## 📖 Documentation

- **[README.md](./README.md)** - Project overview
- **[SETUP.md](./SETUP.md)** - Quick setup (10 min)
- **[COMPLETE_INSTALLATION_GUIDE.md](./COMPLETE_INSTALLATION_GUIDE.md)** - Full guide (30 min)
- **[INSTALLATION_SUMMARY.md](./INSTALLATION_SUMMARY.md)** - Quick reference
- **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)** - Complete summary

---

