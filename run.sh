#!/bin/bash
# Run ruslan-desktop with API key from ~/.hermes/.env
set -a
source <(grep '^OPENCODE_GO_API_KEY' ~/.hermes/.env 2>/dev/null | head -1)
HERMES_API_KEY=$OPENCODE_GO_API_KEY
HERMES_API_URL=https://opencode.ai/zen/go/v1
VOICE_ENABLED=true
set +a
cd ~/Desktop/ruslan-desktop
exec python3.12 -m core.main
