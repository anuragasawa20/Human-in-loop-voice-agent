# Quick Setup Guide

> Fast track to get the system running. For detailed instructions, see [COMPLETE_INSTALLATION_GUIDE.md](./COMPLETE_INSTALLATION_GUIDE.md)

---

## ⚡ Prerequisites

1. **Create accounts** (all have free tiers):
   - [Firebase](https://console.firebase.google.com/) - Database
   - [LiveKit](https://cloud.livekit.io/) - Voice AI
   - [OpenAI](https://platform.openai.com/) - LLM + Embeddings

2. **Install software**:
   - Python 3.9+ (`python3 --version`)
   - `uv` package manager ([install](https://astral.sh/uv))
   - LiveKit CLI (`brew install livekit-cli`)

---

## 🚀 Quick Install (5 Minutes)

### 1. Clone & Navigate

```bash
cd /Users/mavens/Human-in-the-loop-Agent
```

### 2. Get Credentials

**Firebase:**
- Create Firestore database
- Download service account JSON → Save as `firebase-credentials.json`

**LiveKit:**
```bash
cd agent/
lk cloud auth
lk app env -w  # Creates .env.local
```

**OpenAI:**
- Get API key from [platform.openai.com](https://platform.openai.com/account/api-keys)

### 3. Configure Environment

**Agent** (`agent/.env.local`):
```bash
# From: lk app env -w
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxxx

# Add these:
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxx
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=../firebase-credentials.json
CONFIDENCE_THRESHOLD=0.8
```

**Backend** (`backend/.env.local`):
```bash
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
PORT=8000
REQUEST_TIMEOUT_MINUTES=30
ALLOWED_ORIGINS=http://localhost:8501
```

**Frontend** (`frontend/.env.local`):
```bash
BACKEND_URL=http://localhost:8000
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=../firebase-credentials.json
STREAMLIT_SERVER_PORT=8501
```

### 4. Copy Firebase Credentials

```bash
# Copy to both backend and root
cp ~/Downloads/firebase-credentials.json ./
cp firebase-credentials.json backend/
```

### 5. Install Dependencies

```bash
# Agent
cd agent/
uv sync

# Backend
cd ../backend/
uv sync

# Frontend
cd ../frontend/
uv sync
```

### 6. Seed Knowledge Base

```bash
cd ../agent/

uv run python << 'EOF'
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from knowledge import KnowledgeBaseService
from database import FirebaseClient

async def seed():
    print("🌱 Seeding knowledge base...")
    db = FirebaseClient().db
    kb = KnowledgeBaseService(db)
    await kb.seed_initial_data()
    await kb.sync_to_vector_store()
    print(f"✅ Done! Vector store has {kb.vector_store.count()} entries")

asyncio.run(seed())
EOF
```

---

## 🎯 Run the System (3 Terminals)

**Terminal 1: Backend**
```bash
cd backend/
uv run uvicorn main:app --reload
```
→ http://localhost:8000

**Terminal 2: Agent**
```bash
cd agent/
uv run agent.py console
```
→ Type questions to test

**Terminal 3: Dashboard**
```bash
cd frontend/
streamlit run dashboard.py
```
→ http://localhost:8501

---

## ✅ Test It Works

**In Agent terminal, type:**

1. **Known question:**
   ```
   What are your hours?
   ```
   → Should answer immediately

2. **Similar question (semantic search):**
   ```
   When do you open?
   ```
   → Should find answer despite different wording

3. **Unknown question:**
   ```
   Do you offer hair extensions?
   ```
   → Should escalate to supervisor
   → Check dashboard to respond
   → Try asking again - should know answer now!

---

## 🐛 Troubleshooting

### Agent won't start
```bash
cd agent/
uv sync
echo $OPENAI_API_KEY  # Should show your key
lk app env -w  # Regenerate LiveKit config
```

### Backend errors
```bash
cd backend/
ls -la firebase-credentials.json  # Should exist
cat .env.local | grep PROJECT_ID  # Should match Firebase
```

### Dashboard not loading
```bash
cd frontend/
streamlit cache clear
curl http://localhost:8000/health  # Backend must be running
streamlit run dashboard.py
```

### Vector store issues
```bash
cd agent/
rm -rf chroma_db/  # Delete and rebuild
# Re-run seed script from step 6
```

---

## 📚 Full Documentation

- **[COMPLETE_INSTALLATION_GUIDE.md](./COMPLETE_INSTALLATION_GUIDE.md)** - Detailed step-by-step (30 min)
- **[SEMANTIC_SEARCH_UPGRADE.md](./SEMANTIC_SEARCH_UPGRADE.md)** - How semantic search works
- **[QUICK_START_SEMANTIC_SEARCH.md](./QUICK_START_SEMANTIC_SEARCH.md)** - 5-min demo
- **[README.md](./README.md)** - Project overview
- **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)** - Complete summary

---

## 🎓 What You Get

After setup, you have:

- ✅ **Voice AI Agent** - Handles calls with STT-LLM-TTS pipeline
- ✅ **Semantic Search** - Finds answers by meaning, not keywords  
- ✅ **RAG Support** - Synthesizes answers from multiple sources
- ✅ **Supervisor Dashboard** - Real-time Streamlit interface
- ✅ **Auto-Learning** - System learns from human responses
- ✅ **Production-Ready** - Scalable architecture with error handling

---

## 🚀 Deploy to Production

Once tested locally:

```bash
# Deploy agent
cd agent/
lk agent create

# Deploy backend (Google Cloud Run)
cd ../backend/
gcloud run deploy salon-backend --source .

# Deploy dashboard (Streamlit Cloud)
# Push to GitHub, then deploy at share.streamlit.io
```

---

## 💡 Quick Tips

1. **Lower confidence threshold** if agent escalates too much:
   ```bash
   # In agent/.env.local
   CONFIDENCE_THRESHOLD=0.7  # Was 0.8
   ```

2. **Add more KB entries** via dashboard or:
   ```python
   await kb_service.add_entry(
       question="Your question?",
       answer="Your answer",
       category="general"
   )
   ```

3. **Monitor costs**:
   - OpenAI: https://platform.openai.com/usage
   - LiveKit: https://cloud.livekit.io/projects/YOUR_PROJECT/usage

4. **View API docs**: http://localhost:8000/docs

---

## Need Help?

1. **Detailed guide**: [COMPLETE_INSTALLATION_GUIDE.md](./COMPLETE_INSTALLATION_GUIDE.md)
2. **Troubleshooting**: See detailed guide or README
3. **Check logs**: Each terminal shows real-time logs
4. **Test components**: Run each piece individually

---

**Setup complete!** 🎉 Start asking questions to your AI agent!
