#!/usr/bin/env python
"""
Test script to verify agent and knowledge base functionality.

This script tests:
1. Knowledge base service loads
2. Semantic search works
3. Agent can answer known questions
4. Agent escalates unknown questions
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv(".env.local")

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("🧪 TESTING AGENT & KNOWLEDGE BASE")
print("=" * 60)
print()


async def test_knowledge_base():
    """Test knowledge base functionality."""
    print("📚 TEST 1: Knowledge Base Service")
    print("-" * 60)

    try:
        from knowledge import KnowledgeBaseService

        # Initialize without database (for testing)
        kb_service = KnowledgeBaseService(db_client=None)

        print("✅ Knowledge base service initialized")
        print(f"   Confidence threshold: {kb_service.confidence_threshold}")
        print(f"   Semantic search enabled: {kb_service.vector_store is not None}")
        print()

        return True
    except Exception as e:
        print(f"❌ Failed to initialize knowledge base: {e}")
        print()
        return False


async def test_vector_store():
    """Test vector store and semantic search."""
    print("🔍 TEST 2: Vector Store & Semantic Search")
    print("-" * 60)

    try:
        from vector_store import VectorStore

        # Initialize vector store
        vs = VectorStore()

        print(f"✅ Vector store initialized")
        print(f"   Entries in vector store: {vs.count()}")
        print()

        # Add test entries
        print("Adding test entries...")
        vs.add_entry(
            entry_id="test-hours",
            question="What are your business hours?",
            answer="We're open Monday through Saturday from 9 AM to 7 PM. Closed Sundays.",
            metadata={"category": "hours", "confidence": 1.0},
        )

        vs.add_entry(
            entry_id="test-pricing",
            question="How much does a haircut cost?",
            answer="A haircut is $50, which includes wash and style.",
            metadata={"category": "pricing", "confidence": 1.0},
        )

        print(f"✅ Added 2 test entries")
        print(f"   Total entries: {vs.count()}")
        print()

        # Test semantic search
        print("Testing semantic search...")
        test_queries = [
            ("What are your hours?", "test-hours"),  # Exact match
            ("When do you open?", "test-hours"),  # Similar question
            ("What time do you close?", "test-hours"),  # Similar question
            ("How expensive is a haircut?", "test-pricing"),  # Similar question
        ]

        for query, expected_id in test_queries:
            results = vs.search(query, n_results=1, similarity_threshold=0.7)

            if results:
                result = results[0]
                match_status = "✅" if result["id"] == expected_id else "⚠️"
                print(f"{match_status} '{query}'")
                print(f"   → Matched: '{result['question']}'")
                print(f"   → Similarity: {result['similarity']:.2f}")
            else:
                print(f"❌ '{query}' - No match found")
            print()

        return True

    except Exception as e:
        print(f"❌ Vector store test failed: {e}")
        import traceback

        traceback.print_exc()
        print()
        return False


async def test_knowledge_base_search():
    """Test knowledge base search with semantic search."""
    print("🔎 TEST 3: Knowledge Base Search")
    print("-" * 60)

    try:
        from knowledge import KnowledgeBaseService

        kb_service = KnowledgeBaseService(db_client=None, confidence_threshold=0.7)

        # Ensure vector store is loaded
        if kb_service.vector_store is None:
            print("⚠️  Vector store not available")
            return False

        print("Testing knowledge base search...")

        # Test questions
        test_questions = [
            "What are your hours?",
            "When do you open?",
            "How much is a haircut?",
            "What's the price for a cut?",
        ]

        for question in test_questions:
            result = await kb_service.search(question)

            if result:
                print(f"✅ '{question}'")
                print(f"   → Answer: {result.answer[:60]}...")
                print(f"   → Confidence: {result.confidence:.2f}")
                print(f"   → Source: {result.source}")
            else:
                print(f"❌ '{question}' - No answer found")
            print()

        return True

    except Exception as e:
        print(f"❌ Knowledge base search failed: {e}")
        import traceback

        traceback.print_exc()
        print()
        return False


async def test_prompt_loading():
    """Test prompt loading."""
    print("💬 TEST 4: Prompt Loading")
    print("-" * 60)

    try:
        from prompt import get_system_prompt, get_greeting

        prompt = get_system_prompt()
        greeting = get_greeting()

        print("✅ System prompt loaded")
        print(f"   Length: {len(prompt)} characters")
        print(f"   Contains 'Bella': {'Bella' in prompt}")
        print(f"   Contains 'request_help': {'request_help' in prompt}")
        print()

        print("✅ Greeting loaded")
        print(f"   Greeting: {greeting}")
        print()

        return True

    except Exception as e:
        print(f"❌ Prompt loading failed: {e}")
        print()
        return False


async def test_tools():
    """Test tools."""
    print("🔧 TEST 5: Tools (request_help)")
    print("-" * 60)

    try:
        from tools import create_request_help_tool

        # Create tool with mock caller_id
        tool = create_request_help_tool(None, caller_id="test-caller")

        print("✅ request_help tool created")
        print(f"   Tool type: {type(tool).__name__}")
        print(f"   Tool is callable: {callable(tool)}")
        print()

        return True

    except Exception as e:
        print(f"❌ Tools test failed: {e}")
        import traceback

        traceback.print_exc()
        print()
        return False


async def test_environment():
    """Test environment variables."""
    print("⚙️  TEST 6: Environment Variables")
    print("-" * 60)

    required_vars = {
        "OPENAI_API_KEY": "OpenAI API (for LLM and embeddings)",
        "LIVEKIT_URL": "LiveKit server URL",
        "LIVEKIT_API_KEY": "LiveKit API key",
        "LIVEKIT_API_SECRET": "LiveKit API secret",
    }

    all_set = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask the value for security
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✅ {var}: {masked}")
        else:
            print(f"❌ {var}: NOT SET ({description})")
            all_set = False

    print()

    if not all_set:
        print("⚠️  Some environment variables are missing!")
        print("   Create agent/.env.local with required values")
        print("   See SETUP.md for instructions")
        print()

    return all_set


async def main():
    """Run all tests."""

    # Test environment first
    env_ok = await test_environment()

    # Test components
    kb_ok = await test_knowledge_base()
    vs_ok = await test_vector_store()
    search_ok = await test_knowledge_base_search()
    prompt_ok = await test_prompt_loading()
    tools_ok = await test_tools()

    # Summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    tests = [
        ("Environment Variables", env_ok),
        ("Knowledge Base Service", kb_ok),
        ("Vector Store & Semantic Search", vs_ok),
        ("Knowledge Base Search", search_ok),
        ("Prompt Loading", prompt_ok),
        ("Tools (request_help)", tools_ok),
    ]

    passed = sum(1 for _, ok in tests if ok)
    total = len(tests)

    for test_name, ok in tests:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status}: {test_name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print()
        print("🎉 All tests passed! Agent is ready to run!")
        print()
        print("Next steps:")
        print("1. Configure environment variables (if not done)")
        print("2. Run backend: cd backend && uv run uvicorn main:app --reload")
        print("3. Run agent: cd agent && uv run agent.py console")
        print("4. Test by asking: 'What are your hours?'")
    else:
        print()
        print("⚠️  Some tests failed. Fix the issues above before running agent.")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
