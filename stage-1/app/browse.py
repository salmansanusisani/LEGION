"""Section 8 browsing: the restaurant list, restaurant detail and availability.

All three are public. Availability is a single pass over the day's slots with one
occupancy query per slot, so a restaurant with many tables still answers inside
the 5 s per-request budget.
"""
from __future__ import annotations

from . import errors, scheduling, timeutil, validation


def list_restaurants(store) -> dict:
    with store.read() as connection:
        rows = connection.execute(
            "SELECT id, name, timezone FROM restaurants ORDER BY ordinal, id"
        ).fetchall()
        return {"restaurants": [
            {"id": row["id"], "name": row["name"], "timezone": row["timezone"]}
            for row in rows
        ]}


def get_restaurant(store, restaurant_id: str) -> dict:
    with store.read() as connection:
        restaurant = scheduling.load(connection, restaurant_id)
        if restaurant is None:
            raise errors.not_found(f"no restaurant {restaurant_id}")
        return restaurant.detail(scheduling.tables_of(connection, restaurant_id))


def availability(store, query) -> dict:
    """``GET /availability``.

    All three parameters are required and each is validated on its own, so
    omitting any one of them is 422 before the restaurant is even looked up. A
    closed weekday simply produces an empty slot list.
    """
    restaurant_id = validation.query_string(query, "restaurant_id")
    raw_date = validation.query_string(query, "date")
    party_size = validation.query_integer(query, "party_size")

    day = timeutil.parse_date(raw_date)
    if day is None:
        raise errors.validation_failed("date must be a real YYYY-MM-DD calendar date")

    with store.read() as connection:
        restaurant = scheduling.load(connection, restaurant_id)
        if restaurant is None:
            raise errors.not_found(f"no restaurant {restaurant_id}")
        tables = scheduling.tables_of(connection, restaurant_id)

        slots = []
        for naive, starts_us, ends_us in scheduling.day_slots(restaurant, day):
            slots.append({
                "starts_at_local": timeutil.format_local(naive),
                "starts_at": timeutil.rfc3339(timeutil.from_micros(starts_us, restaurant.zone)),
                "available_table_ids": scheduling.available_tables(
                    connection, restaurant, tables, party_size, starts_us, ends_us
                ),
            })
        return {
            "restaurant_id": restaurant.id,
            "date": day.isoformat(),
            "timezone": restaurant.timezone,
            "slots": slots,
        }
