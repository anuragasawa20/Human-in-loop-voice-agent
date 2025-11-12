"""
Tests for backend services.

Design Decision:
- Test business logic in services
- Mock database calls
- Verify state transitions
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from backend.services import HelpRequestService, KnowledgeBaseService
from backend.models import HelpRequestCreate, Priority, RequestStatus


class TestHelpRequestService:
    """Test help request service."""
    
    @pytest.mark.asyncio
    async def test_create_request_sets_timeout(self):
        """Test that creating a request sets proper timeout."""
        mock_db = Mock()
        mock_doc_ref = Mock()
        mock_doc_ref.id = "test-123"
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        service = HelpRequestService(mock_db)
        
        data = HelpRequestCreate(
            caller_id="+1234567890",
            question="Test question",
            context="Test context",
            call_session_id="session-123"
        )
        
        result = await service.create_request(data)
        
        assert result["id"] == "test-123"
        assert result["status"] == RequestStatus.PENDING.value
        
        # Verify timeout is ~30 minutes from now
        timeout_at = result["timeout_at"]
        created_at = result["created_at"]
        expected_timeout = created_at + timedelta(minutes=30)
        
        # Allow 1 minute tolerance
        assert abs((timeout_at - expected_timeout).total_seconds()) < 60
    
    @pytest.mark.asyncio
    async def test_update_validates_state_transition(self):
        """Test that update validates state transitions."""
        mock_db = Mock()
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "status": RequestStatus.RESOLVED.value,  # Already resolved
            "created_at": datetime.now()
        }
        mock_doc_ref.get.return_value = mock_doc
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        service = HelpRequestService(mock_db)
        
        # Try to update already resolved request
        from backend.models import HelpRequestUpdate
        update_data = HelpRequestUpdate(
            supervisor_response="Test response",
            supervisor_id="test-supervisor"
        )
        
        with pytest.raises(ValueError, match="already resolved"):
            await service.update_request("test-123", update_data)
    
    @pytest.mark.asyncio
    async def test_check_timeouts_marks_expired_requests(self):
        """Test that check_timeouts marks expired requests."""
        mock_db = Mock()
        
        # Create mock expired requests
        expired_doc_1 = Mock()
        expired_doc_1.id = "req-1"
        expired_doc_2 = Mock()
        expired_doc_2.id = "req-2"
        
        mock_query = Mock()
        mock_query.stream.return_value = [expired_doc_1, expired_doc_2]
        mock_db.collection.return_value.where.return_value.where.return_value = mock_query
        
        # Mock document updates
        def mock_document(doc_id):
            mock_ref = Mock()
            return mock_ref
        
        mock_db.collection.return_value.document.side_effect = mock_document
        
        service = HelpRequestService(mock_db)
        timed_out_ids = await service.check_timeouts()
        
        assert len(timed_out_ids) == 2
        assert "req-1" in timed_out_ids
        assert "req-2" in timed_out_ids


class TestKnowledgeBaseService:
    """Test knowledge base service."""
    
    def test_normalize_question(self):
        """Test question normalization."""
        mock_db = Mock()
        service = KnowledgeBaseService(mock_db)
        
        assert service.normalize_question("What are your HOURS?") == "what are your hours"
        assert service.normalize_question("  Spaces  ") == "spaces"
        assert service.normalize_question("Question?!") == "question"
    
    @pytest.mark.asyncio
    async def test_find_duplicate_detects_exact_match(self):
        """Test that find_duplicate finds exact matches."""
        mock_db = Mock()
        
        # Mock existing entry
        mock_doc = Mock()
        mock_doc.id = "existing-1"
        mock_doc.to_dict.return_value = {
            "question": "What are your hours?",
            "answer": "9am-7pm",
            "confidence": 1.0
        }
        
        mock_query = Mock()
        mock_query.stream.return_value = [mock_doc]
        mock_db.collection.return_value.where.return_value.limit.return_value = mock_query
        
        service = KnowledgeBaseService(mock_db)
        duplicate = await service.find_duplicate("What are your hours?")
        
        assert duplicate is not None
        assert duplicate["id"] == "existing-1"
    
    @pytest.mark.asyncio
    async def test_update_from_resolution_creates_new_entry(self):
        """Test that update_from_resolution creates new entry if no duplicate."""
        mock_db = Mock()
        
        # No duplicates found
        mock_query = Mock()
        mock_query.stream.return_value = []
        mock_db.collection.return_value.where.return_value.limit.return_value = mock_query
        
        # Mock document creation
        mock_doc_ref = Mock()
        mock_doc_ref.id = "new-kb-1"
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        service = KnowledgeBaseService(mock_db)
        result = await service.update_from_resolution(
            question="Do you offer hair extensions?",
            answer="Yes, starting at $200",
            source_request_id="req-123"
        )
        
        assert result["id"] == "new-kb-1"
        assert result["confidence"] == 0.9  # High confidence from supervisor


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

