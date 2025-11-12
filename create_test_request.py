#!/usr/bin/env python
"""
Quick script to create a test help request.
Use this to test the dashboard without running the full agent.

Usage:
    cd backend && uv run python ../create_test_request.py
Or:
    cd /Users/mavens/Human-in-the-loop-Agent
    cd backend && uv run python ../create_test_request.py
"""

import asyncio
import sys
import os

# Add backend to path (we should be running from backend dir)
backend_dir = os.path.dirname(__file__)
if os.path.basename(backend_dir) != "backend":
    backend_dir = os.path.join(backend_dir, "backend")
sys.path.insert(0, backend_dir)

from database import FirebaseClient
from services import HelpRequestService
from models import HelpRequestCreate, Priority


async def main():
    print("🧪 Creating test help request...")
    print()

    try:
        # Initialize
        db = FirebaseClient()
        service = HelpRequestService(db.db)

        # Create request
        request = HelpRequestCreate(
            caller_id="test-caller-001",
            caller_name="Test Customer",
            question="Do you offer hair extensions?",
            context="Customer called and asked about hair extensions. Agent was uncertain and escalated to supervisor.",
            call_session_id="test-session-001",
            priority=Priority.MEDIUM,
        )

        result = await service.create_request(request)

        print("✅ Test help request created successfully!")
        print()
        print(f"📋 Request Details:")
        print(f"   ID: {result['id']}")
        print(f"   Question: {result['question']}")
        print(f"   Caller: {result['caller_name']}")
        print(f"   Status: {result['status']}")
        print(f"   Priority: {result['priority']}")
        print()
        print("👉 Now check your dashboard:")
        print("   1. Open: http://localhost:8501")
        print("   2. Go to 'Pending Requests' tab")
        print("   3. Click 'Refresh' if needed")
        print("   4. You should see the test request!")
        print()
        print("💡 To respond:")
        print("   1. Click the 'Respond' button")
        print("   2. Type your answer")
        print("   3. Click 'Submit Response'")

    except Exception as e:
        print(f"❌ Error creating test request: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
