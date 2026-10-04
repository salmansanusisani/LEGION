"""The single error type every transport path understands.

Section 5 of the specification requires every 4xx and 5xx response to carry
``{"error": {"code": ..., "message": ...}}`` with a status and code drawn from
its table, or from an endpoint-specific row. Raising ``ApiError`` is the only
way an endpoint reports a refusal, which keeps the mapping from "what went
wrong" to "what the caller sees" in one place.
"""
from __future__ import annotations


class ApiError(Exception):
    """A refusal the caller can see. ``message`` wording is free per section 5."""

    __slots__ = ("status", "code", "message")

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message

    def body(self) -> dict:
        return {"error": {"code": self.code, "message": self.message}}


def malformed_request(message: str = "the request body is not a JSON object") -> ApiError:
    return ApiError(400, "malformed_request", message)


def missing_idempotency_key() -> ApiError:
    return ApiError(400, "missing_idempotency_key", "an Idempotency-Key header is required")


def unauthenticated(message: str = "a valid bearer token is required") -> ApiError:
    return ApiError(401, "unauthenticated", message)


def forbidden(message: str = "this caller may not touch this resource") -> ApiError:
    return ApiError(403, "forbidden", message)


def not_found(message: str = "no such resource") -> ApiError:
    return ApiError(404, "not_found", message)


def email_taken(message: str = "that email is already registered") -> ApiError:
    return ApiError(409, "email_taken", message)


def idempotency_key_reuse(
    message: str = "this idempotency key was already used with a different request",
) -> ApiError:
    return ApiError(409, "idempotency_key_reuse", message)


def table_unavailable(message: str = "that table is taken for an overlapping interval") -> ApiError:
    return ApiError(409, "table_unavailable", message)


def cutoff_passed(message: str = "the cancellation cutoff for this booking has passed") -> ApiError:
    return ApiError(409, "cutoff_passed", message)


def reservation_cancelled(message: str = "this reservation is cancelled") -> ApiError:
    return ApiError(409, "reservation_cancelled", message)


def validation_failed(message: str = "the request failed validation") -> ApiError:
    return ApiError(422, "validation_failed", message)


def not_on_slot_grid(message: str = "the requested local start is not on the slot grid") -> ApiError:
    return ApiError(422, "not_on_slot_grid", message)


def outside_opening_hours(message: str = "the requested slot is outside opening hours") -> ApiError:
    return ApiError(422, "outside_opening_hours", message)


def party_exceeds_capacity(message: str = "the party is larger than this table holds") -> ApiError:
    return ApiError(422, "party_exceeds_capacity", message)


def invalid_local_time(message: str = "that local time does not exist in this zone") -> ApiError:
    return ApiError(422, "invalid_local_time", message)
