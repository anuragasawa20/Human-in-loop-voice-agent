"""
Business logic services for the backend API.

Design Decision:
- Service layer separates business logic from API routes
- Each service handles one domain (requests, KB, notifications)
- Services are testable and reusable
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from google.cloud import firestore

from models import (
    RequestStatus,
    HelpRequestCreate,
    HelpRequestUpdate,
    KnowledgeEntryCreate,
    Priority,
)
from database import FirebaseClient

logger = logging.getLogger(__name__)


class HelpRequestService:
    """
    Service for managing help requests.

    Responsibilities:
    - CRUD operations for help requests
    - State machine enforcement
    - Timeout management
    """

    def __init__(self, db: FirebaseClient):
        self.db = db
        self.timeout_minutes = 30  # Configurable timeout

    async def create_request(self, data: HelpRequestCreate) -> dict:
        """
        Create a new help request.

        Design Decision:
        - Set timeout_at = created_at + 30 minutes
        - Default status = pending
        - Automatically timestamp

        Args:
            data: Help request creation data

        Returns:
            Created request with ID
        """
        now = datetime.utcnow()
        timeout_at = now + timedelta(minutes=self.timeout_minutes)

        request_data = {
            "caller_id": data.caller_id,
            "caller_name": data.caller_name,
            "question": data.question,
            "context": data.context,
            "call_session_id": data.call_session_id,
            "priority": data.priority.value,
            "status": RequestStatus.PENDING.value,
            "created_at": now,
            "updated_at": now,
            "timeout_at": timeout_at,
            "resolved_at": None,
            "supervisor_response": None,
            "supervisor_id": None,
        }

        doc_ref = self.db.collection("help_requests").document()
        doc_ref.set(request_data)

        logger.info(f"Created help request: {doc_ref.id}")

        return {"id": doc_ref.id, **request_data}

    async def get_request(self, request_id: str) -> Optional[dict]:
        """Get a help request by ID."""
        doc = self.db.collection("help_requests").document(request_id).get()

        if not doc.exists:
            return None

        return {"id": doc.id, **doc.to_dict()}

    async def list_requests(
        self, status: Optional[RequestStatus] = None, limit: int = 50
    ) -> List[dict]:
        """
        List help requests with optional filtering.

        Args:
            status: Filter by status
            limit: Maximum results

        Returns:
            List of help requests
        """
        query = self.db.collection("help_requests")

        if status:
            query = query.where("status", "==", status.value)

        query = query.order_by("created_at", direction=firestore.Query.DESCENDING)
        query = query.limit(limit)

        docs = query.stream()

        return [{"id": doc.id, **doc.to_dict()} for doc in docs]

    async def update_request(
        self, request_id: str, update_data: HelpRequestUpdate
    ) -> Optional[dict]:
        """
        Update a help request with supervisor response.

        Design Decision:
        - Transition to RESOLVED status
        - Set resolved_at timestamp
        - Validate state transitions

        Args:
            request_id: ID of request to update
            update_data: Update data

        Returns:
            Updated request or None if not found
        """
        doc_ref = self.db.collection("help_requests").document(request_id)
        doc = doc_ref.get()

        if not doc.exists:
            logger.warning(f"Request not found: {request_id}")
            return None

        current_data = doc.to_dict()
        current_status = current_data.get("status")

        # Validate state transition
        if current_status == RequestStatus.RESOLVED.value:
            logger.warning(f"Cannot update already resolved request: {request_id}")
            raise ValueError("Request already resolved")

        if current_status == RequestStatus.TIMEOUT.value:
            logger.warning(f"Cannot update timed out request: {request_id}")
            raise ValueError("Request timed out")

        # Update the request
        now = datetime.utcnow()
        update_fields = {
            "supervisor_response": update_data.supervisor_response,
            "supervisor_id": update_data.supervisor_id,
            "status": RequestStatus.RESOLVED.value,
            "resolved_at": now,
            "updated_at": now,
        }

        doc_ref.update(update_fields)

        logger.info(f"Updated help request: {request_id}")

        # Get updated document
        updated_doc = doc_ref.get()
        return {"id": updated_doc.id, **updated_doc.to_dict()}

    async def mark_in_progress(
        self, request_id: str, supervisor_id: str
    ) -> Optional[dict]:
        """
        Mark a request as in progress.

        Args:
            request_id: Request ID
            supervisor_id: Supervisor taking the request

        Returns:
            Updated request
        """
        doc_ref = self.db.collection("help_requests").document(request_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        doc_ref.update(
            {
                "status": RequestStatus.IN_PROGRESS.value,
                "supervisor_id": supervisor_id,
                "updated_at": datetime.utcnow(),
            }
        )

        logger.info(f"Marked request in progress: {request_id}")

        updated_doc = doc_ref.get()
        return {"id": updated_doc.id, **updated_doc.to_dict()}

    async def check_timeouts(self) -> List[str]:
        """
        Check for timed out requests and mark them.

        Design Decision:
        - Run periodically (every 5 minutes)
        - Mark requests past timeout_at as TIMEOUT
        - Return list of timed out request IDs

        Returns:
            List of request IDs that were marked timeout
        """
        now = datetime.utcnow()

        # Find requests past timeout that aren't resolved
        query = (
            self.db.collection("help_requests")
            .where("timeout_at", "<=", now)
            .where(
                "status",
                "in",
                [RequestStatus.PENDING.value, RequestStatus.IN_PROGRESS.value],
            )
        )

        timed_out_ids = []

        for doc in query.stream():
            doc_ref = self.db.collection("help_requests").document(doc.id)
            doc_ref.update({"status": RequestStatus.TIMEOUT.value, "updated_at": now})
            timed_out_ids.append(doc.id)
            logger.info(f"Marked request as timeout: {doc.id}")

        return timed_out_ids


class KnowledgeBaseService:
    """
    Service for managing the knowledge base.

    Responsibilities:
    - CRUD operations for KB entries
    - Duplicate detection
    - Auto-learning from resolved requests
    """

    def __init__(self, db: FirebaseClient):
        self.db = db

    def normalize_question(self, question: str) -> str:
        """Normalize question for consistent matching."""
        return question.lower().strip().rstrip("?!.")

    async def create_entry(self, data: KnowledgeEntryCreate) -> dict:
        """
        Create a new knowledge base entry.

        Args:
            data: KB entry data

        Returns:
            Created entry with ID
        """
        normalized_q = self.normalize_question(data.question)

        entry_data = {
            "question": data.question,
            "question_normalized": normalized_q,
            "answer": data.answer,
            "category": data.category,
            "confidence": data.confidence,
            "source": data.source.value,
            "source_request_id": data.source_request_id,
            "usage_count": 0,
            "created_at": datetime.utcnow(),
            "last_used_at": None,
        }

        doc_ref = self.db.collection("knowledge_base").document()
        doc_ref.set(entry_data)

        logger.info(f"Created KB entry: {doc_ref.id}")

        return {"id": doc_ref.id, **entry_data}

    async def find_duplicate(
        self, question: str, threshold: float = 0.85
    ) -> Optional[dict]:
        """
        Find duplicate question in KB.

        Design Decision:
        - MVP: Simple exact match on normalized question
        - Future: Upgrade to semantic similarity with embeddings

        Args:
            question: Question to check
            threshold: Similarity threshold (0-1)

        Returns:
            Existing entry if duplicate found, None otherwise
        """
        normalized_q = self.normalize_question(question)

        # Exact match for MVP
        query = (
            self.db.collection("knowledge_base")
            .where("question_normalized", "==", normalized_q)
            .limit(1)
        )

        for doc in query.stream():
            logger.info(f"Found duplicate KB entry: {doc.id}")
            return {"id": doc.id, **doc.to_dict()}

        return None

    async def update_from_resolution(
        self, question: str, answer: str, source_request_id: str
    ) -> dict:
        """
        Auto-update KB from supervisor resolution.

        Design Decision:
        - If duplicate exists: Update answer and increase confidence
        - If new: Create entry with high confidence (0.9)

        Args:
            question: The question
            answer: Supervisor's answer
            source_request_id: ID of the help request

        Returns:
            Created or updated KB entry
        """
        logger.info(f"Auto-updating KB from request {source_request_id}")

        # Check for duplicate
        duplicate = await self.find_duplicate(question)

        if duplicate:
            # Update existing entry
            doc_ref = self.db.collection("knowledge_base").document(duplicate["id"])

            # Increase confidence slightly (up to 1.0)
            new_confidence = min(duplicate.get("confidence", 0.9) + 0.05, 1.0)

            doc_ref.update(
                {
                    "answer": answer,  # Override with new answer
                    "confidence": new_confidence,
                    "usage_count": firestore.Increment(1),
                    "last_used_at": datetime.utcnow(),
                }
            )

            logger.info(f"Updated existing KB entry: {duplicate['id']}")

            updated_doc = doc_ref.get()
            return {"id": updated_doc.id, **updated_doc.to_dict()}
        else:
            # Create new entry
            from models import KBSource

            entry_data = KnowledgeEntryCreate(
                question=question,
                answer=answer,
                confidence=0.9,  # High confidence from supervisor
                source=KBSource.SUPERVISOR_ANSWER,
                source_request_id=source_request_id,
                category="learned",
            )

            return await self.create_entry(entry_data)

    async def list_entries(
        self, category: Optional[str] = None, limit: int = 100
    ) -> List[dict]:
        """List KB entries with optional filtering."""
        query = self.db.collection("knowledge_base")

        if category:
            query = query.where("category", "==", category)

        query = query.order_by("confidence", direction=firestore.Query.DESCENDING)
        query = query.limit(limit)

        docs = query.stream()

        return [{"id": doc.id, **doc.to_dict()} for doc in docs]


class NotificationService:
    """
    Service for customer notifications.

    Responsibilities:
    - Send notifications to customers
    - Log notification attempts
    - Handle retries

    Design Decision:
    - MVP: Console log simulation
    - Easy to swap for real SMS/call later
    """

    def __init__(self, db: FirebaseClient):
        self.db = db

    async def notify_customer(
        self, recipient: str, message: str, request_id: str
    ) -> bool:
        """
        Send notification to customer.

        Design Decision:
        - MVP: Print to console (simulated SMS)
        - Production: Integrate with Twilio

        Args:
            recipient: Phone number
            message: Notification message
            request_id: Related help request

        Returns:
            True if successful
        """
        logger.info(f"Sending notification to {recipient}")

        # Simulated SMS output
        print("\n" + "=" * 60)
        print(f"📱 SIMULATED SMS TO: {recipient}")
        print("=" * 60)
        print(f"\n{message}\n")
        print("- Priyanka's Beauty Salon")
        print("=" * 60 + "\n")

        # Log the notification
        notification_data = {
            "recipient": recipient,
            "message": message,
            "request_id": request_id,
            "sent_at": datetime.utcnow(),
            "method": "simulated_sms",
            "status": "sent",
        }

        self.db.collection("notifications").add(notification_data)

        return True
