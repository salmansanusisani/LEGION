#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v opencode >/dev/null 2>&1; then
  echo "OpenCode is not on PATH." >&2
  exit 1
fi

exec opencode serve --hostname=127.0.0.1 --port="${OPENCODE_PORT:-4096}"

