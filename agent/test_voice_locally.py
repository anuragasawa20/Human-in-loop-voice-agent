#!/usr/bin/env python3
"""
Simple voice test script to interact with the AI agent locally.

This script:
1. Connects to LiveKit using your microphone
2. Allows you to speak to the AI agent
3. Plays AI responses through your speakers
4. Shows transcript in the terminal

"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment
load_dotenv(".env.local")

try:
    from livekit import rtc, api
except ImportError:
    print("❌ Error: livekit package not installed")
    print("Install with: uv add livekit")
    sys.exit(1)


class VoiceTester:
    """Simple voice test client for the AI agent."""

    def __init__(self):
        """Initialize the voice tester."""
        self.room = None
        self.audio_source = None
        self.connected = False

        # LiveKit configuration
        self.livekit_url = os.getenv("LIVEKIT_URL")
        self.livekit_api_key = os.getenv("LIVEKIT_API_KEY")
        self.livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")

        if not all([self.livekit_url, self.livekit_api_key, self.livekit_api_secret]):
            print("❌ Error: LiveKit credentials not configured")
            print("Set LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET in .env.local")
            sys.exit(1)

    def generate_token(self, room_name: str, participant_name: str) -> str:
        """
        Generate a LiveKit access token.

        Args:
            room_name: Name of the room to join
            participant_name: Name of the participant

        Returns:
            JWT token for LiveKit connection
        """
        token = api.AccessToken(self.livekit_api_key, self.livekit_api_secret)
        token.with_identity(participant_name)
        token.with_name(participant_name)
        token.with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )

        return token.to_jwt()

    async def connect(self, room_name: str = "voice-test"):
        """
        Connect to LiveKit room.

        Args:
            room_name: Name of the room (default: voice-test)
        """
        print("🔌 Connecting to LiveKit...")
        print(f"   Room: {room_name}")
        print(f"   URL: {self.livekit_url}")
        print()

        # Generate token
        token = self.generate_token(room_name, "voice-tester")

        # Create room
        self.room = rtc.Room()

        # Set up event handlers
        @self.room.on("track_subscribed")
        def on_track_subscribed(
            track: rtc.Track,
            publication: rtc.TrackPublication,
            participant: rtc.RemoteParticipant,
        ):
            """Handle new audio track from AI agent."""
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                print(f"🔊 AI agent audio track received")
                # Audio will play automatically through speakers

        @self.room.on("data_received")
        def on_data_received(data: bytes, participant: rtc.Participant):
            """Handle transcription data from agent."""
            try:
                import json

                message = json.loads(data.decode())

                if message.get("type") == "transcription":
                    speaker = message.get("speaker", "unknown")
                    text = message.get("text", "")

                    if speaker == "user":
                        print(f"\n👤 You: {text}")
                    elif speaker == "agent":
                        print(f"\n🤖 AI: {text}")
            except Exception as e:
                pass

        @self.room.on("disconnected")
        def on_disconnected():
            """Handle disconnection."""
            print("\n🔴 Disconnected from LiveKit")
            self.connected = False

        # Connect to room
        try:
            await self.room.connect(self.livekit_url, token)
            self.connected = True
            print("✅ Connected to LiveKit!")
            print()

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            raise

    async def start_audio(self):
        """Start publishing microphone audio."""
        print("🎤 Starting microphone...")

        try:
            # Create audio source from microphone
            self.audio_source = rtc.AudioSource(sample_rate=48000, num_channels=1)

            # Create track
            track = rtc.LocalAudioTrack.create_audio_track(
                "microphone", self.audio_source
            )

            # Publish track
            await self.room.local_participant.publish_track(track)

            print("✅ Microphone active - You can speak now!")
            print()
            print("=" * 60)
            print("VOICE TEST ACTIVE")
            print("=" * 60)
            print()
            print("Try saying:")
            print("  - 'What are your hours?'")
            print("  - 'How much is a haircut?'")
            print("  - 'Do you offer bridal packages?'")
            print()
            print("Press Ctrl+C to stop")
            print("=" * 60)
            print()

        except Exception as e:
            print(f"❌ Failed to start microphone: {e}")
            print("\nMake sure:")
            print("  1. Microphone is connected")
            print("  2. Microphone permission is granted")
            print("  3. No other app is using the microphone")
            raise

    async def disconnect(self):
        """Disconnect from LiveKit."""
        if self.room:
            await self.room.disconnect()

        self.connected = False
        print("\n👋 Disconnected")

    async def run(self):
        """Run the voice test."""
        try:
            # Connect to LiveKit
            await self.connect()

            # Start microphone
            await self.start_audio()

            # Keep running until interrupted
            while self.connected:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping voice test...")
            await self.disconnect()

        except Exception as e:
            print(f"\n❌ Error: {e}")
            await self.disconnect()
            raise


async def main():
    """Main function."""
    print()
    print("=" * 60)
    print("🎙️  VOICE TEST - Beauty Salon AI Agent")
    print("=" * 60)
    print()
    print("This will connect to your AI agent using your microphone.")
    print()

    # Check prerequisites
    print("📋 Checking prerequisites...")
    print()

    # Check if agent is running
    import httpx

    backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{backend_url}/health", timeout=2.0)
            if response.status_code == 200:
                print(f"✅ Backend running ({backend_url})")
            else:
                print(f"⚠️  Backend returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Backend not reachable ({backend_url})")
        print(f"   Error: {e}")
        print()
        print("Please start the backend:")
        print("  cd backend && uv run uvicorn main:app --reload")
        print()
        return

    print()
    print("⚠️  IMPORTANT: Make sure the agent is running!")
    print("   Terminal: cd agent && uv run agent.py dev")
    print()

    # Wait for confirmation
    try:
        input("Press Enter when agent is ready (or Ctrl+C to cancel)...")
        print()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        return

    # Run voice test
    tester = VoiceTester()
    await tester.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
