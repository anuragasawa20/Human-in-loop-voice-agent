#!/usr/bin/env python
"""
Main AI Agent for Priyanka's Beauty Salon.

This agent handles phone calls, answers questions from knowledge base,
and escalates to human supervisors when uncertain.

Architecture:
1. Speech-to-Text (AssemblyAI)
2. Large Language Model (OpenAI GPT-4.1 mini)
3. Text-to-Speech (Cartesia Sonic-3)
4. Knowledge Base lookup before LLM
5. request_help() tool for escalation
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions
from livekit.plugins import noise_cancellation, silero

from prompt import get_system_prompt, get_greeting
from knowledge import KnowledgeBaseService
from tools import HelpRequestService, create_request_help_tool

# Load environment variables
load_dotenv(".env.local")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SalonReceptionist(Agent):
    """
        AI Receptionist for Priyanka's Beauty Salon.

    Design Decision:
    - Checks knowledge base FIRST before using LLM
    - LLM has access to request_help() tool for escalation
    - Gracefully handles unknown questions
    """

    def __init__(self, caller_id: str = "unknown"):
        """
        Initialize the salon receptionist agent.

        Args:
            caller_id: Identifier for the current caller
        """
        backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")
        help_service = HelpRequestService(backend_url)
        request_help_tool = create_request_help_tool(help_service, caller_id)

        super().__init__(instructions=get_system_prompt(), tools=[request_help_tool])

        self.caller_id = caller_id
        self.kb_service = KnowledgeBaseService()
        self.help_service = help_service
        self.request_help_tool = request_help_tool

        logger.info(f"SalonReceptionist initialized for caller: {caller_id}")


async def entrypoint(ctx: agents.JobContext):
    """
    Main entry point for the agent.

    This function is called when a new call/session starts.

    Design Decision:
    - Uses STT-LLM-TTS pipeline for best performance
    - Includes noise cancellation for phone calls
    - Turn detection for natural conversation flow
    """

    # Get caller information (from room metadata if available)
    caller_id = ctx.room.metadata or f"caller-{ctx.room.name}"

    logger.info(f"New call session started: {caller_id}")

    # Create agent instance
    agent = SalonReceptionist(caller_id=caller_id)

    # Create session with voice pipeline
    session = AgentSession(
        # STT: AssemblyAI Universal-Streaming
        stt="assemblyai/universal-streaming:en",
        # LLM: OpenAI GPT-4.1 mini
        llm="openai/gpt-4.1-mini",
        # TTS: Cartesia Sonic-3
        tts="cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        # Voice Activity Detection
        vad=silero.VAD.load(),
    )

    # Start the session
    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            # Noise cancellation for better phone call quality
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Generate initial greeting
    await session.generate_reply(instructions=f"Greet the caller: {get_greeting()}")

    logger.info("Agent session started and greeting sent")


def main():
    """
    Main function to run the agent.

    Modes:
    - console: Run in terminal (Python only)
    - dev: Connect to LiveKit Cloud in development mode
    - start: Production mode
    """

    # Check required environment variables
    required_vars = ["LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "LIVEKIT_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please copy .env.example to .env.local and fill in the values")
        logger.error("Run: lk app env -w")
        return

    logger.info("Starting Priyanka's Beauty Salon AI Receptionist...")
    logger.info(f"Backend API: {os.getenv('BACKEND_API_URL', 'http://localhost:8000')}")

    # Run the agent with LiveKit CLI
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))


if __name__ == "__main__":
    main()
