"""
Knowledge Base service for the AI agent.
Handles searching and retrieving learned answers using semantic search.
"""

import logging
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeEntry:
    """Represents a knowledge base entry."""

    id: str
    question: str
    answer: str
    confidence: float
    category: str
    usage_count: int
    source: str
    created_at: datetime
    last_used_at: Optional[datetime] = None


class KnowledgeBaseService:
    """
    Service for managing and searching the knowledge base.

    Design Decision:
    - Uses semantic search with vector embeddings (upgraded from keyword matching)
    - OpenAI embeddings + ChromaDB for similarity search
    - RAG (Retrieval Augmented Generation) for complex questions
    - Confidence threshold ensures quality answers only

    Upgrade from MVP:
    - MVP used simple keyword matching
    - Production uses semantic search with embeddings
    - Handles similar questions even with different wording
    """

    def __init__(self, db_client=None, confidence_threshold: float = 0.8):
        """
        Initialize the knowledge base service.

        Args:
            db_client: Firebase database client
            confidence_threshold: Minimum confidence to return results (0-1)
        """
        self.db_client = db_client
        self.confidence_threshold = confidence_threshold
        self._cache = {}  # Simple in-memory cache for frequently accessed entries

        # Initialize vector store (lazy loading)
        self._vector_store = None
        self._rag_kb = None

        logger.info(
            f"KnowledgeBaseService initialized with confidence threshold: {confidence_threshold}"
        )
        logger.info("Semantic search enabled with vector embeddings")

    @property
    def vector_store(self):
        """Lazy load vector store."""
        if self._vector_store is None:
            try:
                from vector_store import VectorStore

                self._vector_store = VectorStore()
                logger.info("Vector store initialized")
            except Exception as e:
                logger.warning(f"Could not initialize vector store: {e}")
                logger.warning("Falling back to keyword matching")
        return self._vector_store

    @property
    def rag_kb(self):
        """Lazy load RAG knowledge base."""
        if self._rag_kb is None and self.vector_store is not None:
            try:
                from vector_store import RAGKnowledgeBase

                self._rag_kb = RAGKnowledgeBase(self.vector_store)
                logger.info("RAG knowledge base initialized")
            except Exception as e:
                logger.warning(f"Could not initialize RAG KB: {e}")
        return self._rag_kb

    def normalize_question(self, question: str) -> str:
        """
        Normalize question for consistent matching.

        Args:
            question: Raw question text

        Returns:
            Normalized question (lowercase, trimmed, no punctuation)
        """
        # Remove punctuation and normalize whitespace
        normalized = question.lower().strip()
        normalized = normalized.rstrip("?!.")
        return normalized

    async def search(
        self, question: str, use_rag: bool = False
    ) -> Optional[KnowledgeEntry]:
        """
        Search knowledge base for an answer using semantic search.

        Design Decision:
        - Semantic search using vector embeddings (production)
        - Falls back to keyword matching if vector store unavailable
        - Optional RAG mode for complex questions

        Args:
            question: The question to search for
            use_rag: Whether to use RAG (Retrieval Augmented Generation)

        Returns:
            KnowledgeEntry if found with sufficient confidence, None otherwise
        """
        normalized_q = self.normalize_question(question)

        logger.info(f"Searching KB for: '{normalized_q}' (semantic search)")

        # Check cache first
        if normalized_q in self._cache:
            cached_entry = self._cache[normalized_q]
            if cached_entry.confidence >= self.confidence_threshold:
                logger.info(f"Cache hit: {cached_entry.id}")
                await self._increment_usage(cached_entry.id)
                return cached_entry

        # Try semantic search with vector store
        if self.vector_store is not None:
            try:
                if use_rag and self.rag_kb is not None:
                    # Use RAG for more complex answers
                    result = await self.rag_kb.answer_with_context(
                        question=question,
                        similarity_threshold=self.confidence_threshold,
                    )

                    if result:
                        # Convert RAG result to KnowledgeEntry
                        entry = KnowledgeEntry(
                            id=f"rag-{hash(question)}",
                            question=question,
                            answer=result["answer"],
                            confidence=result["confidence"],
                            category="rag-generated",
                            usage_count=0,
                            source=result["method"],
                            created_at=datetime.now(),
                        )
                        logger.info(
                            f"RAG answer generated (confidence: {entry.confidence})"
                        )
                        return entry
                else:
                    # Direct semantic search
                    results = self.vector_store.search(
                        query=question,
                        n_results=1,
                        similarity_threshold=self.confidence_threshold,
                    )

                    if results:
                        result = results[0]
                        entry = KnowledgeEntry(
                            id=result["id"],
                            question=result["question"],
                            answer=result["answer"],
                            confidence=result["similarity"],
                            category=result.get("category", "general"),
                            usage_count=result.get("metadata", {}).get(
                                "usage_count", 0
                            ),
                            source="semantic_search",
                            created_at=datetime.now(),
                        )

                        # Cache the result
                        self._cache[normalized_q] = entry

                        logger.info(
                            f"Semantic search hit: {entry.id} "
                            f"(similarity: {entry.confidence:.2f})"
                        )

                        # Increment usage counter
                        await self._increment_usage(entry.id)

                        return entry

            except Exception as e:
                logger.error(f"Error in semantic search: {e}")
                logger.info("Falling back to keyword matching")

        # Fallback to keyword matching if vector store unavailable
        return await self._keyword_search(normalized_q)

    async def _keyword_search(self, normalized_q: str) -> Optional[KnowledgeEntry]:
        """
        Fallback keyword search (original MVP implementation).

        Args:
            normalized_q: Normalized question

        Returns:
            KnowledgeEntry or None
        """
        # If no DB client, return None (will be used for testing)
        if not self.db_client:
            logger.warning("No DB client available, returning None")
            return None

        try:
            # Search database with exact match
            results = (
                self.db_client.collection("knowledge_base")
                .where("question_normalized", "==", normalized_q)
                .where("confidence", ">=", self.confidence_threshold)
                .order_by("confidence", direction="DESCENDING")
                .limit(1)
                .stream()
            )

            for doc in results:
                data = doc.to_dict()
                entry = KnowledgeEntry(
                    id=doc.id,
                    question=data["question"],
                    answer=data["answer"],
                    confidence=data["confidence"],
                    category=data.get("category", "general"),
                    usage_count=data.get("usage_count", 0),
                    source=data.get("source", "unknown"),
                    created_at=data["created_at"],
                    last_used_at=data.get("last_used_at"),
                )

                # Cache the result
                self._cache[normalized_q] = entry

                logger.info(
                    f"Keyword match: {entry.id} (confidence: {entry.confidence})"
                )

                # Increment usage counter
                await self._increment_usage(entry.id)

                return entry

            logger.info("No KB entry found above confidence threshold")
            return None

        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return None

    async def _increment_usage(self, entry_id: str) -> None:
        """
        Increment usage counter for a KB entry.

        Args:
            entry_id: ID of the KB entry
        """
        if not self.db_client:
            return

        try:
            from google.cloud import firestore

            doc_ref = self.db_client.collection("knowledge_base").document(entry_id)
            doc_ref.update(
                {"usage_count": firestore.Increment(1), "last_used_at": datetime.now()}
            )
        except Exception as e:
            logger.warning(f"Failed to increment usage for {entry_id}: {e}")

    async def add_entry(
        self,
        question: str,
        answer: str,
        confidence: float = 0.9,
        category: str = "general",
        source: str = "manual",
    ) -> str:
        """
        Add a new entry to the knowledge base (both Firebase and vector store).

        Args:
            question: The question
            answer: The answer
            confidence: Confidence score (0-1)
            category: Category (hours, services, pricing, etc.)
            source: Source of the entry

        Returns:
            ID of the created entry
        """
        if not self.db_client:
            raise ValueError("Cannot add entry without DB client")

        normalized_q = self.normalize_question(question)

        entry_data = {
            "question": question,
            "question_normalized": normalized_q,
            "answer": answer,
            "confidence": confidence,
            "category": category,
            "source": source,
            "usage_count": 0,
            "created_at": datetime.now(),
            "last_used_at": None,
        }

        doc_ref = self.db_client.collection("knowledge_base").add(entry_data)
        entry_id = doc_ref[1].id

        logger.info(f"Added KB entry to Firebase: {entry_id}")

        # Also add to vector store
        if self.vector_store is not None:
            try:
                self.vector_store.add_entry(
                    entry_id=entry_id,
                    question=question,
                    answer=answer,
                    metadata={
                        "category": category,
                        "confidence": confidence,
                        "source": source,
                        "usage_count": 0,
                    },
                )
                logger.info(f"Added KB entry to vector store: {entry_id}")
            except Exception as e:
                logger.warning(f"Failed to add to vector store: {e}")

        # Clear cache to force refresh
        self._cache.clear()

        return entry_id

    async def seed_initial_data(self) -> None:
        """
        Seed the knowledge base with initial salon information.

        Design Decision:
        - Include only information that rarely changes
        - High confidence (1.0) for official business information
        - Categorized for better organization
        - Also populates vector store for semantic search
        """
        if not self.db_client:
            logger.warning("Cannot seed data without DB client")
            return

        initial_entries = [
            {
                "question": "What are your hours?",
                "answer": "We're open Monday through Saturday from 9 AM to 7 PM. We're closed on Sundays.",
                "category": "hours",
                "confidence": 1.0,
                "source": "initial_prompt",
            },
            {
                "question": "What time do you open?",
                "answer": "We open at 9 AM Monday through Saturday.",
                "category": "hours",
                "confidence": 1.0,
                "source": "initial_prompt",
            },
            {
                "question": "What time do you close?",
                "answer": "We close at 7 PM Monday through Saturday. We're closed on Sundays.",
                "category": "hours",
                "confidence": 1.0,
                "source": "initial_prompt",
            },
            {
                "question": "How much is a haircut?",
                "answer": "A haircut is $50, which includes a wash and style.",
                "category": "pricing",
                "confidence": 1.0,
                "source": "initial_prompt",
            },
            {
                "question": "What services do you offer?",
                "answer": "We offer haircuts ($50), full color ($120), full highlights ($150), partial highlights ($100), manicures ($35), and pedicures ($45).",
                "category": "services",
                "confidence": 1.0,
                "source": "initial_prompt",
            },
            {
                "question": "Where are you located?",
                "answer": "We're located at 123 Main St in Springfield.",
                "category": "location",
                "confidence": 1.0,
                "source": "initial_prompt",
            },
            {
                "question": "Do you accept credit cards?",
                "answer": "Yes, we accept cash, credit cards, and debit cards.",
                "category": "payment",
                "confidence": 1.0,
                "source": "initial_prompt",
            },
            {
                "question": "What is your cancellation policy?",
                "answer": "We require 24-hour notice for cancellations. There is a $25 no-show fee.",
                "category": "policy",
                "confidence": 1.0,
                "source": "initial_prompt",
            },
        ]

        logger.info("Seeding knowledge base with initial data...")

        for entry in initial_entries:
            await self.add_entry(
                question=entry["question"],
                answer=entry["answer"],
                confidence=entry["confidence"],
                category=entry["category"],
                source=entry["source"],
            )

        logger.info(f"Successfully seeded {len(initial_entries)} KB entries")

    async def sync_to_vector_store(self) -> None:
        """
        Sync all Firebase KB entries to vector store.

        Design Decision:
        - Called on startup to ensure vector store is up to date
        - Also called periodically to catch any updates
        """
        if not self.db_client or self.vector_store is None:
            logger.warning("Cannot sync without DB client and vector store")
            return

        logger.info("Syncing Firebase KB to vector store...")

        try:
            # Get all KB entries from Firebase
            docs = self.db_client.collection("knowledge_base").stream()

            entries = []
            for doc in docs:
                data = doc.to_dict()
                entries.append(
                    {
                        "id": doc.id,
                        "question": data["question"],
                        "answer": data["answer"],
                        "category": data.get("category", "general"),
                        "confidence": data.get("confidence", 0.9),
                        "source": data.get("source", "unknown"),
                        "usage_count": data.get("usage_count", 0),
                    }
                )

            # Sync to vector store
            self.vector_store.sync_from_firebase(entries)

            logger.info(f"Successfully synced {len(entries)} entries to vector store")

        except Exception as e:
            logger.error(f"Error syncing to vector store: {e}")
