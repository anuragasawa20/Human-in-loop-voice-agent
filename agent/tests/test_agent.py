"""
Tests for the AI agent.

Design Decision:
- Test core functionality in isolation
- Mock external services (LiveKit, OpenAI, Firebase)
- Focus on business logic
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from agent.knowledge import KnowledgeBaseService, KnowledgeEntry
from agent.tools import HelpRequestService
from datetime import datetime


class TestKnowledgeBaseService:
    """Test the knowledge base service."""

    def test_normalize_question(self):
        """Test question normalization."""
        service = KnowledgeBaseService()

        assert (
            service.normalize_question("What are your hours?") == "what are your hours"
        )
        assert (
            service.normalize_question("  What   are  your  hours?  ")
            == "what are your hours"
        )
        assert (
            service.normalize_question("WHAT ARE YOUR HOURS?!") == "what are your hours"
        )

    @pytest.mark.asyncio
    async def test_search_returns_none_without_db(self):
        """Test search returns None when no DB client."""
        service = KnowledgeBaseService(db_client=None)

        result = await service.search("What are your hours?")
        assert result is None

    @pytest.mark.asyncio
    async def test_search_with_cache(self):
        """Test cache hit."""
        service = KnowledgeBaseService(db_client=None)

        # Add to cache
        entry = KnowledgeEntry(
            id="test-1",
            question="What are your hours?",
            answer="We're open Monday-Saturday 9am-7pm",
            confidence=1.0,
            category="hours",
            usage_count=0,
            source="test",
            created_at=datetime.now(),
        )
        service._cache["what are your hours"] = entry

        # Should return from cache
        result = await service.search("What are your hours?")
        assert result is not None
        assert result.answer == "We're open Monday-Saturday 9am-7pm"


class TestHelpRequestService:
    """Test the help request service."""

    @pytest.mark.asyncio
    async def test_request_help_creates_request(self):
        """Test that request_help creates a request."""
        service = HelpRequestService(backend_url="http://test")

        # Mock the HTTP client
        with patch.object(service.client, "post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": "req-123",
                "timeout_at": "2025-11-05T11:00:00Z",
            }
            mock_post.return_value = mock_response

            result = await service.request_help(
                caller_id="+1234567890",
                question="Do you offer hair extensions?",
                context="Customer asking about services",
            )

            assert result["success"] is True
            assert result["request_id"] == "req-123"
            assert (
                "supervisor" in result["message"].lower()
                or "manager" in result["message"].lower()
            )

    @pytest.mark.asyncio
    async def test_request_help_handles_timeout(self):
        """Test graceful handling of backend timeout."""
        import httpx

        service = HelpRequestService(backend_url="http://test")

        with patch.object(
            service.client, "post", side_effect=httpx.TimeoutException("Timeout")
        ):
            result = await service.request_help(
                caller_id="+1234567890",
                question="Test question",
                context="Test context",
            )

            assert result["success"] is False
            assert "message" in result  # Still provides a message to customer


class TestPrompt:
    """Test the system prompt."""

    def test_prompt_contains_business_info(self):
        """Test that prompt includes business information."""
        from agent.prompt import SALON_CONTEXT

        assert "Priyanka's Beauty Salon" in SALON_CONTEXT
        assert "9am" in SALON_CONTEXT or "9 AM" in SALON_CONTEXT
        assert "7pm" in SALON_CONTEXT or "7 PM" in SALON_CONTEXT
        assert "50000 INR" in SALON_CONTEXT  # Haircut price

    def test_prompt_defines_escalation_behavior(self):
        """Test that prompt explains when to escalate."""
        from agent.prompt import SALON_CONTEXT

        assert (
            "escalate" in SALON_CONTEXT.lower()
            or "request_help" in SALON_CONTEXT.lower()
        )
        assert (
            "uncertain" in SALON_CONTEXT.lower()
            or "don't know" in SALON_CONTEXT.lower()
        )


# Integration test (requires setup)
@pytest.mark.integration
class TestEndToEndFlow:
    """Test complete escalation flow."""

    @pytest.mark.asyncio
    async def test_complete_escalation_flow(self):
        """
        Test: Unknown question → Escalate → Resolve → Notify → Learn

        This is a high-level integration test that requires:
        - Backend running
        - Firebase configured
        - All services connected
        """
        # This would be implemented with actual service instances
        # For now, it serves as documentation of the expected flow

        # Step 1: Agent receives unknown question
        question = "Do you offer hair extensions?"

        # Step 2: Agent escalates (creates help request)
        # help_request = await agent.handle_question(question)
        # assert help_request.status == "pending"

        # Step 3: Supervisor responds
        # response = await supervisor.respond(help_request.id, "Yes, starting at $200")
        # assert response.status == "resolved"

        # Step 4: Verify KB updated
        # kb_entry = await kb.search(question)
        # assert kb_entry is not None
        # assert "$200" in kb_entry.answer

        # Step 5: Verify customer notified
        # notification = await notifications.get_latest()
        # assert notification.recipient == caller_id

        pass  # Placeholder for full integration test


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
