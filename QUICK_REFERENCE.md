# Quick Reference Guide

## 🎯 Project Goal
Build an AI agent that escalates to humans when uncertain, learns from answers, and follows up with customers.

---

## 🏗️ System Architecture (One View)

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CUSTOMER CALLS                             │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       LiveKit AI Agent                              │
│  • Speech-to-Text (AssemblyAI)                                      │
│  • LLM (OpenAI GPT-4.1 mini)                                        │
│  • Text-to-Speech (Cartesia Sonic-3)                                │
│  • Knowledge Base Lookup → Check if question is known              │
│  • request_help() Tool → Escalate if unknown                        │
└─────────────────────────────────────────────────────────────────────┘
          │                                          │
    Known Answer                              Unknown → Escalate
          │                                          │
          ▼                                          ▼
   ┌──────────────┐                    ┌──────────────────────────────┐
   │   Respond    │                    │  Create Help Request (DB)    │
   │  to Caller   │                    │  Status: pending             │
   └──────────────┘                    │  Timeout: created_at + 30min │
                                       └──────────────────────────────┘
                                                     │
                                                     ▼
                                       ┌──────────────────────────────┐
                                       │  Notify Supervisor           │
                                       │  (Console/Dashboard)         │
                                       └──────────────────────────────┘
                                                     │
                                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Supervisor Dashboard (React)                     │
│  • View Pending Requests                                            │
│  • Submit Answers                                                   │
│  • View History                                                     │
│  • Manage Knowledge Base                                            │
└─────────────────────────────────────────────────────────────────────┘
                                                     │
                                                     ▼
                                       ┌──────────────────────────────┐
                                       │  Update Request              │
                                       │  Status: resolved            │
                                       │  Add supervisor_response     │
                                       └──────────────────────────────┘
                                                     │
                          ┌──────────────────────────┴──────────────────┐
                          ▼                                             ▼
            ┌──────────────────────────┐              ┌──────────────────────────┐
            │  Notify Customer         │              │  Update Knowledge Base   │
            │  (SMS/Call Simulation)   │              │  (Auto-learn)            │
            └──────────────────────────┘              └──────────────────────────┘
```

---

## 📊 Database Schema (Quick View)

### Collection: `help_requests`
```typescript
{
  id: string,
  caller_id: string,        // Phone number
  question: string,         // What they asked
  context: string,          // Conversation context
  
  status: "pending" | "in_progress" | "resolved" | "timeout",
  
  created_at: timestamp,
  timeout_at: timestamp,    // created_at + 30 min
  
  supervisor_response: string,
  supervisor_id: string
}
```

### Collection: `knowledge_base`
```typescript
{
  id: string,
  question: string,         // Normalized question
  answer: string,
  
  source: "initial_prompt" | "supervisor_answer" | "manual_entry",
  confidence: number,       // 0-1
  usage_count: number,
  
  category: string,         // "hours", "services", "pricing"
  created_at: timestamp
}
```

---

## 🔄 Request Lifecycle

```
PENDING ──start work──> IN_PROGRESS ──submit answer──> RESOLVED
   │                           │
   │ 30 min                    │ 30 min
   ▼                           ▼
TIMEOUT                    TIMEOUT
```

**States:**
- `pending`: Waiting for supervisor
- `in_progress`: Supervisor is working on it
- `resolved`: Answer provided, customer notified
- `timeout`: No response within 30 minutes

---

## 🛠️ Tech Stack

| Component | Technology | Why? |
|-----------|-----------|------|
| **AI Agent** | LiveKit Agents (Python) | Voice AI, handles calls |
| **STT** | AssemblyAI | Multi-language support |
| **LLM** | OpenAI GPT-4.1 mini | Fast, cost-effective |
| **TTS** | Cartesia Sonic-3 | Natural voice |
| **Database** | Firebase Firestore | Real-time updates |
| **Backend** | FastAPI (Python) | Async, fast, auto-docs |
| **Frontend** | React + Tailwind | Modern UI |
| **Hosting** | LiveKit Cloud | Agents deployment |

---

## 📁 Project Structure

```
project/
├── agent/                  # LiveKit AI Agent (Python)
│   ├── agent.py           # Main agent logic
│   ├── tools.py           # request_help() function
│   ├── knowledge.py       # KB lookup
│   ├── prompt.py          # System prompt
│   └── .env.local         # API keys
│
├── backend/               # API Server (FastAPI)
│   ├── main.py           # FastAPI app
│   ├── api/
│   │   ├── help_requests.py
│   │   ├── knowledge_base.py
│   │   └── notifications.py
│   ├── services/
│   │   ├── request_service.py
│   │   ├── kb_service.py
│   │   └── notification_service.py
│   ├── models/
│   │   ├── help_request.py
│   │   └── knowledge_entry.py
│   └── db/
│       └── firebase_client.py
│
├── frontend/              # Supervisor Dashboard (React)
│   ├── src/
│   │   ├── components/
│   │   │   ├── PendingRequests.tsx
│   │   │   ├── RequestCard.tsx
│   │   │   ├── ResponseModal.tsx
│   │   │   └── KnowledgeBase.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── App.tsx
│   └── package.json
│
└── shared/               # Shared types, constants
    ├── types.ts
    └── constants.ts
```

---

## 🚀 Setup Commands

### 1. Agent Setup
```bash
cd agent/
uv init --bare
uv add "livekit-agents[silero,turn-detector]~=1.2"
uv add "livekit-plugins-noise-cancellation~=0.2"
uv add "python-dotenv"

# Get LiveKit API keys
lk cloud auth
lk app env -w  # Saves to .env.local

# Download model files
uv run agent.py download-files

# Test in console mode
uv run agent.py console

# Run in dev mode (connects to LiveKit Cloud)
uv run agent.py dev
```

### 2. Backend Setup
```bash
cd backend/
uv init --bare
uv add "fastapi" "uvicorn[standard]" "firebase-admin" "python-dotenv"

# Create .env.local with Firebase credentials
# Run server
uvicorn main:app --reload
```

### 3. Frontend Setup
```bash
cd frontend/
npm create vite@latest . -- --template react-ts
npm install
npm install firebase tailwindcss

# Run dev server
npm run dev
```