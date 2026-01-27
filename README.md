# Clawdpod 🦞🎙️

**Talk to your Clawdbot through Apple HomePod.**

Clawdpod bridges Apple HomePod's voice interface to [Clawdbot](https://github.com/clawdbot/clawdbot), letting you have natural conversations with your AI assistant through any HomePod in your home.

## How It Works

```
You: "Hey Siri, Call Dobby"
    ↓
iOS Shortcut activates, listens to your voice
    ↓
Speech-to-text via Siri
    ↓
POST /chat → Clawdpod server
    ↓
clawdbot agent CLI
    ↓
Response returned
    ↓
Text-to-speech via Siri
    ↓
HomePod speaks the reply
```

### Key Features

- **Voice Recognition**: HomePod can identify family members by voice, routing each person to their own conversation context
- **Conversation Continuity**: Multi-turn conversations within a session
- **Full Clawdbot Power**: Access to all your Clawdbot tools, memory, and personality
- **Natural Termination**: Say "goodbye" or "that's all" to end the conversation

## Requirements

- Apple HomePod (any model)
- iPhone/iPad for creating the Shortcut
- Mac/Linux server running [Clawdbot](https://github.com/clawdbot/clawdbot)
- Python 3.11+ with [uv](https://github.com/astral-sh/uv)
- Network connectivity between HomePod and server

## Quick Start

### 1. Start the Server

```bash
# Clone the repo
git clone https://github.com/yourusername/clawdpod
cd clawdpod

# Run the server (uv handles dependencies automatically)
uv run clawdpod_server.py
```

Server listens on `0.0.0.0:7001` by default.

### 2. Create the iOS Shortcut

See [SHORTCUT.md](SHORTCUT.md) for step-by-step instructions with screenshots.

**Quick overview:**
1. Open Shortcuts app on iPhone
2. Create new shortcut named "Call Dobby"
3. Add actions: Dictate → POST to server → Speak response → Loop
4. Enable for Siri: "Hey Siri, Call Dobby"

### 3. Test It

```bash
# From another terminal
curl -X POST http://localhost:7001/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "What time is it?", "speaker": "Alexis"}'
```

Then try on HomePod: **"Hey Siri, Call Dobby"**

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAWDPOD_HOST` | `0.0.0.0` | Bind address |
| `CLAWDPOD_PORT` | `7001` | Listen port |
| `CLAWDPOD_LOG_LEVEL` | `INFO` | Logging level |
| `CLAWDPOD_API_TOKEN` | (none) | Optional bearer token for auth |
| `CLAWDPOD_AGENT` | `main` | Clawdbot agent to use |
| `CLAWDPOD_TIMEOUT` | `60` | Response timeout (seconds) |
| `CLAWDPOD_SESSION_PREFIX` | `homepod` | Session ID prefix |

## API

### `POST /chat`

Send a voice transcription, get a response.

**Request:**
```json
{
  "text": "What's the weather like?",
  "speaker": "Alexis"
}
```

**Response:**
```json
{
  "reply": "It's currently 62°F and partly cloudy in San Francisco.",
  "end_conversation": false
}
```

The `speaker` field enables per-person conversation contexts. HomePod can recognize household members by voice and the iOS Shortcut can pass this to the server.

### `GET /health`

Health check (no auth required).

```json
{"status": "healthy", "service": "clawdpod"}
```

## Conversation Flow

1. **User initiates**: "Hey Siri, Call Dobby"
2. **Loop begins**: Shortcut listens, sends to server, speaks response
3. **Continue or end**: 
   - Keep talking to continue
   - Say "goodbye" or "that's all" to end
   - Or the assistant can end with those phrases
4. **Shortcut exits** when `end_conversation: true`

## Speaker Recognition

HomePod can recognize different family members' voices. The iOS Shortcut can access this and pass it to Clawdpod:

- Each speaker gets their own session: `homepod:alexis`, `homepod:odysseus`, etc.
- Unknown speakers use: `homepod:family`
- Clawdbot maintains separate context per session

## Security Considerations

- **Network**: Run on a private network or use a VPN
- **Auth Token**: Set `CLAWDPOD_API_TOKEN` for bearer auth
- **HTTPS**: Consider a reverse proxy (nginx/caddy) for TLS
- **Firewall**: Restrict access to trusted IPs

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   HomePod    │────▶│   Clawdpod   │────▶│   Clawdbot   │
│   (Siri)     │◀────│   (FastAPI)  │◀────│   (Agent)    │
└──────────────┘     └──────────────┘     └──────────────┘
     voice              HTTP/JSON           CLI/Session
     
- HomePod: Voice I/O via Siri
- Clawdpod: HTTP bridge, session routing
- Clawdbot: AI agent with tools, memory, personality
```

## Limitations

- **Pull-only**: Clawdbot cannot initiate conversations to HomePod
- **Synchronous**: Request-response only, no streaming
- **Siri dependency**: STT/TTS quality depends on Siri
- **Network required**: HomePod must reach the server

## Troubleshooting

**"Server not responding"**
- Check server is running: `curl http://your-server:7001/health`
- Verify network connectivity from iPhone to server
- Check firewall rules

**"Clawdbot not found"**
- Ensure Clawdbot is installed and in PATH
- Check volta/npm-global paths

**"Authentication failed"**
- Verify `CLAWDPOD_API_TOKEN` matches Shortcut header

**Slow responses**
- Check Clawdbot gateway status
- Consider increasing `CLAWDPOD_TIMEOUT`
- Check network latency

## Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT

## Credits

- [Clawdbot](https://github.com/clawdbot/clawdbot) - The AI agent platform
- Inspired by the desire to talk to AI assistants naturally at home
