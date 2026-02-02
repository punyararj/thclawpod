# TODO

## Shortcut Improvements

- [ ] Check `end_conversation` field from server response, exit if true (allows Clawdbot to end conversation)
- [ ] Support multiple end phrases ("goodbye", "that's all", not just "thank you")
- [ ] Dynamic speaker identification using HomePod voice recognition instead of hardcoded name

## Server

- [ ] Add systemd service file for daemonized operation
- [ ] Configurable greeting message
- [ ] Session timeout/cleanup for stale conversations

## Documentation

- [ ] Document HomePod voice recognition setup (Personal Content / Recognize My Voice, family member enrollment)
- [ ] Add launchd plist example for macOS users

## Testing

- [ ] End-to-end test with actual HomePod (scheduled for tomorrow AM)
- [ ] Test multi-speaker scenarios
- [ ] Test timeout handling
