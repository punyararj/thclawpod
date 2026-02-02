# TODO

- [ ] End-to-end test with actual HomePod (scheduled for tomorrow AM)
- [ ] finalize end phrases for agent to end convo.

## Someday/maybe

- [ ] Document use of CLAWD_AGENT to segregate dialogs into sessions
- [ ] Document dynamic speaker identification using HomePod voice recognition instead of hardcoded name
  - (Personal Content / Recognize My Voice, family member enrollment) etc.
- [ ] Add systemd service file for daemonized linux operation
- [ ] Add launchd plist example for macOS users
- [ ] refactor away from `openclaw` CLI, to use dedicated RPC/http gateway for better latency.
- [ ] Add instructions for publicly hosted gateways, secured server.
