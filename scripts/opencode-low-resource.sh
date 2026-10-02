#!/usr/bin/env bash
set -euo pipefail

available_kib=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
if (( available_kib < 2097152 )); then
  printf 'Runtime blocked: less than 2 GiB available RAM (%s KiB).\n' "$available_kib" >&2
  exit 75
fi

# Fail a competing launch rather than creating a second memory-heavy worker.
# The operator starts the next seat after the current seat's turn and runtime end.
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
export PATH="$script_dir/infra-bin:$PATH"
exec flock --nonblock --conflict-exit-code 75 "/tmp/legion-opencode-${UID}.lock" \
  nice -n 10 taskset -c 0,1 opencode "$@"
