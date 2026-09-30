#!/usr/bin/env bash
set -u

cd "$(dirname "$0")/.."
failed=0

check_command() {
  if command -v "$1" >/dev/null 2>&1; then
    printf 'OK      %s\n' "$1"
  else
    printf 'MISSING %s\n' "$1"
    failed=1
  fi
}

check_command git
check_command docker
check_command opencode

if command -v band-desktop >/dev/null 2>&1; then
  echo "OK      band-desktop"
else
  echo "MISSING band-desktop (download the official Linux .deb)"
  failed=1
fi

if [[ -x .venv/bin/python ]] && .venv/bin/python -c \
  'from band.adapters import OpencodeAdapter, OpencodeAdapterConfig' 2>/dev/null; then
  echo "OK      BAND OpenCode adapter"
else
  echo "MISSING BAND OpenCode adapter"
  failed=1
fi

if opencode models opencode 2>/dev/null | grep -qx 'opencode/big-pickle'; then
  echo "OK      opencode/big-pickle"
else
  echo "MISSING opencode/big-pickle access"
  failed=1
fi

if [[ -f agent_config.yaml ]]; then
  echo "OK      agent_config.yaml"
else
  echo "PENDING agent_config.yaml (create four BAND Remote Agents first)"
  failed=1
fi

if docker info >/dev/null 2>&1; then
  echo "OK      Docker daemon access"
else
  echo "BLOCKED Docker daemon access for the current user"
  failed=1
fi

exit "$failed"
