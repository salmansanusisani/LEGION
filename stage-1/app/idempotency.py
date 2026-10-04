"""Section 7 idempotency, resolved as early as the specification allows.

The mandated order inside a write handler is:

1. the body parses as a JSON object
2. the caller authenticates
3. the ``Idempotency-Key`` is present (400) and within 1..255 characters (422)
4. **the key resolves** -- replay (200) or conflict (409)
5. only then endpoint field validation and current-resource checks

So a used key with a different, invalid body still answers
``409 idempotency_key_reuse``. Receipts are only written for a 2xx outcome, which
is what makes "key reused after a 4xx is treated as a first use" fall out for
free.

Concurrency falls out of the store: a receipt lookup and the write that follows
it happen inside one serialized write transaction, so N identical requests on one
unused key produce one 201 and N-1 replays with the operation applied once.
"""
from __future__ import annotations

from . import errors, jsonutil
from .config import MAX_IDEMPOTENCY_KEY

REPLAY_STATUS = 200


class Key:
    __slots__ = ("value", "method", "path")

    def __init__(self, value: str, method: str, path: str) -> None:
        self.value = value
        self.method = method
        self.path = path


def read_key(headers, method: str, path: str) -> Key:
    """The ``Idempotency-Key`` header, or the section 5/7 refusal for it.

    Absent or empty is 400 ``missing_idempotency_key``; present but longer than
    255 characters is 422 ``validation_failed`` from the shared range table.
    """
    raw = headers.get("Idempotency-Key")
    if raw is None:
        raise errors.missing_idempotency_key()
    value = raw.strip()
    if not value:
        raise errors.missing_idempotency_key()
    if len(value) > MAX_IDEMPOTENCY_KEY:
        raise errors.validation_failed(
            f"Idempotency-Key must be at most {MAX_IDEMPOTENCY_KEY} characters"
        )
    return Key(value, method, path)


def lookup(connection, user_id: str, key: Key, body):
    """Return the original response body for a replay, or None for a first use.

    The key is scoped to the authenticated user, and a replay additionally needs
    the same method, the same path and the same parsed JSON value. A different
    path with the same key is a different request and falls through to normal
    handling, as section 7 requires.
    """
    row = connection.execute(
        "SELECT request_json, response_json FROM receipts"
        " WHERE user_id = ? AND key = ? AND method = ? AND path = ?",
        (user_id, key.value, key.method, key.path),
    ).fetchone()
    if row is None:
        return None
    try:
        original = jsonutil.loads(row["request_json"].encode("utf-8"))
    except errors.ApiError:
        original = None
    if not jsonutil.same_value(original, body):
        raise errors.idempotency_key_reuse(
            "this idempotency key was already used with a different request body"
        )
    return jsonutil.loads(row["response_json"].encode("utf-8"))


def record(connection, user_id: str, key: Key, body, status: int, response, created_at: int) -> None:
    """Store the receipt for a successful outcome, inside the same transaction."""
    connection.execute(
        "INSERT INTO receipts(user_id, key, method, path, request_json, status_code,"
        " response_json, created_at) VALUES(?,?,?,?,?,?,?,?)",
        (
            user_id,
            key.value,
            key.method,
            key.path,
            jsonutil.canonical(body),
            status,
            jsonutil.canonical(response),
            created_at,
        ),
    )
