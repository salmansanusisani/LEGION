"""JSON parsing, encoding and the small type predicates the validation layer uses.

Section 3.4 fixes the media type; section 5 separates a body that does not parse
or carries a wrong JSON type (400 ``malformed_request``) from a correctly typed
value that is out of range or badly formatted (422 ``validation_failed``).
Keeping both decisions in one module makes that boundary auditable.
"""
from __future__ import annotations

import json

from . import errors


def _reject_constant(name: str):
    # json.loads accepts NaN/Infinity by default; they are not JSON and would
    # poison the canonical form used for idempotency body comparison.
    raise ValueError(f"{name} is not a JSON value")


def loads(raw: bytes):
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise errors.malformed_request("the request body is not valid UTF-8") from exc
    try:
        return json.loads(text, parse_constant=_reject_constant)
    except ValueError as exc:
        raise errors.malformed_request("the request body is not valid JSON") from exc


def load_object(raw: bytes) -> dict:
    """Parse a body that section 7 requires to be a JSON object.

    Idempotency resolves *after* this, so an unparseable or non-object body is
    refused before the key is even looked at.
    """
    value = loads(raw)
    if not isinstance(value, dict):
        raise errors.malformed_request("the request body must be a JSON object")
    return value


def encode(value) -> bytes:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def canonical(value) -> str:
    """A stable textual form of a parsed JSON value.

    Section 7: "same body" means the same JSON value after parsing, so key order
    and whitespace are irrelevant. Sorting keys and dropping whitespace makes
    two spellings of one value compare equal.
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def same_value(left, right) -> bool:
    try:
        return canonical(left) == canonical(right)
    except (TypeError, ValueError):
        return False


def is_string(value) -> bool:
    return isinstance(value, str)


def is_integer(value) -> bool:
    """A JSON integer. Booleans are excluded: section 5 calls them invalid."""
    return isinstance(value, int) and not isinstance(value, bool)


def is_object(value) -> bool:
    return isinstance(value, dict)


def is_list(value) -> bool:
    return isinstance(value, list)
