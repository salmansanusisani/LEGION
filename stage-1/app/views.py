"""Response shapes.

One place builds a reservation body, so create, list, lookup, cancel, amend,
batch move, export and import all agree field for field (section 8).
"""
from __future__ import annotations

from . import timeutil


def reservation(row, restaurant) -> dict:
    """The section 8 reservation shape.

    ``starts_at_local`` is the stored bare local string, so it always goes back
    into ``POST /reservations`` unchanged, and ``starts_at``/``ends_at`` carry the
    zone's offset for that date. ``ends_at`` is absolute elapsed time, which on a
    fall-back night reads an hour earlier than wall-clock subtraction would.
    """
    return {
        "reservation_id": row["id"],
        "reference": row["reference"],
        "restaurant_id": row["restaurant_id"],
        "table_id": row["table_id"],
        "party_size": row["party_size"],
        "status": row["status"],
        "starts_at_local": row["starts_local"],
        "starts_at": timeutil.rfc3339(timeutil.from_micros(row["starts_us"], restaurant.zone)),
        "ends_at": timeutil.rfc3339(timeutil.from_micros(row["ends_us"], restaurant.zone)),
        "created_at": timeutil.rfc3339_utc(row["created_at"]),
    }


def reservations(rows, loader) -> list:
    """Serialise an ordered result set, loading each row's restaurant once."""
    cache: dict = {}
    out = []
    for row in rows:
        restaurant = cache.get(row["restaurant_id"])
        if restaurant is None:
            restaurant = loader(row["restaurant_id"])
            cache[row["restaurant_id"]] = restaurant
        out.append(reservation(row, restaurant))
    return out
