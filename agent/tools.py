"""
Tools/functions available to the AI agent.
Main tool: request_help() for escalating to supervisors.
"""

import logging
import httpx
from typing import Optional
from datetime import datetime, timedelta

from livekit.agents.llm import function_tool

logger = logging.getLogger(__name__)


class HelpRequestService:
    """
    Service for creating and managing help requests.

    Design Decision:
    - Agent calls this service when uncertain
    - Creates request in backend via API
    - Returns graceful message for customer
    """

    def __init__(self, backend_url: str = "http://localhost:8000"):
        """
        Initialize the help request service.

        Args:
            backend_url: URL of the backend API
        """
        self.backend_url = backend_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=10.0)

        logger.info(f"HelpRequestService initialized with backend: {backend_url}")

    async def request_help(
        self,
        caller_id: str,
        question: str,
        context: str,
        caller_name: Optional[str] = None,
        priority: str = "medium",
    ) -> dict:
        """
        Escalate a question to human supervisor.

        This is the main function called by the AI agent when it cannot
        answer a question or is uncertain.

        Design Decision:
        - Creates help request in database via backend API
        - Returns graceful message for agent to tell customer
        - Sets 30-minute timeout for supervisor response

        Args:
            caller_id: Phone number or session ID
            question: The specific question asked
            context: Conversation context leading to this question
            caller_name: Optional caller name
            priority: Urgency level (low, medium, high)

        Returns:
            Dict with message and request details
            {
                "message": "...",
                "request_id": "...",
                "estimated_time": "..."
            }
        """
        logger.info(f"Creating help request for caller {caller_id}: {question}")

        request_data = {
            "caller_id": caller_id,
            "caller_name": caller_name,
            "question": question,
            "context": context,
            "priority": priority,
            "call_session_id": caller_id,  # For now, use same as caller_id
        }

        try:
            # Call backend API to create help request
            response = await self.client.post(
                f"{self.backend_url}/api/help-requests", json=request_data
            )

            if response.status_code == 201:
                result = response.json()

                logger.info(f"Help request created: {result['id']}")

                return {
                    "success": True,
                    "request_id": result["id"],
                    "message": "That's a great question! Let me check with my manager and I'll get back to you shortly.",
                    "estimated_time": "within 30 minutes",
                    "timeout_at": result.get("timeout_at"),
                }
            else:
                logger.error(f"Backend returned error: {response.status_code}")
                raise Exception(f"Backend error: {response.status_code}")

        except httpx.TimeoutException:
            logger.error("Backend request timed out")
            # Fallback: Still tell customer we'll help
            return {
                "success": False,
                "request_id": None,
                "message": "Let me check with my manager and get back to you.",
                "estimated_time": "as soon as possible",
                "error": "Backend timeout",
            }
        except Exception as e:
            logger.error(f"Error creating help request: {e}")
            # Fallback: Graceful degradation
            return {
                "success": False,
                "request_id": None,
                "message": "Let me have someone get back to you about that.",
                "estimated_time": "shortly",
                "error": str(e),
            }

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Tool definition for LiveKit agent
def create_request_help_tool(help_service: HelpRequestService, caller_id: str):
    """
    Create the request_help tool for the agent.

    This function returns a tool definition that the LLM can call.

    Args:
        help_service: Instance of HelpRequestService
        caller_id: Current caller's ID

    Returns:
        Tool function for the agent
    """

    @function_tool(
        name="request_help",
        description="Escalate the caller's question to a human supervisor when the agent is uncertain or the request is outside standard policies.",
    )
    async def request_help(
        question: str, reason: str = "Information not in knowledge base"
    ) -> str:
        """
        Escalate question to human supervisor when Agent cannot answer.

        Use this function when:
        - Question is outside your knowledge scope
        - You are uncertain about the answer
        - Customer asks about custom services or special cases
        - Anything related to specific availability, scheduling, or stylist requests

        Args:
            question: The exact question the customer asked
            reason: Why you need help (e.g., "Not in KB", "Needs custom pricing")

        Returns:
            A message to tell the customer
        """
        # Get some context (this would come from conversation history)
        context = f"Customer asked: {question}. Reason for escalation: {reason}"

        if help_service is None:
            logger.warning(
                "HelpRequestService not configured; returning default escalation message."
            )
            return "That's a great question! Let me check with my manager and I'll get back to you shortly."

        result = await help_service.request_help(
            caller_id=caller_id, question=question, context=context, priority="medium"
        )

        if result["success"]:
            return result["message"]
        else:
            # Even if backend fails, give graceful response
            return "Let me have someone get back to you about that shortly."

    return request_help
