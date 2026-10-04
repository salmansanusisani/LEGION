"""Booking lifecycle: create, list, lookup, cancel, amend, and atomic batch moves.

Every function that changes state opens exactly one store write transaction and
returns only after it commits, so a create, an amendment and a batch move each
land as a unit or not at all (sections 1 and 11). The two idempotent write paths
resolve their key inside that same transaction, which is what gives section 7 its
exactly-one-201 guarantee under concurrency.

Reference to section 8 for the refusal table, section 9 for local-time handling
and section 11 for batch ordering.
"""
from __future__ import annotations

from . import errors, idempotency, jsonutil, scheduling, timeutil, validation, views
from .config import MAX_ID_LENGTH, MAX_MOVES, MIN_MOVES
from .credentials import new_id, new_reference

_SELECT = (
    "SELECT id, reference, user_id, restaurant_id, table_id, party_size, status,"
    " starts_local, starts_us, ends_us, created_at, ordinal FROM reservations"
)


def _load_owned(connection, user_id: str, reference: str):
    """The caller's booking, or None.

    Section 8 requires 404 for another owner's booking *without leaking that it
    exists*, so the user filter is part of the lookup, not a later check.
    """
    return connection.execute(
        _SELECT + " WHERE reference = ? AND user_id = ?", (reference, user_id)
    ).fetchone()


def _require_owned(connection, user_id: str, reference: str):
    row = _load_owned(connection, user_id, reference)
    if row is None:
        raise errors.not_found("no such reservation for this caller")
    return row


def _restaurant_or_404(connection, restaurant_id: str):
    restaurant = scheduling.load(connection, restaurant_id)
    if restaurant is None:
        raise errors.not_found(f"no restaurant {restaurant_id}")
    return restaurant


def _next_ordinal(connection) -> int:
    row = connection.execute("SELECT COALESCE(MAX(ordinal), -1) + 1 AS next FROM reservations").fetchone()
    return int(row["next"])


def _fresh_reference(connection) -> str:
    """6 to 12 characters of ``A-Z0-9``, unique across all reservations.

    Eight characters over a 36-symbol alphabet is about 2.8e12 candidates, so a
    collision is vanishingly unlikely and the retry loop is a formality. The
    budget exists only so that a pathological run cannot spin while holding the
    write lock; it is far beyond any number of retries a real workload reaches.
    """
    for _ in range(1024):
        candidate = new_reference()
        taken = connection.execute(
            "SELECT 1 FROM reservations WHERE reference = ?", (candidate,)
        ).fetchone()
        if taken is None:
            return candidate
    raise errors.ApiError(500, "internal_error", "could not allocate a unique reference")


def _insert(connection, *, reservation_id, reference, user_id, restaurant, placement) -> dict:
    created_at = timeutil.now_micros()
    connection.execute(
        "INSERT INTO reservations(id, reference, user_id, restaurant_id, table_id,"
        " party_size, status, starts_local, starts_us, ends_us, created_at, ordinal)"
        " VALUES(?,?,?,?,?,?,'confirmed',?,?,?,?,?)",
        (
            reservation_id,
            reference,
            user_id,
            restaurant.id,
            placement.table_id,
            placement.party_size,
            placement.starts_local,
            placement.starts_us,
            placement.ends_us,
            created_at,
            _next_ordinal(connection),
        ),
    )
    return {
        "id": reservation_id,
        "reference": reference,
        "user_id": user_id,
        "restaurant_id": restaurant.id,
        "table_id": placement.table_id,
        "party_size": placement.party_size,
        "status": "confirmed",
        "starts_local": placement.starts_local,
        "starts_us": placement.starts_us,
        "ends_us": placement.ends_us,
        "created_at": created_at,
        "ordinal": 0,
    }


# -- reads ---------------------------------------------------------------


def listing(store, user_id: str) -> dict:
    with store.read() as connection:
        rows = connection.execute(
            _SELECT + " WHERE user_id = ? ORDER BY starts_us DESC, reference ASC",
            (user_id,),
        ).fetchall()
        # Section 8: the caller's own reservations, confirmed and cancelled alike,
        # newest start first.
        def restaurant_of(restaurant_id):
            return _restaurant_or_404(connection, restaurant_id)

        return {"reservations": views.reservations(rows, restaurant_of)}


def lookup(store, user_id: str, reference: str) -> dict:
    with store.read() as connection:
        row = _require_owned(connection, user_id, reference)
        return views.reservation(row, _restaurant_or_404(connection, row["restaurant_id"]))


# -- writes --------------------------------------------------------------


def create(store, user_id: str, body, key) -> tuple:
    with store.write() as connection:
        replay = idempotency.lookup(connection, user_id, key, body)
        if replay is not None:
            return idempotency.REPLAY_STATUS, replay

        restaurant_id = validation.string_field(body, "restaurant_id")
        table_id = validation.string_field(body, "table_id")
        naive = validation.local_datetime_field(body)
        party_size = validation.party_size_field(body)

        restaurant = _restaurant_or_404(connection, restaurant_id)
        table = scheduling.resolve_table(connection, restaurant, table_id)
        if table is None:
            raise errors.not_found(f"no table {table_id} at restaurant {restaurant_id}")

        placement = scheduling.placement_for(restaurant, table, naive, party_size)
        scheduling.ensure_free(connection, placement.table_id, placement.starts_us, placement.ends_us)

        row = _insert(
            connection,
            reservation_id=new_id("res"),
            reference=_fresh_reference(connection),
            user_id=user_id,
            restaurant=restaurant,
            placement=placement,
        )
        response = views.reservation(row, restaurant)
        idempotency.record(connection, user_id, key, body, 201, response, timeutil.now_micros())
        return 201, response


def cancel(store, user_id: str, reference: str) -> tuple:
    with store.write() as connection:
        row = _require_owned(connection, user_id, reference)
        restaurant = _restaurant_or_404(connection, row["restaurant_id"])
        if row["status"] == "cancelled":
            # Section 8: cancelling twice is not an error.
            return 200, views.reservation(row, restaurant)
        if scheduling.cutoff_passed(restaurant, row["starts_us"], timeutil.now_micros()):
            raise errors.cutoff_passed(
                f"this booking starts within {restaurant.cutoff} minutes"
            )
        connection.execute(
            "UPDATE reservations SET status = 'cancelled' WHERE id = ?", (row["id"],)
        )
        updated = dict(row)
        updated["status"] = "cancelled"
        return 200, views.reservation(updated, restaurant)


def _target_values(body, row):
    """Merge an amendment body over the current values. Omitted fields are kept."""
    table_id = validation.optional_string_field(body, "table_id")
    naive = validation.optional_local_datetime_field(body)
    if "party_size" in body:
        party_size = validation.party_size_field(body)
    else:
        party_size = row["party_size"]
    return (
        row["table_id"] if table_id is None else table_id,
        timeutil.parse_local(row["starts_local"]) if naive is None else naive,
        party_size,
    )


def amend(store, user_id: str, reference: str, body) -> tuple:
    with store.write() as connection:
        row = _require_owned(connection, user_id, reference)
        restaurant = _restaurant_or_404(connection, row["restaurant_id"])
        if row["status"] != "confirmed":
            raise errors.reservation_cancelled("this reservation is already cancelled")
        if scheduling.cutoff_passed(restaurant, row["starts_us"], timeutil.now_micros()):
            # Measured against the current start, per section 8.
            raise errors.cutoff_passed(
                f"this booking starts within {restaurant.cutoff} minutes"
            )

        table_id, naive, party_size = _target_values(body, row)
        table = scheduling.resolve_table(connection, restaurant, table_id)
        if table is None:
            raise errors.not_found(f"no table {table_id} at restaurant {restaurant.id}")

        placement = scheduling.placement_for(restaurant, table, naive, party_size)
        scheduling.ensure_free(
            connection,
            placement.table_id,
            placement.starts_us,
            placement.ends_us,
            exclude_ids=frozenset({row["id"]}),
        )

        connection.execute(
            "UPDATE reservations SET table_id = ?, party_size = ?, starts_local = ?,"
            " starts_us = ?, ends_us = ? WHERE id = ?",
            (
                placement.table_id,
                placement.party_size,
                placement.starts_local,
                placement.starts_us,
                placement.ends_us,
                row["id"],
            ),
        )
        updated = dict(row)
        updated.update({
            "table_id": placement.table_id,
            "party_size": placement.party_size,
            "starts_local": placement.starts_local,
            "starts_us": placement.starts_us,
            "ends_us": placement.ends_us,
        })
        # reference, reservation_id, owner and created_at are untouched.
        return 200, views.reservation(updated, restaurant)


# -- section 11: atomic moves -------------------------------------------


def _move_items(body) -> list:
    """Shape check for ``moves``. Section 11 makes every failure here 422."""
    if "moves" not in body:
        raise errors.validation_failed("moves is required")
    moves = body["moves"]
    if not jsonutil.is_list(moves):
        raise errors.validation_failed("moves must be an array")
    if not MIN_MOVES <= len(moves) <= MAX_MOVES:
        raise errors.validation_failed(
            f"moves must hold {MIN_MOVES} to {MAX_MOVES} items"
        )
    seen = set()
    items = []
    for item in moves:
        if not jsonutil.is_object(item):
            raise errors.validation_failed("each move must be a JSON object")
        reference = item.get("reference")
        if not jsonutil.is_string(reference) or not reference:
            raise errors.validation_failed("each move needs a string reference")
        if len(reference) > MAX_ID_LENGTH:
            raise errors.validation_failed("move reference is too long")
        if reference in seen:
            raise errors.validation_failed(f"duplicate move reference {reference}")
        seen.add(reference)
        items.append(item)
    return items


def _overlaps(first: scheduling.Placement, second: scheduling.Placement) -> bool:
    return first.starts_us < second.ends_us and second.starts_us < first.ends_us


def moves(store, user_id: str, body, key) -> tuple:
    with store.write() as connection:
        replay = idempotency.lookup(connection, user_id, key, body)
        if replay is not None:
            return idempotency.REPLAY_STATUS, replay

        items = _move_items(body)

        rows = []
        for item in items:
            rows.append(_require_owned(connection, user_id, item["reference"]))

        restaurant_ids = {row["restaurant_id"] for row in rows}
        if len(restaurant_ids) > 1:
            raise errors.validation_failed("every move must belong to the same restaurant")
        restaurant = _restaurant_or_404(connection, rows[0]["restaurant_id"])

        now = timeutil.now_micros()
        placements: list = []
        # Section 11: non-occupancy errors in input order, and for one booking
        # its cutoff error precedes its other changes.
        for item, row in zip(items, rows):
            if row["status"] != "confirmed":
                raise errors.reservation_cancelled(
                    f"{row['reference']} is already cancelled"
                )
            if scheduling.cutoff_passed(restaurant, row["starts_us"], now):
                raise errors.cutoff_passed(
                    f"{row['reference']} starts within {restaurant.cutoff} minutes"
                )
            table_id, naive, party_size = _target_values(item, row)
            table = scheduling.resolve_table(connection, restaurant, table_id)
            if table is None:
                raise errors.not_found(f"no table {table_id} at restaurant {restaurant.id}")
            placements.append(scheduling.placement_for(restaurant, table, naive, party_size))

        # Occupancy last, and only across the *resulting* set. The listed
        # bookings' own current occupancy is excluded, which is what lets two
        # eligible bookings swap tables in one atomic batch.
        listed = frozenset(row["id"] for row in rows)
        for index, placement in enumerate(placements):
            for other in range(index + 1, len(placements)):
                if placements[other].table_id == placement.table_id and _overlaps(
                    placement, placements[other]
                ):
                    raise errors.table_unavailable(
                        "two moved bookings would overlap on the same table"
                    )
            scheduling.ensure_free(
                connection, placement.table_id, placement.starts_us, placement.ends_us,
                exclude_ids=listed,
            )

        updated_rows = []
        for row, placement in zip(rows, placements):
            connection.execute(
                "UPDATE reservations SET table_id = ?, party_size = ?, starts_local = ?,"
                " starts_us = ?, ends_us = ? WHERE id = ?",
                (
                    placement.table_id,
                    placement.party_size,
                    placement.starts_local,
                    placement.starts_us,
                    placement.ends_us,
                    row["id"],
                ),
            )
            merged = dict(row)
            merged.update({
                "table_id": placement.table_id,
                "party_size": placement.party_size,
                "starts_local": placement.starts_local,
                "starts_us": placement.starts_us,
                "ends_us": placement.ends_us,
            })
            updated_rows.append(merged)

        response = {
            "reservations": [views.reservation(row, restaurant) for row in updated_rows]
        }
        idempotency.record(connection, user_id, key, body, 201, response, now)
        return 201, response
