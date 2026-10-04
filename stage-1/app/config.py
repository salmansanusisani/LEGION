"""Process configuration read once at start-up."""
from __future__ import annotations

import os

DEFAULT_PORT = 8080
BIND_HOST = "0.0.0.0"
DEFAULT_DB_PATH = "/data/tablekeeper.sqlite3"

# A fixture or import is a single JSON document; anything larger is a client bug
# and must not be allowed to consume the 2 GiB memory limit.
MAX_BODY_BYTES = 8 * 1024 * 1024

# Section 3.4 caps opaque ids, including ids supplied by a reset fixture.
MAX_ID_LENGTH = 64

# Section 7 caps the client-chosen idempotency key.
MAX_IDEMPOTENCY_KEY = 255

# Section 11 caps a batch move.
MIN_MOVES = 1
MAX_MOVES = 8

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
WEEKDAY_INDEX = {name: index for index, name in enumerate(WEEKDAYS)}

# scrypt work factors. n=2**13 with r=8 costs 8 MiB per hash and ~50 ms on the
# 2 vCPU grading profile, so 50 concurrent logins finish well inside the 5 s
# per-request budget while remaining a memory-hard KDF. See README.md.
SCRYPT_N = int(os.environ.get("TABLEKEEPER_SCRYPT_N", "8192"))
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 32


def port() -> int:
    raw = os.environ.get("PORT", "").strip()
    if not raw:
        return DEFAULT_PORT
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_PORT
    return value if 0 < value < 65536 else DEFAULT_PORT


def db_path() -> str:
    return os.environ.get("TABLEKEEPER_DB") or DEFAULT_DB_PATH
