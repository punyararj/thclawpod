#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "fastapi",
#     "uvicorn[standard]",
# ]
# ///
"""
Clawpod: HomePod ↔ Clawdbot voice bridge.

A FastAPI server that receives voice transcriptions from an iOS Shortcut
running on HomePod, routes them to Clawdbot, and returns spoken responses.

Architecture:
    HomePod → "Hey Siri, Call Dobby"
        → iOS Shortcut (STT)
        → POST /chat to this server
        → openclaw agent CLI
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
import httpx
import strip_markdown
import re

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

HOST = os.getenv("CLAWPOD_HOST", "0.0.0.0")
PORT = int(os.getenv("CLAWPOD_PORT", "7001"))
LOG_LEVEL = os.getenv("CLAWPOD_LOG_LEVEL", "INFO")
API_TOKEN = os.getenv("CLAWPOD_API_TOKEN")  # Optional auth
TH_CLAW_TOKEN = os.getenv("TH_CLAW_TOKEN")
TH_CLAW_URL = os.getenv("TH_CLAW_URL")

# Clawdbot settings
CLAWDBOT_AGENT = os.getenv("CLAWPOD_AGENT", "main")
CLAWDBOT_TIMEOUT = int(os.getenv("CLAWPOD_TIMEOUT", "60"))
TH_CLAW_HOME = os.getenv("TH_CLAW_HOME",".")

# Session prefix for HomePod conversations
SESSION_PREFIX = os.getenv("CLAWPOD_SESSION_PREFIX", "homepod")

# End-of-conversation phrases (either party can say these)
END_PHRASES = [
    "goodbye",
    "that's all", 
    "thats all",  # smart apostrophe variant
    "end conversation",
    "bye for now",
    "แค่นี้นะ",
    "จบ",
    "แค่นี้แหละ",
    "ขอบคุณนะ",
    "ขอบใจ",
    "ยินดีให้บริการครับ"
]

# Logging
logging.basicConfig(level=LOG_LEVEL.upper())
logger = logging.getLogger("thclawpod")
user_session:dict[str, str] = {}
if os.path.exists("user_session.json"):
    with open("user_session.json") as f:
        user_session = json.load(f)

if os.path.exists(f'{TH_CLAW_HOME.rstrip("/")}/.thclaws/sessions'):
    for sess in user_session:
        sess_key = user_session[sess]
        if not os.path.exists(sess_key):
            del user_session[sess]

def set_user_session(speaker: str, session_id: str) -> None:
    user_session[speaker] = session_id
    with open("user_session.json", "w") as f:
        json.dump(user_session, f)


def strip_markdown_and_emoji(text: str) -> str:
    # 1. Strip Markdown formatting (bold, headers, links, etc.)
    text = strip_markdown.strip_markdown(text)

    # 2. Regex to remove all Unicode emojis and symbols
    # Matches all characters outside the Basic Multilingual Plane (BMP)
    emoji_pattern = re.compile(
        u'([\U00002600-\U000027BF])|'
        u'([\U0001f300-\U0001f64F])|'
        u'([\U0001f680-\U0001f6FF])|'
        u'([\U0001f1e6-\U0001f1ff])|'
        u'([\U0001f900-\U0001f9ff])',
        flags=re.UNICODE
    )

    # Remove emojis and strip any extra leading/trailing whitespace
    return emoji_pattern.sub(r'', text).strip()

app = FastAPI(title="THClawpod", version="1.0.0")

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

class THClawAgentRequest(BaseModel):
    """Request to THClawbot agent."""
    prompt: str
    model: str
    session_id: str
    workspace_dir: str
    stream: bool


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

def get_session_id(speaker: str) -> str|None:
    """
    Derive session ID from speaker name.
    
    This allows different family members to have distinct conversation
    contexts, or everyone can share one session.
    """
    # Normalize speaker name
    speaker_key = speaker.lower().strip().replace(" ", "-")
    if not speaker_key or speaker_key == "unknown":
        speaker_key = "family"
    if speaker_key in user_session:
        return user_session[speaker_key]
    return None



async def call_openclaw(message: str, session_id: str, speaker: str) -> str:
    """
    Call openclaw agent CLI and return the response.
    
    Args:
        message: User's transcribed speech
        session_id: Session identifier for conversation continuity
        speaker: Speaker name for context
        
    Returns:
        Agent's response text
    """
    async with httpx.AsyncClient() as client:
        session_id = get_session_id(speaker)
        headers = {'Content-Type': 'application/json'}
        if TH_CLAW_TOKEN:
            headers.update({"Authorization": f"Bearer {TH_CLAW_TOKEN}"})
        payload = {
            "prompt": message,
            "model": "gemini-2.5-flash",
            "workspace_dir": "/workspace/",
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 4096,
        }
        if session_id:
            payload["session_id"] = session_id
        url = f'{TH_CLAW_URL}/agent/run'
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=CLAWDBOT_TIMEOUT)
            if response.status_code == 200:
                response_json = response.json()
                response_text = response_json["summary"]
                response_text = strip_markdown_and_emoji(response_text)
                response_session_id = response_json["session_id"]
                set_user_session(speaker, response_session_id)
                return response_text
            else:
                logger.error(f"Server return {response.status_code}")
                return "การประมวลผลผิดพลาดต้องการลองใหม่ไหมคะ"
        except httpx.TimeoutException:
            logger.error("openclaw timed out")
            return "การประมวลผลใช้เวลานานเกินไป ลองใหม่ไหมคะ"


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
    return {"status": "healthy", "service": "clawpod"}


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
    
    # Get session and call Clawdbot
    session_id = get_session_id(speaker)

    reply = await call_openclaw(text, session_id, speaker)
    end_conversation = is_end_phrase(text)
    # Check if agent wants to end conversation

    
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
    
    logger.info(f"Starting Clawpod on {HOST}:{PORT}")
    logger.info(f"Agent: {CLAWDBOT_AGENT}, Session prefix: {SESSION_PREFIX}")
    
    uvicorn.run(app, host=HOST, port=PORT, log_level=LOG_LEVEL.lower())
