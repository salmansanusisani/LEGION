"""Opening hours, the slot grid, daylight-saving resolution and occupancy rules.

Everything that decides *when* a booking may exist lives here, and every rule
below is stated in section 8 or section 9:

* slots step from ``opens`` by ``slot_minutes`` and only exist while the whole
  reservation still fits before ``closes``;
* a local time in a spring-forward gap does not exist, so it is never offered and
  booking it is ``invalid_local_time``;
* a local time in a fall-back repeated hour resolves to its first occurrence;
* occupancy is the half-open interval ``[starts, starts + duration)``.

The order of the refusals is fixed here so that create, amend and batch-move all
answer identically, which is what sections 8, 9 and 11 ask for.
"""
from __future__ import annotations

from datetime import date, datetime

from . import errors, store, timeutil
from .config import WEEKDAY_INDEX, WEEKDAYS

MICROS_PER_MINUTE = 60 * timeutil.MICROS


def weekday_index(day: date) -> int:
    """``date.weekday()``, which is already Monday==0 like ``config.WEEKDAYS``.

    ``strftime("%a")`` would also produce the right name but only by accident:
    it is locale-dependent, and a container with a non-English ``LC_TIME`` would
    silently look up a weekday the fixture never wrote.
    """
    return day.weekday()


def weekday_name(index: int) -> str:
    return WEEKDAYS[index]


class Restaurant:
    """A fixture-shaped restaurant plus its resolved zone and hours."""

    __slots__ = (
        "id", "name", "timezone", "slot_minutes", "duration", "cutoff",
        "ordinal", "hours", "zone",
    )

    def __init__(self, row, hours, zone) -> None:
        self.id = row["id"]
        self.name = row["name"]
        self.timezone = row["timezone"]
        self.slot_minutes = row["slot_minutes"]
        self.duration = row["reservation_duration_minutes"]
        self.cutoff = row["cancellation_cutoff_minutes"]
        self.ordinal = row["ordinal"]
        self.hours = hours
        self.zone = zone

    def day_hours(self, day: date):
        """``(opens, closes)`` in local minutes past midnight, or None when closed.

        Section 4: a weekday with no entry is closed.
        """
        return self.hours.get(weekday_index(day))

    def end_of(self, starts_us: int) -> int:
        """Absolute elapsed time. Section 9: duration is not wall-clock."""
        return starts_us + self.duration * MICROS_PER_MINUTE

    def summary(self) -> dict:
        return {"id": self.id, "name": self.name, "timezone": self.timezone}

    def detail(self, tables: list) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "timezone": self.timezone,
            "slot_minutes": self.slot_minutes,
            "reservation_duration_minutes": self.duration,
            "cancellation_cutoff_minutes": self.cutoff,
            "opening_hours": [
                {
                    "weekday": hour["weekday"],
                    "opens": _clock(hour["opens_min"]),
                    "closes": _clock(hour["closes_min"]),
                }
                for hour in self.hours.values()
            ],
            "tables": [
                {"id": table["id"], "label": table["label"], "capacity": table["capacity"]}
                for table in tables
            ],
        }


def _clock(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def load(connection, restaurant_id: str):
    """Fetch a restaurant, or None. Callers turn None into 404 ``not_found``."""
    row = connection.execute(
        "SELECT id, name, timezone, slot_minutes, reservation_duration_minutes,"
        " cancellation_cutoff_minutes, ordinal FROM restaurants WHERE id = ?",
        (restaurant_id,),
    ).fetchone()
    if row is None:
        return None
    hours = {}
    for hour in connection.execute(
        "SELECT weekday, opens_min, closes_min, ordinal FROM opening_hours"
        " WHERE restaurant_id = ? ORDER BY ordinal",
        (restaurant_id,),
    ):
        hours[WEEKDAY_INDEX[hour["weekday"]]] = {
            "weekday": hour["weekday"],
            "opens_min": hour["opens_min"],
            "closes_min": hour["closes_min"],
        }
    return Restaurant(row, hours, timeutil.zone(row["timezone"]))


def tables_of(connection, restaurant_id: str) -> list:
    return list(connection.execute(
        "SELECT id, restaurant_id, label, capacity, ordinal FROM tables"
        " WHERE restaurant_id = ? ORDER BY ordinal",
        (restaurant_id,),
    ))


# -- availability --------------------------------------------------------


def day_slots(restaurant: Restaurant, day: date) -> list:
    """Every offerable start on ``day``, as ``(naive_local, starts_us, ends_us)``.

    Section 8: step from ``opens`` while ``slot + duration <= closes``. Section 9:
    a start in a spring-forward gap does not exist and is skipped, and a start in
    a fall-back repeated hour resolves to its first occurrence, which this loop
    produces naturally because it walks distinct local times once.
    """
    hours = restaurant.day_hours(day)
    if hours is None:
        return []
    opens, closes = hours["opens_min"], hours["closes_min"]
    span = closes - opens - restaurant.duration
    if span < 0:
        return []
    slots = []
    offset = 0
    while offset <= span:
        naive = timeutil.naive_at(day, opens + offset)
        instant = timeutil.resolve_local(naive, restaurant.zone)
        if instant is not None:
            starts_us = timeutil.to_micros(instant)
            slots.append((naive, starts_us, restaurant.end_of(starts_us)))
        offset += restaurant.slot_minutes
    return slots


def occupancy_map(connection, table_ids: list, starts_us: int, ends_us: int) -> dict:
    """Confirmed reservations touching ``[starts_us, ends_us)`` per table.

    One query for a whole slot, so availability cost is a single statement rather
    than one per table.
    """
    found: dict = {}
    if not table_ids:
        return found
    placeholders = ",".join("?" for _ in table_ids)
    rows = connection.execute(
        "SELECT table_id FROM reservations"
        f" WHERE table_id IN ({placeholders}) AND status = 'confirmed'"
        "   AND starts_us < ? AND ends_us > ?",
        [*table_ids, ends_us, starts_us],
    )
    for row in rows:
        found[row["table_id"]] = True
    return found


def available_tables(connection, restaurant: Restaurant, tables: list, party_size: int,
                     starts_us: int, ends_us: int) -> list:
    """Tables with ``capacity >= party_size`` and no overlapping confirmed booking.

    Section 8 fixes the order: the restaurant's fixture order.
    """
    eligible = [table for table in tables if table["capacity"] >= party_size]
    busy = occupancy_map(connection, [table["id"] for table in eligible], starts_us, ends_us)
    return [table["id"] for table in eligible if table["id"] not in busy]


# -- booking and amendment validation ------------------------------------


class Placement:
    """A fully validated booking or amendment target."""

    __slots__ = ("table_id", "party_size", "starts_local", "naive", "starts_us", "ends_us")

    def __init__(self, table_id, party_size, starts_local, naive, starts_us, ends_us) -> None:
        self.table_id = table_id
        self.party_size = party_size
        self.starts_local = starts_local
        self.naive = naive
        self.starts_us = starts_us
        self.ends_us = ends_us


def resolve_table(connection, restaurant: Restaurant, table_id: str):
    """The table, or None when unknown or owned by another restaurant.

    Section 8 folds both cases into one 404 so the caller cannot tell them apart.
    """
    row = connection.execute(
        "SELECT id, restaurant_id, label, capacity, ordinal FROM tables"
        " WHERE id = ? AND restaurant_id = ?",
        (table_id, restaurant.id),
    ).fetchone()
    return row


def place_instant(restaurant: Restaurant, naive: datetime):
    """Restaurant-local wall clock -> ``(starts_us, ends_us)``, or ``(0, 0)``.

    Section 9: the duration is absolute elapsed time, so ``ends_us`` is derived
    from the instant and never from wall-clock subtraction. A local time that
    does not exist has no instant at all; the zero pair is a sentinel that
    :func:`check_placement` turns into ``invalid_local_time`` before any caller
    can use it, and a real instant is never zero.
    """
    instant = timeutil.resolve_local(naive, restaurant.zone)
    if instant is None:
        return 0, 0
    starts_us = timeutil.to_micros(instant)
    return starts_us, restaurant.end_of(starts_us)


def check_placement(restaurant: Restaurant, table, naive: datetime, party_size: int) -> None:
    """Apply section 8's refusal table to a proposed booking.

    Order, fixed here so create, amend and batch move agree:

    1. capacity               -> ``party_exceeds_capacity``
    2. the local time exists  -> ``invalid_local_time``  (before the grid, because
       section 9 guarantees a skipped time is refused as *that*, not as off-grid)
    3. the day and window     -> ``outside_opening_hours``
    4. the slot grid          -> ``not_on_slot_grid``

    Steps 1 and 3 follow the order section 8's own table lists. Step 2 is placed
    before step 3 because section 9 states unconditionally that booking a
    skipped local time *is* ``invalid_local_time``, and before step 4 because a
    time that does not exist cannot meaningfully be called off-grid.

    Occupancy is deliberately not checked here; the store decides it inside the
    writing transaction.
    """
    if party_size > table["capacity"]:
        raise errors.party_exceeds_capacity(
            f"table {table['id']} seats {table['capacity']}"
        )

    if timeutil.resolve_local(naive, restaurant.zone) is None:
        raise errors.invalid_local_time(
            f"{naive.strftime('%Y-%m-%dT%H:%M')} does not exist in {restaurant.timezone}"
        )

    hours = restaurant.day_hours(naive.date())
    if hours is None:
        raise errors.outside_opening_hours(
            f"{weekday_name(weekday_index(naive.date()))} is closed at {restaurant.name}"
        )
    opens, closes = hours["opens_min"], hours["closes_min"]
    start_minutes = naive.hour * 60 + naive.minute
    if start_minutes < opens:
        raise errors.outside_opening_hours(
            f"the restaurant opens at {_clock(opens)}"
        )
    if start_minutes + restaurant.duration > closes:
        raise errors.outside_opening_hours(
            f"a {restaurant.duration}-minute reservation would end after {_clock(closes)}"
        )

    if (start_minutes - opens) % restaurant.slot_minutes:
        raise errors.not_on_slot_grid(
            f"starts step by {restaurant.slot_minutes} minutes from {_clock(opens)}"
        )


def placement_for(restaurant: Restaurant, table, naive: datetime, party_size: int) -> Placement:
    """Validate a proposed booking against an already-resolved table row.

    The caller resolves the table first so that "unknown table" is a 404 before
    any business rule runs, exactly as section 8's table separates them.
    """
    starts_us, ends_us = place_instant(restaurant, naive)
    check_placement(restaurant, table, naive, party_size)
    return Placement(table["id"], party_size, timeutil.format_local(naive), naive, starts_us, ends_us)


def ensure_free(connection, table_id: str, starts_us: int, ends_us: int,
                exclude_ids=frozenset()) -> None:
    """Refuse an overlapping booking, half-open interval, inside the transaction."""
    if store.conflicting_reservation(
        connection, table_id, starts_us, ends_us, exclude_ids=exclude_ids
    ):
        raise errors.table_unavailable(
            f"table {table_id} is already taken for that interval"
        )


def cutoff_passed(restaurant: Restaurant, starts_us: int, now_us: int) -> bool:
    """Section 8: cancellation is refused within ``cutoff`` minutes of the start.

    Measured against the *current* start time, so an amendment is judged on the
    booking it already holds, never on the time it is proposing.
    """
    return starts_us - now_us <= restaurant.cutoff * MICROS_PER_MINUTE
