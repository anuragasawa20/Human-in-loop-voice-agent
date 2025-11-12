"""
Simple LiveKit agent connection test.
"""

import asyncio
import logging
import os
import sys
import time
from dotenv import load_dotenv
from uuid import uuid4

# Load environment variables
load_dotenv(".env.local")

try:
    from livekit import rtc, api
except ImportError:
    print("❌ Error: livekit package not installed")
    print("Install with: uv add livekit")
    sys.exit(1)

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test-agent")

# LiveKit credentials from environment
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
ROOM_NAME = os.getenv("TEST_ROOM_NAME", "test-room")


async def main():
    """Main test function."""

    # Validate credentials
    if not all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]):
        logger.error("❌ Missing LiveKit credentials!")
        logger.error("Please set in .env.local:")
        logger.error("  - LIVEKIT_URL")
        logger.error("  - LIVEKIT_API_KEY")
        logger.error("  - LIVEKIT_API_SECRET")
        logger.error("  - TEST_ROOM_NAME (optional, defaults to 'test-room')")
        sys.exit(1)

    logger.info("=" * 70)
    logger.info("🤖 Starting LiveKit Test Agent")
    logger.info("=" * 70)
    logger.info(f"📍 URL: {LIVEKIT_URL}")
    logger.info(f"🏠 Room: {ROOM_NAME}")

    # Generate token for the agent to join the room
    # Use unique identity to avoid duplicate connections
    unique_identity = f"test-agent-{uuid4()}"
    logger.info(f"🆔 Identity: {unique_identity}")
    logger.info("")

    logger.info("🔑 Generating access token...")
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    token.with_identity(unique_identity)
    token.with_name("Test Agent")
    token.with_grants(
        api.VideoGrants(
            room_join=True,
            room=ROOM_NAME,
        )
    )
    agent_token = token.to_jwt()
    logger.info("✅ Token generated")
    logger.info("")
    logger.info("=" * 70)
    logger.info("🔑 AGENT TOKEN (copy this to join the room manually):")
    logger.info("=" * 70)
    logger.info(f"{agent_token}")
    logger.info("=" * 70)
    logger.info("")

    # Create room instance
    room = rtc.Room()

    # Event handlers
    @room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info("")
        logger.info("=" * 70)
        logger.info(
            f"✅ NEW PARTICIPANT JOINED: {participant.identity} (name: {participant.name})"
        )
        logger.info(f"   Total participants: {len(room.remote_participants) + 1}")
        logger.info("=" * 70)
        logger.info("")

    @room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info(f"👋 Participant left: {participant.identity}")
        logger.info(f"   Remaining participants: {len(room.remote_participants) + 1}")

    @room.on("track_published")
    def on_track_published(
        publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant
    ):
        logger.info("")
        logger.info("🎯" * 35)
        logger.info(f"📡 TRACK PUBLISHED by {participant.identity}")
        logger.info(f"   Type: {publication.kind}")
        logger.info(f"   Track SID: {publication.sid}")
        logger.info(f"   Track name: {publication.name}")
        logger.info(f"   Subscribed: {publication.subscribed}")
        logger.info("🎯" * 35)
        logger.info("")

    @room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.TrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        logger.info("")
        logger.info("🔊" * 35)
        logger.info(f"🎵 TRACK SUBSCRIBED from {participant.identity}")
        logger.info(f"   Type: {track.kind}")
        logger.info(f"   Track SID: {track.sid}")
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            logger.info("   📢 This is an AUDIO track - you should hear them speaking!")
            logger.info("   🎤 Audio is now streaming from this participant")
        elif track.kind == rtc.TrackKind.KIND_VIDEO:
            logger.info("   📹 This is a VIDEO track")
        logger.info("🔊" * 35)
        logger.info("")

    @room.on("track_unsubscribed")
    def on_track_unsubscribed(
        track: rtc.Track,
        publication: rtc.TrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        logger.info(f"🔇 Unsubscribed from {participant.identity}'s track")

    @room.on("data_received")
    def on_data_received(data: bytes, participant: rtc.Participant):
        logger.info(f"📨 Data received from {participant.identity}")
        try:
            decoded = data.decode("utf-8")
            logger.info(f"   Content: {decoded[:100]}...")  # First 100 chars
        except Exception:
            logger.info(f"   Binary data: {len(data)} bytes")

    @room.on("connection_quality_changed")
    def on_connection_quality_changed(*args, **kwargs):
        # Connection quality event - parameters vary by SDK version
        # Suppress these logs as they're too verbose
        pass

    @room.on("disconnected")
    def on_disconnected():
        logger.info("🔴 Disconnected from room")

    try:
        # Connect to the room
        logger.info("")
        logger.info(f"🔌 Connecting to room: {ROOM_NAME}...")
        await room.connect(LIVEKIT_URL, agent_token)

        logger.info("=" * 70)
        logger.info("✅ CONNECTED SUCCESSFULLY!")
        logger.info("=" * 70)
        logger.info(f"🏠 Room: {room.name}")
        logger.info(f"👤 Identity: {room.local_participant.identity}")
        logger.info(f"👥 Participants in room: {len(room.remote_participants)}")
        logger.info("")

        # List current participants
        if room.remote_participants:
            logger.info("Current participants:")
            for participant in room.remote_participants.values():
                logger.info(f"  👤 {participant.identity} (name: {participant.name})")
                # List their tracks
                for pub in participant.track_publications.values():
                    logger.info(f"     - {pub.kind} track: {pub.sid}")
        else:
            logger.info("⚠️  No other participants in room yet")
            logger.info("   Join the room from another device/browser to test")

        logger.info("")
        logger.info("=" * 70)
        logger.info("🎤 Agent is now listening for events...")
        logger.info("=" * 70)
        logger.info("")
        logger.info("📋 How to test:")
        logger.info(f"  1. Go to: https://meet.livekit.io")
        logger.info(f"  2. Enter room name: {ROOM_NAME}")
        logger.info("  3. Click 'Join Room' (don't use 'Join with token')")
        logger.info("  4. Enable your microphone")
        logger.info("  5. SPEAK - watch terminal for track events!")
        logger.info("")
        logger.info(
            "⚠️  IMPORTANT: Join as a NEW participant (not with the agent token)"
        )
        logger.info("")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 70)
        logger.info("")

        # Keep the agent running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 70)
        logger.info("⏹️  Stopping test agent...")
        logger.info("=" * 70)
    except Exception as e:
        logger.error("=" * 70)
        logger.error(f"❌ Error occurred: {e}")
        logger.error("=" * 70)
        import traceback

        traceback.print_exc()
    finally:
        logger.info("🔌 Disconnecting from room...")
        await room.disconnect()
        logger.info("👋 Disconnected successfully")
        logger.info("")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
