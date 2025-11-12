"""
Main FastAPI application for the salon backend.

This provides REST API endpoints for:
- Help requests (CRUD)
- Knowledge base (CRUD)
- Notifications
- LiveKit token generation
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from livekit import api

from models import (
    HelpRequestCreate,
    HelpRequestUpdate,
    HelpRequestResponse,
    KnowledgeEntryCreate,
    KnowledgeEntryUpdate,
    KnowledgeEntryResponse,
    NotificationRequest,
    SuccessResponse,
    ErrorResponse,
    RequestStatus,
)
from database import get_db, FirebaseClient
from services import HelpRequestService, KnowledgeBaseService, NotificationService

# Load environment
load_dotenv(".env.local")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# writing changes for the backend
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for the application.

    Design Decision:
    - Initialize database connection on startup
    - Close connections on shutdown
    """
    logger.info("Starting Bella's Beauty Salon Backend API...")

    # Startup
    db = get_db()
    logger.info("Database connected")

    yield

    # Shutdown
    logger.info("Shutting down...")
    db.close()


# Create FastAPI application
app = FastAPI(
    title="Bella's Beauty Salon API",
    description="Backend API for human-in-the-loop AI agent system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection
def get_request_service(db: FirebaseClient = Depends(get_db)) -> HelpRequestService:
    """Get help request service instance."""
    return HelpRequestService(db)


def get_kb_service(db: FirebaseClient = Depends(get_db)) -> KnowledgeBaseService:
    """Get knowledge base service instance."""
    return KnowledgeBaseService(db)


def get_notification_service(
    db: FirebaseClient = Depends(get_db),
) -> NotificationService:
    """Get notification service instance."""
    return NotificationService(db)


# ============================================================================
# HELP REQUESTS API
# ============================================================================


@app.post(
    "/api/help-requests",
    response_model=HelpRequestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Help Requests"],
)
async def create_help_request(
    request_data: HelpRequestCreate,
    service: HelpRequestService = Depends(get_request_service),
    kb_service: KnowledgeBaseService = Depends(get_kb_service),
):
    """
    Create a new help request from the AI agent.

    Design Decision:
    - Called by agent when escalating
    - Automatically sets timeout (30 min)
    - Returns request ID and details
    """
    try:
        result = await service.create_request(request_data)
        logger.info(f"Help request created via API: {result['id']}")
        return result
    except Exception as e:
        logger.error(f"Error creating help request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@app.get(
    "/api/help-requests",
    response_model=List[HelpRequestResponse],
    tags=["Help Requests"],
)
async def list_help_requests(
    status_filter: Optional[RequestStatus] = None,
    limit: int = 50,
    service: HelpRequestService = Depends(get_request_service),
):
    """
    List help requests with optional filtering.

    Query Parameters:
    - status_filter: Filter by status (pending, in_progress, resolved, timeout)
    - limit: Maximum number of results (default 50)
    """
    try:
        results = await service.list_requests(status=status_filter, limit=limit)
        return results
    except Exception as e:
        logger.error(f"Error listing help requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@app.get(
    "/api/help-requests/{request_id}",
    response_model=HelpRequestResponse,
    tags=["Help Requests"],
)
async def get_help_request(
    request_id: str, service: HelpRequestService = Depends(get_request_service)
):
    """Get a specific help request by ID."""
    result = await service.get_request(request_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Help request {request_id} not found",
        )

    return result


@app.patch(
    "/api/help-requests/{request_id}",
    response_model=HelpRequestResponse,
    tags=["Help Requests"],
)
async def update_help_request(
    request_id: str,
    update_data: HelpRequestUpdate,
    service: HelpRequestService = Depends(get_request_service),
    kb_service: KnowledgeBaseService = Depends(get_kb_service),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Update a help request with supervisor response.

    Design Decision:
    - Marks request as RESOLVED
    - Triggers knowledge base auto-update
    - Sends notification to customer

    This is the main endpoint supervisors use to respond.
    """
    try:
        # Update the request
        result = await service.update_request(request_id, update_data)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Help request {request_id} not found",
            )

        # Auto-update knowledge base
        try:
            kb_entry = await kb_service.update_from_resolution(
                question=result["question"],
                answer=update_data.supervisor_response,
                source_request_id=request_id,
            )
            logger.info(f"KB auto-updated: {kb_entry['id']}")
        except Exception as e:
            logger.warning(f"Failed to auto-update KB: {e}")
            # Don't fail the request if KB update fails

        # Send notification to customer
        try:
            notification_message = f"""Hi! Thank you for your patience.

Regarding your question: "{result['question']}"

Answer: {update_data.supervisor_response}

Feel free to call us again if you have more questions!"""

            await notification_service.notify_customer(
                recipient=result["caller_id"],
                message=notification_message,
                request_id=request_id,
            )
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")
            # Don't fail the request if notification fails

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating help request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@app.post(
    "/api/help-requests/{request_id}/in-progress",
    response_model=HelpRequestResponse,
    tags=["Help Requests"],
)
async def mark_request_in_progress(
    request_id: str,
    supervisor_id: str,
    service: HelpRequestService = Depends(get_request_service),
):
    """Mark a request as in progress (supervisor is working on it)."""
    result = await service.mark_in_progress(request_id, supervisor_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Help request {request_id} not found",
        )

    return result


# ============================================================================
# KNOWLEDGE BASE API
# ============================================================================


@app.get(
    "/api/knowledge-base",
    response_model=List[KnowledgeEntryResponse],
    tags=["Knowledge Base"],
)
async def list_knowledge_entries(
    category: Optional[str] = None,
    limit: int = 100,
    service: KnowledgeBaseService = Depends(get_kb_service),
):
    """
    List knowledge base entries.

    Query Parameters:
    - category: Filter by category
    - limit: Maximum results (default 100)
    """
    try:
        results = await service.list_entries(category=category, limit=limit)
        return results
    except Exception as e:
        logger.error(f"Error listing KB entries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@app.post(
    "/api/knowledge-base",
    response_model=KnowledgeEntryResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Knowledge Base"],
)
async def create_knowledge_entry(
    entry_data: KnowledgeEntryCreate,
    service: KnowledgeBaseService = Depends(get_kb_service),
):
    """
    Create a new knowledge base entry manually.

    Design Decision:
    - Supervisors can manually add entries
    - Useful for proactive knowledge building
    """
    try:
        result = await service.create_entry(entry_data)
        logger.info(f"KB entry created manually: {result['id']}")
        return result
    except Exception as e:
        logger.error(f"Error creating KB entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ============================================================================
# NOTIFICATIONS API
# ============================================================================


@app.post(
    "/api/notifications/send", response_model=SuccessResponse, tags=["Notifications"]
)
async def send_notification(
    notification: NotificationRequest,
    service: NotificationService = Depends(get_notification_service),
):
    """
    Send a notification to a customer.

    Design Decision:
    - MVP: Console log simulation
    - Can be called manually or automatically
    """
    try:
        success = await service.notify_customer(
            recipient=notification.recipient,
            message=notification.message,
            request_id=notification.request_id,
        )

        if success:
            return SuccessResponse(
                message="Notification sent successfully",
                data={"recipient": notification.recipient},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send notification",
            )
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ============================================================================
# LIVEKIT TOKEN ENDPOINT
# ============================================================================


class LiveKitTokenRequest(BaseModel):
    """Request model for LiveKit token generation."""

    room: str
    participant: str = "user"


class LiveKitTokenResponse(BaseModel):
    """Response model for LiveKit token."""

    token: str
    url: str


@app.post("/api/livekit/token", response_model=LiveKitTokenResponse, tags=["LiveKit"])
async def get_livekit_token(request: LiveKitTokenRequest):
    """
    Generate a LiveKit token for voice call connection.

    This endpoint allows the voice demo to connect to LiveKit
    and interact with the AI agent.

    Args:
        room: Room name (e.g., "voice-demo")
        participant: Participant name (e.g., "demo-user-123")

    Returns:
        LiveKit connection token and URL
    """
    try:
        # Get LiveKit credentials from environment
        livekit_url = os.getenv("LIVEKIT_URL")
        livekit_api_key = os.getenv("LIVEKIT_API_KEY")
        livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")

        if not all([livekit_url, livekit_api_key, livekit_api_secret]):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LiveKit credentials not configured",
            )

        # Generate token
        token = (
            api.AccessToken(livekit_api_key, livekit_api_secret)
            .with_identity(request.participant)
            .with_name(request.participant)
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=request.room,
                    can_publish=True,
                    can_subscribe=True,
                )
            )
        )

        jwt_token = token.to_jwt()

        logger.info(
            f"Generated LiveKit token for {request.participant} in room {request.room}"
        )

        return LiveKitTokenResponse(token=jwt_token, url=livekit_url)

    except Exception as e:
        logger.error(f"Error generating LiveKit token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate token: {str(e)}",
        )


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================


@app.get("/health", tags=["Utility"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "salon-backend"}


@app.get("/api/stats", tags=["Utility"])
async def get_stats(
    request_service: HelpRequestService = Depends(get_request_service),
    kb_service: KnowledgeBaseService = Depends(get_kb_service),
):
    """
    Get system statistics.

    Returns:
    - Total requests by status
    - KB entry count
    - Recent activity
    """
    try:
        # Get counts
        pending = await request_service.list_requests(
            status=RequestStatus.PENDING, limit=1000
        )
        in_progress = await request_service.list_requests(
            status=RequestStatus.IN_PROGRESS, limit=1000
        )
        resolved = await request_service.list_requests(
            status=RequestStatus.RESOLVED, limit=1000
        )
        timeout = await request_service.list_requests(
            status=RequestStatus.TIMEOUT, limit=1000
        )

        kb_entries = await kb_service.list_entries(limit=1000)

        return {
            "help_requests": {
                "pending": len(pending),
                "in_progress": len(in_progress),
                "resolved": len(resolved),
                "timeout": len(timeout),
                "total": len(pending) + len(in_progress) + len(resolved) + len(timeout),
            },
            "knowledge_base": {"total_entries": len(kb_entries)},
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
