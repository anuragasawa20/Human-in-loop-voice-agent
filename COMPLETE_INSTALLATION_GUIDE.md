# Complete Installation Guide

> Step-by-step instructions to install and run the Human-in-the-Loop AI Agent system with semantic search.

**Time Required:** ~30 minutes  
**Difficulty:** Intermediate  
**Prerequisites:** Basic terminal/command line knowledge

---

## 📋 Table of Contents

1. [Prerequisites & Accounts](#prerequisites--accounts)
2. [System Requirements](#system-requirements)
3. [Firebase Setup](#step-1-firebase-setup)
4. [LiveKit Setup](#step-2-livekit-setup)
5. [OpenAI Setup](#step-3-openai-setup)
6. [Agent Installation](#step-4-agent-installation)
7. [Backend Installation](#step-5-backend-installation)
8. [Frontend Installation](#step-6-frontend-installation-streamlit)
9. [Environment Variables](#step-7-environment-variables)
10. [Initialize Database](#step-8-initialize-database)
11. [Run the System](#step-9-run-the-system)
12. [Test Complete Flow](#step-10-test-complete-flow)
13. [Deployment](#step-11-deploy-to-production)
14. [Troubleshooting](#troubleshooting)

---

## Prerequisites & Accounts

### Required Accounts (All have free tiers!)

| Service | Purpose | Cost | Sign Up |
|---------|---------|------|---------|
| **Firebase** | Database & real-time sync | Free tier sufficient | [console.firebase.google.com](https://console.firebase.google.com/) |
| **LiveKit** | Voice AI infrastructure | $0 (50 hours/month free) | [cloud.livekit.io](https://cloud.livekit.io/) |
| **OpenAI** | LLM + embeddings | ~$5/month testing | [platform.openai.com](https://platform.openai.com/) |

### Optional Accounts

| Service | Purpose | Cost | Sign Up |
|---------|---------|------|---------|
| **Pinecone** | Production vector DB (optional) | Free tier available | [pinecone.io](https://www.pinecone.io/) |

---

## System Requirements

### Software Requirements

- **Python 3.9+** (3.11 recommended)
- **Git** (for cloning repository)
- **Terminal/Command Line** access
- **Text Editor** (VS Code recommended)

### Operating System

- ✅ macOS (Apple Silicon or Intel)
- ✅ Linux (Ubuntu 20.04+)
- ✅ Windows (WSL2 recommended)

### Hardware Requirements

- **Minimum:** 4GB RAM, 2 CPU cores, 5GB storage
- **Recommended:** 8GB RAM, 4 CPU cores, 10GB storage

---

## Step 1: Firebase Setup

### 1.1 Create Firebase Project

```bash
# Open Firebase Console
open https://console.firebase.google.com/
```

1. Click "**Add project**"
2. Enter project name: `salon-ai-agent` (or your choice)
3. Disable Google Analytics (not needed for this project)
4. Click "**Create project**"

### 1.2 Enable Firestore Database

1. In left sidebar, click "**Firestore Database**"
2. Click "**Create database**"
3. Select "**Start in test mode**" (for development)
4. Choose location (pick closest to you)
5. Click "**Enable**"

### 1.3 Create Web App Configuration

1. In Project Overview, click the **Web icon** (</>)
2. Register app name: `salon-dashboard`
3. Don't enable Firebase Hosting
4. Copy the configuration object - save for later:

```javascript
const firebaseConfig = {
  apiKey: "AIza...",
  authDomain: "salon-ai-agent.firebaseapp.com",
  projectId: "salon-ai-agent",
  storageBucket: "salon-ai-agent.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123"
};
```

### 1.4 Generate Service Account Key

1. Go to **Project Settings** (gear icon) → **Service Accounts**
2. Click "**Generate new private key**"
3. Click "**Generate key**" (JSON file downloads)
4. Save as `firebase-credentials.json` (we'll use this later)

### 1.5 Note Your Project ID

```bash
# Example: salon-ai-agent
# You'll need this for environment variables
```

---

## Step 2: LiveKit Setup

### 2.1 Create LiveKit Account

```bash
# Open LiveKit Cloud
open https://cloud.livekit.io/
```

1. Sign up with GitHub or Google
2. Verify email
3. Create a project (default name is fine)

### 2.2 Install LiveKit CLI

**macOS/Linux:**
```bash
brew install livekit-cli
# OR
curl -sSL https://get.livekit.io/cli | bash
```

**Windows (PowerShell):**
```powershell
iwr https://get.livekit.io/cli.ps1 -useb | iex
```

### 2.3 Authenticate CLI

```bash
# This opens browser to authenticate
lk cloud auth
```

Follow the prompts to link your CLI to your LiveKit account.

### 2.4 Get Project Credentials

```bash
# Navigate to agent directory (we'll create this soon)
cd /Users/mavens/Human-in-the-loop-Agent/agent/

# Generate .env.local with LiveKit credentials
lk app env -w
```

This creates `agent/.env.local` with:
```bash
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxxx
```

---

## Step 3: OpenAI Setup

### 3.1 Get API Key

1. Go to [platform.openai.com](https://platform.openai.com/)
2. Sign up or log in
3. Go to **API Keys** section
4. Click "**Create new secret key**"
5. Name it: `salon-agent`
6. Copy the key (starts with `sk-...`)
7. **Save it securely** - you can't view it again!

### 3.2 Add Credits (if new account)

1. Go to **Billing** → **Payment methods**
2. Add payment method
3. Add $5-10 credit for testing

**Cost estimate:**
- Development/testing: ~$5/month
- Semantic search: ~$0.02/month for 1000 queries
- GPT-4.1 mini calls: ~$0.01 per 1000 tokens

---

## Step 4: Agent Installation

### 4.1 Navigate to Project

```bash
cd /Users/mavens/Human-in-the-loop-Agent/agent/
```

### 4.2 Install uv (Python Package Manager)

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (add to ~/.zshrc or ~/.bashrc)
export PATH="$HOME/.cargo/bin:$PATH"

# Reload shell
source ~/.zshrc  # or source ~/.bashrc
```

**Windows (PowerShell as Admin):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify installation:
```bash
uv --version
# Should show: uv 0.x.x
```

### 4.3 Install Agent Dependencies

```bash
cd agent/

# Install all dependencies (including chromadb, openai)
uv sync

# This installs:
# - livekit-agents
# - openai (for LLM + embeddings)
# - chromadb (for vector search)
# - firebase-admin
# - httpx
# - python-dotenv
```

### 4.4 Configure Agent Environment

Create `agent/.env.local`:

```bash
# Copy from template
cat > .env.local << 'EOF'
# LiveKit Configuration (from: lk app env -w)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxxx

# OpenAI Configuration
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxx

# Firebase Configuration
FIREBASE_PROJECT_ID=salon-ai-agent
FIREBASE_CREDENTIALS_PATH=../firebase-credentials.json

# Agent Configuration
LOG_LEVEL=INFO
CONFIDENCE_THRESHOLD=0.8
EOF
```

**Edit the file** with your actual credentials:
```bash
nano .env.local  # or use your preferred editor
```

### 4.5 Download Model Files

```bash
# Download required AI models
uv run agent.py download-files

# This downloads:
# - Silero VAD model (voice activity detection)
# - Other required files
```

---

## Step 5: Backend Installation

### 5.1 Install Backend Dependencies

```bash
cd /Users/mavens/Human-in-the-loop-Agent/backend/

# Install dependencies
uv sync

# This installs:
# - fastapi
# - uvicorn
# - firebase-admin
# - httpx
# - pydantic
```

### 5.2 Configure Backend Environment

Create `backend/.env.local`:

```bash
cat > .env.local << 'EOF'
# Firebase Configuration
FIREBASE_PROJECT_ID=salon-ai-agent
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Timeout Configuration
REQUEST_TIMEOUT_MINUTES=30

# CORS (for frontend)
ALLOWED_ORIGINS=http://localhost:8501,http://localhost:5173
EOF
```

**Edit with your project ID:**
```bash
nano .env.local
```

### 5.3 Copy Firebase Credentials

```bash
# Copy the firebase-credentials.json you downloaded earlier
cp ~/Downloads/firebase-credentials.json ./firebase-credentials.json

# Verify it exists
ls -la firebase-credentials.json
```

---

## Step 6: Frontend Installation (Streamlit)

### 6.1 Install Frontend Dependencies

```bash
cd /Users/mavens/Human-in-the-loop-Agent/frontend/

# Install dependencies
uv sync

# This installs:
# - streamlit
# - firebase-admin
# - httpx
# - python-dotenv
```

### 6.2 Configure Frontend Environment

Create `frontend/.env.local`:

```bash
cat > .env.local << 'EOF'
# Backend API
BACKEND_URL=http://localhost:8000

# Firebase Configuration
FIREBASE_PROJECT_ID=salon-ai-agent
FIREBASE_CREDENTIALS_PATH=../firebase-credentials.json

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
EOF
```

**Edit with your values:**
```bash
nano .env.local
```

---

## Step 7: Environment Variables

### Summary of All Required Variables

#### Agent (.env.local)
```bash
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxx
FIREBASE_PROJECT_ID=salon-ai-agent
FIREBASE_CREDENTIALS_PATH=../firebase-credentials.json
LOG_LEVEL=INFO
CONFIDENCE_THRESHOLD=0.8
```

#### Backend (.env.local)
```bash
FIREBASE_PROJECT_ID=salon-ai-agent
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
REQUEST_TIMEOUT_MINUTES=30
ALLOWED_ORIGINS=http://localhost:8501
```

#### Frontend (.env.local)
```bash
BACKEND_URL=http://localhost:8000
FIREBASE_PROJECT_ID=salon-ai-agent
FIREBASE_CREDENTIALS_PATH=../firebase-credentials.json
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

### Verify All Files Exist

```bash
cd /Users/mavens/Human-in-the-loop-Agent/

# Check agent
ls -la agent/.env.local
ls -la firebase-credentials.json

# Check backend  
ls -la backend/.env.local
ls -la backend/firebase-credentials.json

# Check frontend
ls -la frontend/.env.local
```

---

## Step 8: Initialize Database

### 8.1 Start Backend

```bash
cd /Users/mavens/Human-in-the-loop-Agent/backend/

# Start backend server
uv run uvicorn main:app --reload
```

**Expected output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Firebase initialized with credentials
INFO:     Firestore client connected
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 8.2 Verify Backend API

Open new terminal:
```bash
# Test health endpoint
curl http://localhost:8000/health

# Should return: {"status":"ok"}

# View API docs
open http://localhost:8000/docs
```

### 8.3 Seed Knowledge Base (Optional but Recommended)

```bash
# In a Python shell
cd /Users/mavens/Human-in-the-loop-Agent/agent/

uv run python << 'EOF'
import asyncio
from knowledge import KnowledgeBaseService
from database import FirebaseClient

async def seed():
    db = FirebaseClient().db
    kb_service = KnowledgeBaseService(db)
    
    print("Seeding knowledge base...")
    await kb_service.seed_initial_data()
    print("Done! Knowledge base seeded.")
    
    print("\nSyncing to vector store...")
    await kb_service.sync_to_vector_store()
    print("Done! Vector store synced.")

asyncio.run(seed())
EOF
```

**Expected output:**
```
Seeding knowledge base...
Added KB entry to Firebase: abc123
Added KB entry to vector store: abc123
...
Successfully seeded 8 KB entries
Done! Knowledge base seeded.

Syncing to vector store...
Syncing Firebase KB to vector store...
Successfully synced 8 entries to vector store
Done! Vector store synced.
```

---

## Step 9: Run the System

You need **3 terminals** running simultaneously.

### Terminal 1: Backend

```bash
cd /Users/mavens/Human-in-the-loop-Agent/backend/
uv run uvicorn main:app --reload
```

**Keep this running.** ✅

### Terminal 2: Agent (Console Mode for Testing)

```bash
cd /Users/mavens/Human-in-the-loop-Agent/agent/
uv run agent.py console
```

**Expected output:**
```
INFO:agent: Starting agent in console mode
INFO:knowledge: KnowledgeBaseService initialized
INFO:knowledge: Semantic search enabled with vector embeddings
INFO:vector_store: Vector store initialized with 8 entries
Agent ready! Type your questions...
```

**Keep this running.** ✅

### Terminal 3: Dashboard

```bash
cd /Users/mavens/Human-in-the-loop-Agent/frontend/
streamlit run dashboard.py
```

**Expected output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

**Keep this running.** ✅

Browser should auto-open to http://localhost:8501

---
