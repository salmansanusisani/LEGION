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
check_command band

if command -v band-desktop >/dev/null 2>&1; then
  echo "OK      band-desktop"
else
  echo "MISSING band-desktop (download the official Linux .deb)"
  failed=1
fi

if band whoami >/dev/null 2>&1; then
  echo "OK      BAND account"
else
  echo "MISSING BAND account (run: band init)"
  failed=1
fi

if opencode models opencode 2>/dev/null | grep -qx 'opencode/big-pickle'; then
  echo "OK      opencode/big-pickle"
else
  echo "MISSING opencode/big-pickle access"
  failed=1
fi

agent_count="$(band list 2>/dev/null | grep -c 'salmansanusi90/legion-' || true)"
if [[ "$agent_count" == "4" ]]; then
  echo "OK      four persistent LEGION seats"
else
  echo "MISSING four persistent LEGION seats (found $agent_count)"
  failed=1
fi

if docker info >/dev/null 2>&1; then
  echo "OK      Docker daemon access"
else
  echo "BLOCKED Docker daemon access for the current user"
  failed=1
fi

exit "$failed"
