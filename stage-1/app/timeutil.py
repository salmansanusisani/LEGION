"""IANA local-time resolution for section 9.

Three rules drive this module:

* A local time in a spring-forward gap does not exist. Booking one is
  ``invalid_local_time`` and it never appears in availability.
* A local time in a fall-back repeated hour occurs twice and always resolves to
  the **first** occurrence, the one before the clocks change. ``zoneinfo``
  already does this for ``fold=0``, which is what :func:`resolve_local` asks for.
* ``reservation_duration_minutes`` is absolute elapsed time. Every instant is
  carried as integer microseconds since the epoch, so wall-clock arithmetic can
  never leak into an occupancy decision.

Nothing here reads the host time zone: every conversion takes an explicit
:class:`~zoneinfo.ZoneInfo`.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

LOCAL_PATTERN = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$")
DATE_PATTERN = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
CLOCK_PATTERN = re.compile(r"^(\d{2}):(\d{2})$")

UTC = timezone.utc
MICROS = 1_000_000
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


class UnknownZone(ValueError):
    pass


def zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        raise UnknownZone(name) from exc


def parse_local(text: str):
    """``YYYY-MM-DDTHH:MM`` -> naive datetime, or None when it is not bare.

    Section 5 fixes this as the only accepted ``starts_at_local`` spelling: no
    offset, no ``Z``, no seconds. A well-formed shape carrying an impossible
    calendar value (``2026-02-30``) is also rejected here, as a format failure.
    """
    match = LOCAL_PATTERN.match(text or "")
    if match is None:
        return None
    year, month, day, hour, minute = (int(part) for part in match.groups())
    try:
        return datetime(year, month, day, hour, minute)
    except ValueError:
        return None


def parse_date(text: str):
    match = DATE_PATTERN.match(text or "")
    if match is None:
        return None
    year, month, day = (int(part) for part in match.groups())
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_clock(text: str):
    """``HH:MM`` local 24-hour -> minutes past local midnight, or None."""
    match = CLOCK_PATTERN.match(text or "")
    if match is None:
        return None
    hour, minute = int(match.group(1)), int(match.group(2))
    if hour > 23 or minute > 59:
        return None
    return hour * 60 + minute


def resolve_local(naive: datetime, tz: ZoneInfo):
    """Naive restaurant-local time -> aware instant, or None if it does not exist.

    ``fold=0`` is the documented first occurrence of a repeated local time.
    A naive time is non-existent exactly when a round trip through UTC changes
    its wall-clock reading, which is the only reliable test available.
    """
    first = naive.replace(tzinfo=tz, fold=0)
    if first.astimezone(UTC).astimezone(tz).replace(tzinfo=None) != naive:
        return None
    return first


def to_micros(moment: datetime) -> int:
    """Integer microseconds since the epoch.

    Exact integer arithmetic rather than ``timestamp() * MICROS``: a float would
    round a microsecond-scale instant, and an occupancy decision that compares
    instants must never be decided by a rounding artefact.
    """
    return (moment.astimezone(UTC) - EPOCH) // timedelta(microseconds=1)


def from_micros(value: int, tz: ZoneInfo) -> datetime:
    seconds, remainder = divmod(int(value), MICROS)
    return (EPOCH + timedelta(seconds=seconds, microseconds=remainder)).astimezone(tz)


def rfc3339(moment: datetime) -> str:
    """RFC 3339 with an explicit offset, per section 3.4.

    ``isoformat`` on an aware datetime always emits the offset, so a response
    can never leak a naive or offset-less timestamp.
    """
    return moment.isoformat(timespec="seconds")


def rfc3339_utc(value: int) -> str:
    return from_micros(value, UTC).isoformat(timespec="seconds")


def format_local(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M")


def now_micros() -> int:
    return to_micros(datetime.now(UTC))


def naive_at(day: date, minutes: int) -> datetime:
    return datetime(day.year, day.month, day.day) + timedelta(minutes=minutes)
