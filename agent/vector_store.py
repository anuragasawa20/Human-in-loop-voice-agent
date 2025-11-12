"""
Vector store for semantic search in knowledge base.

Design Decision:
- Use OpenAI embeddings (text-embedding-3-small) for high quality
- ChromaDB as vector database (lightweight, no server needed)
- Cosine similarity for semantic matching
- Configurable similarity threshold

Future Upgrades:
- Switch to Pinecone for production scale
- Use sentence-transformers for lower cost
- Add metadata filtering
"""

import logging
from typing import List, Optional, Dict, Any
import os
from datetime import datetime

import chromadb
from chromadb.config import Settings
from openai import OpenAI

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Vector store for semantic search using embeddings.

    Design Decision:
    - OpenAI embeddings for quality (768 dimensions)
    - ChromaDB for local development (easy setup)
    - Can switch to Pinecone for production scale
    """

    def __init__(
        self,
        collection_name: str = "knowledge_base",
        persist_directory: str = "./chroma_db",
    ):
        """
        Initialize vector store.

        Args:
            collection_name: Name of the collection
            persist_directory: Where to store the database
        """
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding_model = "text-embedding-3-small"

        # Initialize ChromaDB
        self.chroma_client = chromadb.Client(
            Settings(persist_directory=persist_directory, anonymized_telemetry=False)
        )

        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},  # Use cosine similarity
        )

        logger.info(f"VectorStore initialized with {self.collection.count()} entries")

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (768 dimensions)
        """
        response = self.openai_client.embeddings.create(
            model=self.embedding_model, input=text
        )
        return response.data[0].embedding

    def add_entry(
        self,
        entry_id: str,
        question: str,
        answer: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add or update an entry in the vector store.

        Design Decision:
        - Store both question and answer as metadata
        - Generate embedding from question only (what user will search)
        - Include metadata for filtering

        Args:
            entry_id: Unique ID for the entry
            question: The question text
            answer: The answer text
            metadata: Additional metadata (category, confidence, etc.)
        """
        try:
            # Generate embedding for the question
            embedding = self._generate_embedding(question)

            # Prepare metadata
            if metadata is None:
                metadata = {}

            metadata.update(
                {
                    "question": question,
                    "answer": answer,
                    "updated_at": datetime.now().isoformat(),
                }
            )

            # Add to collection (upsert if exists)
            self.collection.upsert(
                ids=[entry_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[question],  # Store question as document for reference
            )

            logger.info(f"Added entry to vector store: {entry_id}")

        except Exception as e:
            logger.error(f"Error adding entry to vector store: {e}")
            raise

    def search(
        self,
        query: str,
        n_results: int = 3,
        similarity_threshold: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for similar questions.

        Design Decision:
        - Return top N results above similarity threshold
        - Include distance/similarity score
        - Allow metadata filtering (e.g., by category)

        Args:
            query: Question to search for
            n_results: Maximum number of results
            similarity_threshold: Minimum similarity (0-1)
            metadata_filter: Filter by metadata

        Returns:
            List of results with question, answer, and similarity score
        """
        try:
            # Generate embedding for query
            query_embedding = self._generate_embedding(query)

            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=metadata_filter,
            )

            # Process results
            processed_results = []

            if results and results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    # Get distance (lower = more similar)
                    distance = results["distances"][0][i]

                    # Convert distance to similarity (1 - distance for cosine)
                    similarity = 1 - distance

                    # Only include if above threshold
                    if similarity >= similarity_threshold:
                        metadata = results["metadatas"][0][i]

                        processed_results.append(
                            {
                                "id": results["ids"][0][i],
                                "question": metadata.get("question", ""),
                                "answer": metadata.get("answer", ""),
                                "similarity": similarity,
                                "category": metadata.get("category", "general"),
                                "confidence": metadata.get("confidence", 0.0),
                                "metadata": metadata,
                            }
                        )

            logger.info(
                f"Search for '{query}' returned {len(processed_results)} results"
            )
            return processed_results

        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []

    def delete_entry(self, entry_id: str) -> None:
        """
        Delete an entry from the vector store.

        Args:
            entry_id: ID of entry to delete
        """
        try:
            self.collection.delete(ids=[entry_id])
            logger.info(f"Deleted entry from vector store: {entry_id}")
        except Exception as e:
            logger.error(f"Error deleting entry: {e}")

    def get_all_ids(self) -> List[str]:
        """
        Get all entry IDs in the collection.

        Returns:
            List of entry IDs
        """
        result = self.collection.get()
        return result["ids"] if result else []

    def count(self) -> int:
        """
        Get count of entries in the collection.

        Returns:
            Number of entries
        """
        return self.collection.count()

    def sync_from_firebase(self, firebase_entries: List[Dict[str, Any]]) -> None:
        """
        Sync vector store with Firebase knowledge base.

        Design Decision:
        - Called on startup or periodically
        - Adds missing entries
        - Updates existing entries if changed

        Args:
            firebase_entries: List of KB entries from Firebase
        """
        logger.info(f"Syncing {len(firebase_entries)} entries from Firebase...")

        synced = 0
        for entry in firebase_entries:
            try:
                self.add_entry(
                    entry_id=entry["id"],
                    question=entry["question"],
                    answer=entry["answer"],
                    metadata={
                        "category": entry.get("category", "general"),
                        "confidence": entry.get("confidence", 0.9),
                        "source": entry.get("source", "unknown"),
                        "usage_count": entry.get("usage_count", 0),
                    },
                )
                synced += 1
            except Exception as e:
                logger.error(f"Error syncing entry {entry.get('id')}: {e}")

        logger.info(f"Successfully synced {synced}/{len(firebase_entries)} entries")


class RAGKnowledgeBase:
    """
    Retrieval Augmented Generation (RAG) knowledge base.

    Design Decision:
    - Use semantic search to find relevant context
    - Let LLM synthesize answer from retrieved documents
    - Fallback to direct answers if confidence is high
    """

    def __init__(self, vector_store: VectorStore):
        """
        Initialize RAG knowledge base.

        Args:
            vector_store: Vector store instance
        """
        self.vector_store = vector_store
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def answer_with_context(
        self, question: str, n_results: int = 3, similarity_threshold: float = 0.7
    ) -> Optional[Dict[str, Any]]:
        """
        Answer question using RAG approach.

        Flow:
        1. Search vector store for similar questions
        2. If high confidence direct answer exists, use it
        3. Otherwise, use LLM to synthesize answer from context

        Args:
            question: User's question
            n_results: Number of similar entries to retrieve
            similarity_threshold: Minimum similarity

        Returns:
            Dict with answer, confidence, and sources
        """
        # Search for similar questions
        results = self.vector_store.search(
            query=question,
            n_results=n_results,
            similarity_threshold=similarity_threshold,
        )

        if not results:
            logger.info(f"No relevant context found for: {question}")
            return None

        # Check if we have a direct high-confidence answer
        best_match = results[0]
        if best_match["similarity"] >= 0.9 and best_match["confidence"] >= 0.9:
            logger.info(
                f"Using direct answer (similarity: {best_match['similarity']:.2f})"
            )
            return {
                "answer": best_match["answer"],
                "confidence": best_match["similarity"],
                "method": "direct",
                "sources": [best_match],
            }

        # Use LLM to synthesize answer from context
        logger.info(f"Using RAG with {len(results)} context documents")

        # Build context from retrieved documents
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"Document {i} (similarity: {result['similarity']:.2f}):\n"
                f"Q: {result['question']}\n"
                f"A: {result['answer']}"
            )

        context = "\n\n".join(context_parts)

        # Prompt for LLM
        system_prompt = """You are a helpful assistant for Bella's Beauty Salon.

Given the context from our knowledge base, answer the user's question.

Rules:
1. Use ONLY information from the provided context
2. If the context doesn't contain enough information, say "I don't have enough information to answer that"
3. Be concise and friendly
4. Don't make up information not in the context"""

        user_prompt = f"""Context from knowledge base:

{context}

User's question: {question}

Please provide a helpful answer based on the context above."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,  # Lower temperature for consistency
                max_tokens=200,
            )

            answer = response.choices[0].message.content.strip()

            # Check if LLM couldn't answer
            if "don't have enough information" in answer.lower():
                return None

            return {
                "answer": answer,
                "confidence": 0.8,  # RAG answers get slightly lower confidence
                "method": "rag",
                "sources": results,
            }

        except Exception as e:
            logger.error(f"Error generating RAG answer: {e}")
            return None
