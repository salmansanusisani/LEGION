"""Request validation.

This module is the only place that decides between the two refusal shapes
section 5 draws:

* a value of the **wrong JSON type** -> 400 ``malformed_request``
* a correctly typed value that is missing, badly formatted or out of range ->
  422 ``validation_failed``

Endpoint-specific rules win over that default. Section 5 says so explicitly for
``party_size`` (strings and booleans included) and for ``starts_at_local`` that is
not a bare local ``YYYY-MM-DDTHH:MM``; both are 422 here regardless of what the
generic rule would have said.
"""
from __future__ import annotations

import re

from . import errors, jsonutil
from .config import MAX_ID_LENGTH
from .timeutil import parse_local

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+$")
DIGITS_PATTERN = re.compile(r"^[0-9]+$")

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 1024
MAX_DISPLAY_NAME = 200


# -- body fields ---------------------------------------------------------


def _required(body: dict, name: str):
    if name not in body:
        raise errors.validation_failed(f"{name} is required")
    return body[name]


def string_field(body: dict, name: str, *, max_length: int = MAX_ID_LENGTH) -> str:
    value = _required(body, name)
    if not jsonutil.is_string(value):
        raise errors.malformed_request(f"{name} must be a string")
    if not value:
        raise errors.validation_failed(f"{name} must not be empty")
    if len(value) > max_length:
        raise errors.validation_failed(f"{name} must be at most {max_length} characters")
    return value


def optional_string_field(body: dict, name: str, *, max_length: int = MAX_ID_LENGTH):
    """PATCH semantics: absent means "keep the current value"."""
    if name not in body:
        return None
    return string_field(body, name, max_length=max_length)


def party_size_field(body: dict, name: str = "party_size") -> int:
    """Section 5 and section 8: anything but an integer of at least 1 is 422.

    ``is_integer`` excludes booleans, so ``true`` is 422 and not 400, and the
    range check runs before any storage.

    No upper bound is imposed here. Section 8 makes an oversized party
    ``party_exceeds_capacity``, which the table comparison in
    :func:`app.scheduling.check_placement` decides, so an arbitrarily large
    ``party_size`` must reach that comparison rather than be refused here as an
    unstated range violation. Section 5 only promises 422 for values beyond *a
    stated maximum*, and section 8 states none for this field.
    """
    value = _required(body, name)
    if not jsonutil.is_integer(value):
        raise errors.validation_failed(f"{name} must be an integer")
    if value < 1:
        raise errors.validation_failed(f"{name} must be at least 1")
    return value


def local_datetime_field(body: dict, name: str = "starts_at_local"):
    value = _required(body, name)
    if not jsonutil.is_string(value):
        raise errors.malformed_request(f"{name} must be a string")
    naive = parse_local(value)
    if naive is None:
        raise errors.validation_failed(f"{name} must be a bare local YYYY-MM-DDTHH:MM")
    return naive


def optional_local_datetime_field(body: dict, name: str = "starts_at_local"):
    if name not in body:
        return None
    return local_datetime_field(body, name)


def email_field(body: dict, name: str = "email") -> str:
    value = _required(body, name)
    if not jsonutil.is_string(value):
        raise errors.malformed_request(f"{name} must be a string")
    if not EMAIL_PATTERN.match(value):
        raise errors.validation_failed(f"{name} must have the form local@domain")
    return value


def optional_email_field(body: dict, name: str = "email"):
    if name not in body:
        return None
    return email_field(body, name)


def password_field(body: dict, name: str = "password") -> str:
    value = _required(body, name)
    if not jsonutil.is_string(value):
        raise errors.malformed_request(f"{name} must be a string")
    if len(value) < MIN_PASSWORD_LENGTH:
        raise errors.validation_failed(
            f"{name} must be at least {MIN_PASSWORD_LENGTH} characters"
        )
    if len(value) > MAX_PASSWORD_LENGTH:
        raise errors.validation_failed(f"{name} is too long")
    return value


def optional_password_field(body: dict, name: str = "password"):
    """Login only: a wrong password is 401, never a length complaint.

    The eight-character minimum is a signup rule. Applying it to login would
    turn "wrong password" into 422 for any short guess, which contradicts the
    section 6 table.
    """
    if name not in body:
        raise errors.validation_failed(f"{name} is required")
    value = body[name]
    if not jsonutil.is_string(value):
        raise errors.malformed_request(f"{name} must be a string")
    if len(value) > MAX_PASSWORD_LENGTH:
        raise errors.validation_failed(f"{name} is too long")
    return value


def display_name_field(body: dict, email: str) -> str:
    """``display_name`` is echoed back but never given a stated range.

    Absent or null falls back to the local part of the email rather than
    refusing a signup the specification does not describe as invalid.
    """
    value = body.get("display_name")
    if value is None:
        return email.split("@", 1)[0]
    if not jsonutil.is_string(value):
        raise errors.malformed_request("display_name must be a string")
    if len(value) > MAX_DISPLAY_NAME:
        raise errors.validation_failed("display_name is too long")
    return value


# -- query parameters ----------------------------------------------------


def query_string(query: dict, name: str) -> str:
    values = query.get(name)
    if not values or not values[0]:
        raise errors.validation_failed(f"query parameter {name} is required")
    value = values[0]
    if len(value) > MAX_ID_LENGTH:
        raise errors.validation_failed(f"{name} must be at most {MAX_ID_LENGTH} characters")
    return value


# Any integer with more significant digits than this exceeds every capacity a
# fixture can hold, so the comparison result is already decided. Parsing stops
# there, which keeps an unbounded digit string from becoming a denial of service
# without inventing a maximum the specification never states.
_UNSIGNED_SIGNIFICANT_DIGITS = 18
_UNSIGNED_CEILING = 10**_UNSIGNED_SIGNIFICANT_DIGITS


def query_integer(query: dict, name: str, *, minimum: int = 1) -> int:
    """Section 5: an integer query parameter is plain decimal digits.

    ``1e9``, ``4.0`` and ``+4`` are all 422 whatever their numeric value, so the
    text is matched against ``[0-9]+`` and never coerced. Leading zeros are still
    plain decimal digits, so ``0004`` is the integer 4.

    There is no stated maximum for an availability ``party_size``, so none is
    enforced: a very long digit string saturates at :data:`_UNSIGNED_CEILING`,
    which is larger than any capacity and therefore yields the same empty
    availability a genuinely huge party must produce.
    """
    values = query.get(name)
    if not values or values[0] == "":
        raise errors.validation_failed(f"query parameter {name} is required")
    raw = values[0]
    if not DIGITS_PATTERN.match(raw):
        raise errors.validation_failed(f"query parameter {name} must be plain decimal digits")
    significant = raw.lstrip("0")
    if len(significant) > _UNSIGNED_SIGNIFICANT_DIGITS:
        value = _UNSIGNED_CEILING
    else:
        value = int(significant) if significant else 0
    if value < minimum:
        raise errors.validation_failed(f"query parameter {name} must be at least {minimum}")
    return value
