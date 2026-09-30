#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

seat="${1:-}"
case "$seat" in
  coordinator|implementer|verifier|experience_reviewer) ;;
  *)
    echo "Usage: $0 {coordinator|implementer|verifier|experience_reviewer}" >&2
    exit 2
    ;;
esac

if [[ ! -x .venv/bin/python ]]; then
  echo "Missing .venv. Run: uv sync --python 3.12" >&2
  exit 1
fi

export BAND_SEAT="$seat"
exec .venv/bin/python factory/agent.py

