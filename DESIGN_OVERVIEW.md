# Human-in-the-Loop AI Agent - Design Overview

## Project Goal
Build a system where an AI agent can escalate to human supervisors when uncertain, get answers, follow up with customers, and automatically update its knowledge base.

---

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        PHONE CALL FLOW                          │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LiveKit AI Agent                             │
│  - STT (Speech-to-Text)                                         │
│  - LLM with Salon Context                                       │
│  - TTS (Text-to-Speech)                                         │
│  - Knowledge Base Lookup                                        │
│  - request_help() Function                                      │
└─────────────────────────────────────────────────────────────────┘
                    │                           │
                    │ Known Answer              │ Unknown → Escalate
                    ▼                           ▼
            ┌──────────────┐         ┌──────────────────────┐
            │   Respond    │         │  Create Help Request │
            │  to Caller   │         │   in Database        │
            └──────────────┘         └──────────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────────┐
                                    │ Notify Supervisor   │
                                    │ (Console/Webhook)   │
                                    └─────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Supervisor UI (Web Dashboard)                │
│  - View Pending Requests                                        │
│  - Submit Answers                                               │
│  - View Resolved History                                        │
│  - View Learned Answers                                         │
└─────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────────┐
                                    │ Supervisor Responds │
                                    └─────────────────────┘
                                              │
                                              ▼
                    ┌─────────────────────────┴─────────────────────────┐
                    │                                                   │
                    ▼                                                   ▼
        ┌────────────────────────┐                    ┌────────────────────────┐
        │  Follow-up Customer    │                    │ Update Knowledge Base  │
        │  (SMS/Call Simulation) │                    │  (Auto-learn)          │
        └────────────────────────┘                    └────────────────────────┘
```

---

## Database Schema Design

### Collection/Table: `help_requests`

```javascript
{
  id: string (UUID),
  caller_id: string,              // Phone number or session ID
  caller_name: string,            // Optional
  question: string,               // What the caller asked
  context: string,                // Conversation context
  call_session_id: string,        // Link to original call
  status: enum [                  // Lifecycle state
    'pending',
    'in_progress',
    'resolved',
    'timeout'
  ],
  created_at: timestamp,
  updated_at: timestamp,
  timeout_at: timestamp,          // Auto-resolve after 30 min
  resolved_at: timestamp,
  supervisor_response: string,    // Answer from supervisor
  supervisor_id: string,          // Who answered
  priority: enum ['low', 'medium', 'high']
}
```

### Collection/Table: `knowledge_base`

```javascript
{
  id: string (UUID),
  question: string,               // Normalized question
  answer: string,                 // Learned answer
  source: enum [                  // Where it came from
    'initial_prompt',
    'supervisor_answer',
    'manual_entry'
  ],
  source_request_id: string,      // Link to help request
  category: string,               // 'hours', 'services', 'pricing'
  confidence: number,             // 0-1 score
  usage_count: number,            // How many times used
  last_used_at: timestamp,
  created_at: timestamp,
  created_by: string,
  tags: array[string]
}
```

### Collection/Table: `call_sessions`

```javascript
{
  id: string (UUID),
  caller_id: string,
  caller_phone: string,
  started_at: timestamp,
  ended_at: timestamp,
  duration_seconds: number,
  transcript: string,             // Full conversation
  help_requested: boolean,
  help_request_ids: array[string],
  resolved_during_call: boolean,
  status: enum ['active', 'completed', 'failed']
}
```

---

## API Design

### Backend REST API Endpoints

```
POST   /api/help-requests          Create new help request from AI
GET    /api/help-requests          Get all requests (with filters)
GET    /api/help-requests/:id      Get specific request
PATCH  /api/help-requests/:id      Update request (supervisor response)
DELETE /api/help-requests/:id      Cancel request

GET    /api/knowledge-base         Get all knowledge entries
POST   /api/knowledge-base         Add manual entry
PATCH  /api/knowledge-base/:id     Update entry
DELETE /api/knowledge-base/:id     Remove entry

GET    /api/call-sessions          Get call history
GET    /api/call-sessions/:id      Get specific call details

POST   /api/notifications/send     Simulate SMS/call follow-up
```

### Request/Response Examples

#### POST /api/help-requests
```json
// Request
{
  "caller_id": "+1234567890",
  "caller_name": "Jane Doe",
  "question": "Do you offer bridal packages?",
  "context": "Caller asked about services for wedding preparation",
  "call_session_id": "session-123",
  "priority": "medium"
}

// Response
{
  "id": "req-456",
  "status": "pending",
  "created_at": "2025-11-05T10:30:00Z",
  "timeout_at": "2025-11-05T11:00:00Z"
}
```

#### PATCH /api/help-requests/:id
```json
// Request
{
  "supervisor_response": "Yes, we offer a full bridal package including hair, makeup, and nails for $350. It includes a trial session two weeks before the wedding.",
  "supervisor_id": "sup-789"
}

// Response
{
  "id": "req-456",
  "status": "resolved",
  "resolved_at": "2025-11-05T10:45:00Z",
  "knowledge_base_updated": true,
  "customer_notified": true
}
```

---

## Request Lifecycle State Machine

```
┌─────────┐     Supervisor      ┌─────────────┐     Response      ┌──────────┐
│ PENDING │ ──── starts work ───►│ IN_PROGRESS │──── submitted ────►│ RESOLVED │
└─────────┘                      └─────────────┘                   └──────────┘
     │                                  │
     │                                  │
     │ timeout (30 min)                 │ timeout (30 min)
     │                                  │
     ▼                                  ▼
┌─────────┐                        ┌─────────┐
│ TIMEOUT │                        │ TIMEOUT │
└─────────┘                        └─────────┘
```

**States:**
- **PENDING**: Waiting for supervisor to see it
- **IN_PROGRESS**: Supervisor is working on it
- **RESOLVED**: Answer provided, customer notified
- **TIMEOUT**: No response within timeout window

---

## AI Agent Design

### Core Prompt Structure

```python
salon_context = """
You are the AI receptionist for "Priyanka's Beauty Salon".

BUSINESS INFORMATION:
- Hours: Mon-Sat 9am-7pm, Closed Sunday
- Services: Haircuts ($50), Color ($120), Highlights ($150), Manicure ($35), Pedicure ($45)
- Booking: Call required, no online booking
- Cancellation: 24 hour notice required
- Location: 123 Main St, Springfield

YOUR BEHAVIOR:
1. Be friendly, professional, and helpful
2. Answer questions you know confidently
3. If you DON'T KNOW or are UNCERTAIN, say: "Let me check with my supervisor and get back to you"
4. Use the request_help() function when uncertain
5. Check the knowledge base before escalating

KNOWLEDGE BASE ACCESS:
You have access to learned answers from past interactions. Always check these first.
"""
```

### AI Function/Tool: `request_help`

```python
def request_help(question: str, context: str) -> dict:
    """
    Called by AI when it doesn't know the answer.
    
    Args:
        question: The specific question the caller asked
        context: Surrounding conversation context
    
    Returns:
        {
            "request_id": "req-123",
            "message": "I've escalated this to my supervisor. We'll get back to you shortly.",
            "estimated_response_time": "within 30 minutes"
        }
    """
    # Create help request in database
    # Notify supervisor
    # Return acknowledgment message
```

### Knowledge Base Integration

```python
# Before responding, AI checks learned answers
def check_knowledge_base(question: str) -> Optional[str]:
    # Semantic search in knowledge_base collection
    # Return answer if confidence > 0.8
    # Otherwise return None (escalate)
```

---

## Technology Stack Recommendations

### Option 1: Firebase + Python (Fastest)
- **Database**: Firebase Firestore (real-time, easy setup)
- **AI Agent**: Python + LiveKit Agents SDK
- **Backend**: Flask/FastAPI + Firebase Admin SDK
- **Frontend**: React + Firebase SDK (real-time updates)
- **Hosting**: Firebase Hosting (frontend), Cloud Run (backend)

### Option 2: DynamoDB + Node.js
- **Database**: AWS DynamoDB
- **AI Agent**: Python + LiveKit Agents SDK
- **Backend**: Express.js + AWS SDK
- **Frontend**: Next.js + DynamoDB API
- **Hosting**: AWS Amplify

### Option 3: Supabase (Modern Alternative)
- **Database**: Supabase (Postgres + real-time)
- **AI Agent**: Python + LiveKit Agents SDK
- **Backend**: Supabase Edge Functions
- **Frontend**: React + Supabase Client
- **Hosting**: Vercel

**Recommendation**: **Firebase** for fastest development + real-time updates

---

## Key Design Decisions

### 1. Database Choice: Firebase Firestore

**Why?**
- Real-time updates for supervisor UI (no polling needed)
- Simple setup, generous free tier
- Built-in authentication if needed later
- Easy to scale from 10/day to 1000/day

**Trade-offs:**
- Vendor lock-in (mitigated by clean data models)
- Less flexible queries than SQL

### 2. Request Lifecycle Management

**Timeout Strategy:**
- Set `timeout_at` = `created_at` + 30 minutes
- Background job checks every 5 minutes
- Mark as 'timeout' if no response
- Option: Send reminder to supervisor at 20 minutes

**Why 30 minutes?**
- Balance between customer patience and supervisor flexibility
- Can be made configurable per priority

### 3. Knowledge Base Auto-Update

**Strategy:**
```python
def update_knowledge_base(help_request):
    # Extract question-answer pair
    entry = {
        "question": normalize_question(help_request.question),
        "answer": help_request.supervisor_response,
        "source": "supervisor_answer",
        "source_request_id": help_request.id,
        "confidence": 0.9,  # High because it's from supervisor
        "created_at": now()
    }
    
    # Check for duplicates (semantic similarity)
    similar = find_similar_questions(entry.question, threshold=0.85)
    
    if similar:
        # Update existing entry (increase confidence, update answer)
        update_existing(similar.id, entry)
    else:
        # Create new entry
        create_new(entry)
```

**Preventing Duplicates:**
- Use simple text similarity (cosine similarity on embeddings)
- Or use LLM to determine if questions are the same
- Threshold: 85% similarity = same question

### 4. Modularization Strategy

```
project/
├── agent/                  # AI Agent (LiveKit)
│   ├── agent.py           # Main agent logic
│   ├── tools.py           # request_help function
│   ├── knowledge.py       # KB lookup
│   └── prompt.py          # System prompt
│
├── backend/               # API Server
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
├── frontend/              # Supervisor UI
│   ├── components/
│   │   ├── PendingRequests.tsx
│   │   ├── ResolvedHistory.tsx
│   │   └── KnowledgeBase.tsx
│   ├── pages/
│   │   └── dashboard.tsx
│   └── services/
│       └── api.ts
│
└── shared/               # Shared utilities
    ├── types.ts
    └── constants.ts
```

### 5. Scaling Considerations (10/day → 1000/day)

#### Current Design (10/day): ✅
- Direct API calls
- Single database instance
- Simple polling/real-time updates

#### At 100/day: 
- Add caching layer (Redis) for knowledge base
- Implement rate limiting
- Add monitoring (Sentry, DataDog)

#### At 1000/day:
- Add message queue (RabbitMQ, AWS SQS) for help requests
- Separate notification service (async workers)
- Scale backend horizontally (multiple instances)
- Add CDN for frontend
- Implement database indexes on `status`, `created_at`

**Current design supports 1000/day** with:
- Proper indexing
- Async notification handling
- Caching frequently accessed KB entries

### 6. Error Handling Strategy

```python
# Database Operations
try:
    result = db.create_help_request(data)
except DatabaseError as e:
    logger.error(f"DB error: {e}")
    # Fallback: Store in local queue, retry later
    queue.add(data)
    return {"status": "queued", "message": "Request received"}

# AI Agent Failures
try:
    response = ai_agent.generate_response(question)
except AIError as e:
    logger.error(f"AI error: {e}")
    # Fallback: Direct to supervisor
    return auto_escalate(question)

# Notification Failures
try:
    send_notification(customer, message)
except NotificationError as e:
    logger.error(f"Notification error: {e}")
    # Retry with exponential backoff
    retry_queue.add(notification_task, retry_in=60)
```

---

## Follow-up System Design

### Option 1: Console Log (Simplest)
```python
def notify_customer(caller_id, question, answer):
    print(f"""
    ═══════════════════════════════════════
    📱 SIMULATED SMS TO: {caller_id}
    
    Hi! Regarding your question:
    "{question}"
    
    Answer: {answer}
    
    - Priyanka's Beauty Salon
    ═══════════════════════════════════════
    """)
```

### Option 2: Webhook Simulation
```python
def notify_customer(caller_id, question, answer):
    # POST to mock webhook endpoint
    requests.post("http://localhost:3001/webhook/sms", json={
        "to": caller_id,
        "message": f"Hi! Regarding your question: '{question}'\n\nAnswer: {answer}",
        "from": "Bella's Salon"
    })
```

### Option 3: Real Twilio Integration (Optional)
```python
from twilio.rest import Client

def notify_customer(caller_id, question, answer):
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=f"Hi! Regarding '{question}': {answer} - Bella's Salon",
        from_=twilio_number,
        to=caller_id
    )
```

---

## Testing Strategy

### End-to-End Test Flow

```python
def test_full_escalation_flow():
    # 1. Simulate AI agent receiving unknown question
    response = agent.receive_call({
        "caller_id": "+1234567890",
        "question": "Do you offer hair extensions?"
    })
    
    assert response.escalated == True
    assert "supervisor" in response.message.lower()
    
    # 2. Verify help request created
    request = db.get_latest_help_request()
    assert request.status == "pending"
    assert request.question == "Do you offer hair extensions?"
    
    # 3. Simulate supervisor responding
    supervisor_response = api.update_help_request(request.id, {
        "supervisor_response": "Yes, we offer tape-in and clip-in extensions starting at $200",
        "supervisor_id": "test-supervisor"
    })
    
    assert supervisor_response.status == "resolved"
    
    # 4. Verify knowledge base updated
    kb_entry = db.search_knowledge_base("hair extensions")
    assert kb_entry is not None
    assert "$200" in kb_entry.answer
    
    # 5. Verify customer notified
    notification = notification_service.get_latest()
    assert notification.recipient == "+1234567890"
    assert "hair extensions" in notification.message.lower()
```

---

## Phase 2 Preview: Live Transfer

### Design for Future Live Transfer Feature

```python
# When supervisor is available during call
if supervisor_available() and caller_on_line():
    # Option 1: Put on hold, transfer
    agent.say("Let me transfer you to my supervisor right away.")
    agent.hold_music()
    supervisor.ring()
    agent.transfer(supervisor)
    
    # Option 2: Conference call
    agent.say("I'll bring my supervisor into this call.")
    agent.conference_add(supervisor)
else:
    # Fallback to text-based flow
    agent.say("Let me check with my supervisor and get back to you.")
    create_help_request()
```

**Implementation Needs:**
- Supervisor availability status
- Real-time supervisor notification (push, not pull)
- Call transfer capability (LiveKit supports this)
- Supervisor phone/softphone integration

---

## Demo Video Outline

### Script (5-7 minutes)

1. **Introduction (30s)**
   - "I built a human-in-the-loop system for AI agents..."
   - Show architecture diagram

2. **AI Agent Demo (90s)**
   - Receive simulated call
   - Answer known question (hours, pricing)
   - Ask unknown question (trigger escalation)
   - Show graceful response

3. **Database & Backend (60s)**
   - Show help request created in database
   - Show supervisor notification (console/webhook)
   - Walk through API structure

4. **Supervisor UI (90s)**
   - Open dashboard
   - Show pending request
   - Submit answer
   - Show resolved history
   - Show knowledge base updated

5. **Follow-up System (45s)**
   - Show customer notification (simulated)
   - Verify knowledge base has new entry

6. **Design Decisions (90s)**
   - Why Firebase? (real-time, simple)
   - Schema design rationale
   - Timeout handling
   - Modularization approach

7. **Future Improvements (45s)**
   - Better semantic search for KB
   - Real Twilio integration
   - Supervisor mobile app
   - Analytics dashboard
   - Phase 2: Live transfer

---

## README Outline

```markdown
# Human-in-the-Loop AI Agent System

## Overview
AI receptionist that escalates to humans when uncertain, learns from answers, and follows up automatically.

## Architecture
[Include simplified diagram]

## Tech Stack
- AI Agent: LiveKit Agents (Python)
- Database: Firebase Firestore
- Backend: FastAPI
- Frontend: React + Firebase

## Setup Instructions
[Step-by-step with commands]

## Design Decisions
### Database Schema
[Explain choices]

### Request Lifecycle
[State machine diagram]

### Scaling Strategy
[Current design → 1000/day]

## Demo
[Link to video]

## Future Improvements
- Semantic search for KB
- Real telephony integration
- Live call transfer (Phase 2)
```

---

## Timeline & Priorities

### Day 1-2: Foundation (High Priority)
- ✅ Set up project structure
- ✅ Initialize Firebase
- ✅ Create database schema
- ✅ Basic LiveKit agent

### Day 3-4: Core Features (High Priority)
- ✅ Help request system
- ✅ Supervisor UI (basic)
- ✅ API endpoints
- ✅ Follow-up simulation

### Day 5-6: Knowledge Base & Polish (Medium Priority)
- ✅ KB auto-update
- ✅ Request lifecycle
- ✅ Error handling
- ✅ UI improvements

### Day 7: Documentation & Demo (High Priority)
- ✅ README with design notes
- ✅ Demo video
- ✅ Final testing

---

## Success Criteria

### Must Have ✅
- AI agent receives calls and responds
- AI escalates when uncertain
- Help requests stored in database
- Supervisor can view and respond
- Customer gets notified (simulated)
- Knowledge base updates automatically

### Should Have 🎯
- Clean, modular code structure
- Proper error handling
- Request timeout handling
- Real-time UI updates
- Good documentation

### Nice to Have ⭐
- Semantic question matching
- Request priority system
- Analytics/metrics
- Deployment to cloud
- Real Twilio integration

---

## Questions to Consider

1. **How to handle multiple supervisors?**
   - Round-robin assignment
   - Skill-based routing
   - First-come-first-served

2. **What if customer doesn't answer follow-up?**
   - Retry logic
   - Mark as "attempted"
   - Email fallback

3. **How to handle conflicting KB entries?**
   - Timestamp priority (newer wins)
   - Confidence scoring
   - Manual review queue

4. **Security considerations?**
   - API authentication (JWT tokens)
   - Supervisor login
   - Rate limiting
   - Input validation

---

This design prioritizes **clarity, modularity, and scalability** while being achievable in the given timeline. Focus on core features first, then polish.

