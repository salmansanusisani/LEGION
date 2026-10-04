"""Section 10 export and import.

Export is a read-only snapshot taken inside one deferred transaction, so it is
coherent even while writes are landing, and later writes cannot change it. The
``state`` object is deliberately logical rather than physical: accounts with
their password hashes, bearer tokens, fixture configuration, reservations with
their references, and every completed idempotent request with the body that
created it and the response it produced. It contains no file path, port, process
or network detail, which is what lets an unchanged export from one container
import into a fresh container at a different port.

Import is replacement inside one write transaction: validate the whole document
first, then wipe and rewrite, so a rejected import leaves the destination exactly
as it was.
"""
from __future__ import annotations

from . import errors, fixtures, jsonutil, store

TRACK = "tablekeeper"
FORMAT_VERSION = 1


def snapshot(connection) -> dict:
    users = [
        {
            "id": row["id"],
            "email": row["email"],
            "password_hash": row["password_hash"],
            "display_name": row["display_name"],
            "created_at": row["created_at"],
        }
        for row in connection.execute(
            "SELECT id, email, password_hash, display_name, created_at FROM users ORDER BY id"
        )
    ]
    tokens = [
        {"token": row["token"], "user_id": row["user_id"], "created_at": row["created_at"]}
        for row in connection.execute(
            "SELECT token, user_id, created_at FROM tokens ORDER BY user_id, token"
        )
    ]

    hours_by_restaurant: dict = {}
    for row in connection.execute(
        "SELECT restaurant_id, weekday, opens_min, closes_min FROM opening_hours"
        " ORDER BY restaurant_id, ordinal"
    ):
        hours_by_restaurant.setdefault(row["restaurant_id"], []).append({
            "weekday": row["weekday"],
            "opens": f"{row['opens_min'] // 60:02d}:{row['opens_min'] % 60:02d}",
            "closes": f"{row['closes_min'] // 60:02d}:{row['closes_min'] % 60:02d}",
        })

    tables_by_restaurant: dict = {}
    for row in connection.execute(
        "SELECT id, restaurant_id, label, capacity FROM tables ORDER BY restaurant_id, ordinal"
    ):
        tables_by_restaurant.setdefault(row["restaurant_id"], []).append({
            "id": row["id"],
            "restaurant_id": row["restaurant_id"],
            "label": row["label"],
            "capacity": row["capacity"],
        })

    restaurants = [
        {
            "id": row["id"],
            "name": row["name"],
            "timezone": row["timezone"],
            "slot_minutes": row["slot_minutes"],
            "reservation_duration_minutes": row["reservation_duration_minutes"],
            "cancellation_cutoff_minutes": row["cancellation_cutoff_minutes"],
            "opening_hours": hours_by_restaurant.get(row["id"], []),
            "tables": tables_by_restaurant.get(row["id"], []),
        }
        for row in connection.execute(
            "SELECT id, name, timezone, slot_minutes, reservation_duration_minutes,"
            " cancellation_cutoff_minutes FROM restaurants ORDER BY ordinal, id"
        )
    ]

    reservations = [
        {
            "id": row["id"],
            "reference": row["reference"],
            "user_id": row["user_id"],
            "restaurant_id": row["restaurant_id"],
            "table_id": row["table_id"],
            "party_size": row["party_size"],
            "status": row["status"],
            "starts_local": row["starts_local"],
            "starts_us": row["starts_us"],
            "ends_us": row["ends_us"],
            "created_at": row["created_at"],
        }
        for row in connection.execute(
            "SELECT id, reference, user_id, restaurant_id, table_id, party_size, status,"
            " starts_local, starts_us, ends_us, created_at FROM reservations"
            " ORDER BY starts_us, ordinal, id"
        )
    ]

    receipts = [
        {
            "user_id": row["user_id"],
            "key": row["key"],
            "method": row["method"],
            "path": row["path"],
            "request_json": row["request_json"],
            "status_code": row["status_code"],
            "response_json": row["response_json"],
            "created_at": row["created_at"],
        }
        for row in connection.execute(
            "SELECT user_id, key, method, path, request_json, status_code, response_json,"
            " created_at FROM receipts ORDER BY user_id, key, method, path"
        )
    ]

    return {
        "users": users,
        "tokens": tokens,
        "restaurants": restaurants,
        "reservations": reservations,
        "receipts": receipts,
    }


def export_document(connection) -> dict:
    return {"track": TRACK, "format_version": FORMAT_VERSION, "state": snapshot(connection)}


def restore(store_: store.Store, document) -> None:
    """Atomically replace all state with an export document."""
    if not jsonutil.is_object(document):
        raise errors.validation_failed("the import body must be a JSON object")
    if "track" not in document:
        raise errors.validation_failed("the export document has no track")
    if document["track"] != TRACK:
        raise errors.validation_failed("the export document is for a different track")
    if "format_version" not in document:
        raise errors.validation_failed("the export document has no format_version")
    version = document["format_version"]
    if not jsonutil.is_integer(version) or version != FORMAT_VERSION:
        raise errors.validation_failed("unsupported export format_version")
    if "state" not in document:
        raise errors.validation_failed("the export document has no state")
    state = document["state"]
    if not jsonutil.is_object(state):
        raise errors.validation_failed("the exported state must be a JSON object")

    # Normalised before anything is deleted, so an invalid state cannot leave a
    # half-replaced destination behind.
    try:
        plan = fixtures.normalize(state)
    except fixtures.FixtureError as exc:
        raise errors.validation_failed(str(exc)) from exc

    with store_.write() as connection:
        fixtures.apply(connection, plan)
