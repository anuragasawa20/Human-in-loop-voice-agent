# Human-in-the-Loop AI Agent System

> An intelligent AI receptionist that gracefully escalates to human supervisors when uncertain, learns from their answers, and follows up with customers automatically.

## 🎙️ **VOICE DEMO AVAILABLE!**

**📖 Complete guide:** [VOICE_DEMO_GUIDE.md](./VOICE_DEMO_GUIDE.md)

---

The knowledge base now uses **vector embeddings** for semantic search! Questions are matched by meaning, not just keywords.

**Example:**
- User asks: "When can I visit?" 
- System finds: "What are your hours?" (similarity: 89%)
- No exact match needed - understands intent!


---

## 📖 Quick Navigation

### 🎙️ Voice Demo (NEW!)
- **[VOICE_DEMO_GUIDE.md](./VOICE_DEMO_GUIDE.md)** - 👈 **Demo the TALKING agent**

### Installation Guides
- **[INSTALL.md](./INSTALL.md)** - Installation guide
- **[SETUP.md](./SETUP.md)** - Quick setup (10 minutes)
- **[COMPLETE_INSTALLATION_GUIDE.md](./COMPLETE_INSTALLATION_GUIDE.md)** - Detailed guide (30 minutes)

### Documentation

---

## 🎯 What This System Does

```
Customer calls → AI answers if confident → Customer happy ✓

Customer calls → AI uncertain → Escalates to supervisor
              → Supervisor responds → Customer notified
              → Knowledge base learns → Next caller gets instant answer ✓
```

**Key Features:**
- ✅ Voice AI receptionist using LiveKit
- ✅ **Semantic search** with vector embeddings (NEW!)
- ✅ Graceful escalation when uncertain
- ✅ Real-time Streamlit dashboard (Python - no React!)
- ✅ Automatic knowledge base learning
- ✅ Customer follow-up notifications
- ✅ Request lifecycle management with timeouts
- ✅ RAG (Retrieval Augmented Generation) support

---

## 🏗️ System Architecture

```
┌──────────────┐
│  Customer    │
│  Phone Call  │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────┐
│     LiveKit AI Agent                │
│  • STT (AssemblyAI)                 │
│  • LLM (OpenAI GPT-4.1)             │
│  • TTS (Cartesia Sonic-3)           │
│  • Semantic Search (NEW!)           │
│  • Knowledge Base Lookup            │
│  • request_help() Escalation        │
└─────────────────────────────────────┘
       │              │
   Known Answer   Unknown → Escalate
       │              │
       ▼              ▼
┌──────────┐   ┌─────────────────┐
│ Respond  │   │  Firebase DB    │
│ to Caller│   │  Help Request   │
└──────────┘   └────────┬────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │ Streamlit Dashboard │
              │  (Real-time Python) │
              └──────────┬──────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │  Supervisor Answers │
              └──────────┬──────────┘
                        │
         ┌──────────────┴──────────────┐
         ▼                              ▼
┌─────────────────┐          ┌──────────────────┐
│ Notify Customer │          │ Update Knowledge │
│   (Simulated)   │          │  Base + Vectors  │
└─────────────────┘          └──────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Voice AI** | LiveKit Agents | Handles phone calls |
| **STT** | AssemblyAI | Speech recognition |
| **LLM** | OpenAI GPT-4.1 mini | Intelligence |
| **TTS** | Cartesia Sonic-3 | Natural voice |
| **Search** | OpenAI Embeddings + ChromaDB | **Semantic search (NEW!)** |
| **Database** | Firebase Firestore | Real-time data |
| **Backend** | FastAPI (Python) | REST API |
| **Frontend** | Streamlit (Python) | Supervisor dashboard |
| **Deployment** | LiveKit Cloud | Agent hosting |

---

## 📂 Project Structure

```
Human-in-the-loop-Agent/
├── agent/                   # LiveKit AI Agent (Python)
│   ├── agent.py            # Main agent logic
│   ├── knowledge.py        # Knowledge base service (semantic search)
│   ├── vector_store.py     # Vector embeddings & RAG (NEW!)
│   ├── tools.py            # request_help() function
│   ├── prompt.py           # System prompts
│   └── tests/              # Unit tests + semantic search tests
│
├── backend/                # FastAPI Backend (Python)
│   ├── main.py             # REST API endpoints
│   ├── services.py         # Business logic
│   ├── models.py           # Data models
│   ├── database.py         # Firebase client
│   ├── lifecycle.py        # Request lifecycle
│   └── tests/              # Unit tests
│
├── frontend/               # Streamlit Dashboard (Python)
│   ├── dashboard.py        # Complete dashboard app
│   └── README.md           # Streamlit guide
│
└── shared/                 # Shared utilities
    └── README.md
```

---

## 🚀 Quick Start

> **New to this project?** See **[INSTALL.md](./INSTALL.md)** for complete installation instructions!

### Prerequisites
1. **Firebase Project** - Create at [firebase.google.com](https://firebase.google.com)
2. **LiveKit Account** - Sign up at [cloud.livekit.io](https://cloud.livekit.io)
3. **OpenAI API Key** - Get from [platform.openai.com](https://platform.openai.com)

**Detailed setup:** See [COMPLETE_INSTALLATION_GUIDE.md](./COMPLETE_INSTALLATION_GUIDE.md)

### 3 Terminals Setup

**Terminal 1: Backend**
```bash
cd backend/
uv sync
uv run uvicorn main:app --reload
# → http://localhost:8000
```

**Terminal 2: Agent**
```bash
cd agent/
uv sync
uv run agent.py dev
# → Connects to LiveKit Cloud
```

**Terminal 3: Dashboard**
```bash
cd frontend/
uv sync
streamlit run dashboard.py
# → http://localhost:8501
```

### First Time Setup

See [SETUP.md](./SETUP.md) for detailed instructions including:
- Firebase configuration
- LiveKit setup
- Environment variables
- Database initialization

## 🧪 Testing

```bash
# Run all tests
pytest -v

# Test specific component
pytest agent/tests/ -v
pytest backend/tests/ -v

# Test semantic search
cd agent/
python tests/test_semantic_search.py

# With coverage
pytest --cov=. --cov-report=html
```

---

## 📈 Monitoring & Metrics

### Key Metrics

**Knowledge Base:**
- Total entries in vector store
- Average similarity scores
- Cache hit rate
- Most searched topics

**Requests:**
- Escalation rate (should decrease over time!)
- Average response time
- Timeout rate
- Customer satisfaction

**System:**
- API latency
- Embedding generation time
- Database query time
- Error rates

---

## 🔧 Configuration

### Knowledge Base Confidence

```python
# agent/knowledge.py
kb_service = KnowledgeBaseService(
    confidence_threshold=0.8  # Minimum similarity (0-1)
)
```

**Recommendations:**
- `0.9` - Very strict (almost identical)
- `0.8` - **Recommended** (good balance)
- `0.7` - Permissive (more matches, some false positives)

### Request Timeout

```python
# backend/services.py
timeout_minutes = 30  # Auto-timeout after 30 min
```

### RAG Mode

```python
# Enable for complex questions
result = await kb_service.search(question, use_rag=True)
```
