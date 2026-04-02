#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo '{"error":"No audio file provided"}' >&2
  exit 1
fi

AUDIO_FILE="$1"

if [ ! -f "$AUDIO_FILE" ]; then
  echo "{\"error\":\"File not found: $AUDIO_FILE\"}" >&2
  exit 1
fi

curl -s \
  -X POST \
  http://127.0.0.1:8765 \
  -H "Content-Type: application/json" \
  -d "{\"file\":\"$AUDIO_FILE\"}"
