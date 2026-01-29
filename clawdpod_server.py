#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "fastapi",
#     "uvicorn[standard]",
# ]
# ///
"""
Clawdpod: HomePod ↔ Clawdbot voice bridge.

A FastAPI server that receives voice transcriptions from an iOS Shortcut
running on HomePod, routes them to Clawdbot, and returns spoken responses.

Architecture:
    HomePod → "Hey Siri, Call Dobby"
        → iOS Shortcut (STT)
        → POST /chat to this server
        → clawdbot agent CLI
        → response spoken aloud (TTS)
"""

import os
import asyncio
import json
import logging
import shutil
import subprocess
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

HOST = os.getenv("CLAWDPOD_HOST", "0.0.0.0")
PORT = int(os.getenv("CLAWDPOD_PORT", "7001"))
LOG_LEVEL = os.getenv("CLAWDPOD_LOG_LEVEL", "INFO")
API_TOKEN = os.getenv("CLAWDPOD_API_TOKEN")  # Optional auth

# Clawdbot settings
CLAWDBOT_AGENT = os.getenv("CLAWDPOD_AGENT", "main")
CLAWDBOT_TIMEOUT = int(os.getenv("CLAWDPOD_TIMEOUT", "60"))

# Session prefix for HomePod conversations
SESSION_PREFIX = os.getenv("CLAWDPOD_SESSION_PREFIX", "homepod")

# End-of-conversation phrases (either party can say these)
END_PHRASES = [
    "goodbye",
    "that's all", 
    "thats all",  # smart apostrophe variant
    "end conversation",
    "bye for now",
]

# Logging
logging.basicConfig(level=LOG_LEVEL.upper())
logger = logging.getLogger("clawdpod")

app = FastAPI(title="Clawdpod", version="1.0.0")

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """Incoming chat request from iOS Shortcut."""
    text: str
    speaker: str = "Unknown"  # From Siri voice recognition


class ChatResponse(BaseModel):
    """Response back to iOS Shortcut."""
    reply: str
    end_conversation: bool = False


# -----------------------------------------------------------------------------
# Auth
# -----------------------------------------------------------------------------

def require_auth(request: Request) -> None:
    """Optional bearer token auth."""
    if not API_TOKEN:
        return
    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")


# -----------------------------------------------------------------------------
# Clawdbot Integration
# -----------------------------------------------------------------------------

def get_session_id(speaker: str) -> str:
    """
    Derive session ID from speaker name.
    
    This allows different family members to have distinct conversation
    contexts, or everyone can share one session.
    """
    # Normalize speaker name
    speaker_key = speaker.lower().strip().replace(" ", "-")
    if not speaker_key or speaker_key == "unknown":
        speaker_key = "family"
    return f"{SESSION_PREFIX}:{speaker_key}"


def find_clawdbot() -> str:
    """Find the clawdbot CLI, preferring volta-managed version."""
    # Try volta path first
    volta_path = os.path.expanduser("~/.volta/bin/clawdbot")
    if os.path.exists(volta_path):
        return volta_path
    
    # Try npm-global
    npm_path = os.path.expanduser("~/.npm-global/bin/clawdbot")
    if os.path.exists(npm_path):
        return npm_path
    
    # Fall back to PATH
    path = shutil.which("clawdbot")
    if path:
        return path
    
    raise RuntimeError("clawdbot not found in volta, npm-global, or PATH")


async def call_clawdbot(message: str, session_id: str, speaker: str) -> str:
    """
    Call clawdbot agent CLI and return the response.
    
    Args:
        message: User's transcribed speech
        session_id: Session identifier for conversation continuity
        speaker: Speaker name for context
        
    Returns:
        Agent's response text
    """
    clawdbot = find_clawdbot()
    
    # Prepend speaker context to message
    contextualized_message = f"[HomePod, speaker: {speaker}] {message}"
    
    cmd = [
        clawdbot,
        "agent",
        "--message", contextualized_message,
        "--session-id", session_id,
        "--agent", CLAWDBOT_AGENT,
        "--timeout", str(CLAWDBOT_TIMEOUT),
        "--json",
    ]
    
    logger.info(f"Calling clawdbot: session={session_id} speaker={speaker}")
    logger.debug(f"Command: {' '.join(cmd)}")
    
    # Set up environment with volta
    env = os.environ.copy()
    volta_home = os.path.expanduser("~/.volta")
    env["VOLTA_HOME"] = volta_home
    env["PATH"] = f"{volta_home}/bin:" + env.get("PATH", "")
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=CLAWDBOT_TIMEOUT + 10
        )
        
        if proc.returncode != 0:
            logger.error(f"clawdbot error (exit {proc.returncode}): {stderr.decode()}")
            return "Sorry, I'm having trouble connecting right now. Try again in a moment."
        
        # Parse JSON response
        # clawdbot --json returns: {"result": {"payloads": [{"text": "..."}]}}
        result = json.loads(stdout.decode())
        payloads = result.get("result", {}).get("payloads", [])
        reply = payloads[0].get("text", "") if payloads else ""
        
        if not reply:
            logger.warning(f"Empty reply from clawdbot: {result}")
            return "I'm not sure how to respond to that."
            
        return reply.strip()
        
    except asyncio.TimeoutError:
        logger.error("clawdbot timed out")
        return "Sorry, that took too long. Try again?"
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse clawdbot response: {e}")
        return "Sorry, something went wrong."
    except Exception as e:
        logger.error(f"clawdbot call failed: {e}")
        return "Sorry, I couldn't process that request."


def is_end_phrase(text: str) -> bool:
    """Check if text contains an end-of-conversation phrase."""
    text_lower = text.lower().strip()
    return any(phrase in text_lower for phrase in END_PHRASES)


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@app.get("/health")
async def health():
    """Health check endpoint (no auth required)."""
    return {"status": "healthy", "service": "clawdpod"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, _: None = Depends(require_auth)):
    """
    Process voice input and return Clawdbot's response.
    
    The iOS Shortcut sends:
        - text: Transcribed speech from Siri
        - speaker: Recognized speaker name (if available)
    
    Returns:
        - reply: Text to be spoken aloud
        - end_conversation: True if conversation should end
    """
    text = request.text.strip()
    speaker = request.speaker.strip() or "Unknown"
    
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    logger.info(f"Chat request: speaker={speaker} text={text[:50]}...")
    
    # Check if user wants to end conversation
    if is_end_phrase(text):
        return ChatResponse(
            reply="Goodbye! Talk to you later.",
            end_conversation=True
        )
    
    # Get session and call Clawdbot
    session_id = get_session_id(speaker)
    reply = await call_clawdbot(text, session_id, speaker)
    
    # Check if agent wants to end conversation
    end_conversation = is_end_phrase(reply)
    
    logger.info(f"Response: end={end_conversation} reply={reply[:50]}...")
    
    return ChatResponse(
        reply=reply,
        end_conversation=end_conversation
    )


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting Clawdpod on {HOST}:{PORT}")
    logger.info(f"Agent: {CLAWDBOT_AGENT}, Session prefix: {SESSION_PREFIX}")
    
    uvicorn.run(app, host=HOST, port=PORT, log_level=LOG_LEVEL.lower())
