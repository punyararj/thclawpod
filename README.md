# Clawdpod

Talk to Clawdbot through Apple HomePod.

Clawdpod bridges HomePod's voice interface to [Clawdbot](https://github.com/clawdbot/clawdbot), letting you have conversations with your AI assistant through any HomePod in your home.

## How It Works

```
You: "Hey Siri, Call Dobby"
    ↓
iOS Shortcut activates, listens
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

## Requirements

- Apple HomePod (any model)
- iPhone/iPad for creating the Shortcut
- Server running [Clawdbot](https://github.com/clawdbot/clawdbot)
- Python 3.11+ with [uv](https://github.com/astral-sh/uv)
- Network connectivity between HomePod and server

## Quick Start

### 1. Start the Server

```bash
git clone https://github.com/yourusername/clawpod
cd clawpod

# Run the server (uv handles dependencies)
uv run clawpod_server.py
```

Server listens on `0.0.0.0:7001` by default.

### 2. Create the iOS Shortcut

See [SHORTCUT.md](SHORTCUT.md) for step-by-step instructions.

The shortcut:
1. Greets you ("This is Dobby")
2. Loops: listens → sends to server → speaks response
3. Exits when you say "thank you"

### 3. Test It

```bash
curl -X POST http://localhost:7001/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "What time is it?", "speaker": "Alexis"}'
```

Then try: "Hey Siri, Call Dobby"

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAWDPOD_HOST` | `0.0.0.0` | Bind address |
| `CLAWDPOD_PORT` | `7001` | Listen port |
| `CLAWDPOD_LOG_LEVEL` | `INFO` | Logging level |
| `CLAWDPOD_API_TOKEN` | (none) | Optional bearer token |
| `CLAWDPOD_AGENT` | `main` | Clawdbot agent to use |
| `CLAWDPOD_TIMEOUT` | `60` | Response timeout (seconds) |
| `CLAWDPOD_SESSION_PREFIX` | `homepod` | Session ID prefix |

## API

### POST /chat

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
  "reply": "It's currently 62°F and partly cloudy.",
  "end_conversation": false
}
```

### GET /health

Health check, no auth required.

## Conversation Flow

1. "Hey Siri, Call Dobby" — Shortcut starts, greets you
2. Speak naturally — your input is sent to Clawdbot
3. Listen to response — Siri speaks Clawdbot's reply
4. Continue or end — say "thank you" to exit

## Security

- Traffic is unencrypted by default
- Set `CLAWDPOD_API_TOKEN` to require bearer auth
- Consider a reverse proxy for TLS if exposed beyond your network

## Limitations

- Pull-only: Clawdbot cannot initiate conversations
- Synchronous: request-response only, no streaming
- Siri-dependent: STT/TTS quality depends on Siri
- Network required: HomePod must reach the server

## Troubleshooting

**Server not responding**
- Check server is running: `curl http://server:7001/health`
- Verify network connectivity
- Check firewall rules

**Clawdbot not found**
- Ensure clawdbot is installed and in PATH
- Check volta/npm-global paths

**Slow responses**
- Check Clawdbot gateway status
- Increase `CLAWDPOD_TIMEOUT`

## License

MIT
