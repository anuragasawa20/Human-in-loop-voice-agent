# Voice Demo Guide

Follow these steps to talk to the salon agent through LiveKit.

---

## 1. Start the Voice Agent

```bash
cd /Users/mavens/Human-in-the-loop-Agent/agent
uv run agent.py dev
```

Leave this terminal running. It connects your worker to LiveKit Cloud using the credentials in `agent/.env.local` (`LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`).

---

## 2. Generate a Meet Token

Open a new terminal:

```bash
cd /Users/mavens/Human-in-the-loop-Agent/agent
python generate_meet_token.py
```

The script prints:

- **LiveKit Server URL** – this is the same value as `LIVEKIT_URL` in `agent/.env.local`
- **Token** – a fresh JWT tied to the Meet participant

Copy both values—each run generates a new participant identity, so repeat this step whenever you want a clean join.

---

## 3. Join from meet.livekit.io

1. Visit [https://meet.livekit.io](https://meet.livekit.io)
2. Click the **Custom** tab
3. Paste the **LiveKit Server URL** into the `LiveKit Server URL` field
4. Paste the **Token** into the `Token` field
5. Click **Connect**
6. Allow microphone access

You should now see the agent session appear in the room. If it does not, make sure the worker from step 1 is still running and that no other participant is using the same token/identity.

---

## 4. Talk to the Agent

- Ask questions like “What are your hours?” or “Do you offer bridal packages?”
- Listen for the agent’s responses in real time
- To end the call, press **Leave** in the Meet UI; the agent disconnects automatically

If you need to reconnect, run `generate_meet_token.py` again for a fresh token and repeat step 3.

---

## Troubleshooting

- **Duplicate identity error:** Wait for the previous session to close or request a new token.
- **No audio:** Confirm your microphone is selected in Meet and not muted on your machine.
- **Agent not joining:** Ensure `uv run agent.py dev` is still running and that `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` are correctly set in `agent/.env.local`.

Enjoy your voice demo!


