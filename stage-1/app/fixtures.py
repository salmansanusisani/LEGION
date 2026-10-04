"""Fixtures (``POST /_test/reset``) and exported state (``POST /_test/import``).

Both arrive as a JSON object describing the same logical world, so both are
normalised through one validator and applied through one writer. That is what
makes section 10's promise cheap to keep: an unchanged export re-enters this
module and lands in the same rows, with the same identities, statuses and
timestamps it left with.

Structural problems are 422 ``validation_failed``. Nothing here reaches for 5xx:
every value is type-checked before it is used, so an odd fixture is refused
rather than crashing a worker thread.
"""
from __future__ import annotations

from . import jsonutil, timeutil
from .config import MAX_ID_LENGTH, WEEKDAY_INDEX
from .credentials import hash_password
from .timeutil import UnknownZone

STATUSES = ("confirmed", "cancelled")


class FixtureError(Exception):
    """A structurally invalid fixture or exported state."""


def _invalid(message: str):
    raise FixtureError(message)


def _require_object(value, what: str) -> dict:
    if not isinstance(value, dict):
        _invalid(f"{what} must be a JSON object")
    return value


def _require_list(container: dict, name: str, what: str) -> list:
    value = container.get(name)
    if value is None:
        return []
    if not isinstance(value, list):
        _invalid(f"{what} {name} must be an array")
    return value


def _text(value, what: str, *, max_length: int = MAX_ID_LENGTH, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        _invalid(f"{what} must be a string")
    if not value and not allow_empty:
        _invalid(f"{what} must not be empty")
    if len(value) > max_length:
        _invalid(f"{what} must be at most {max_length} characters")
    return value


def _integer(value, what: str, *, minimum: int, maximum: int) -> int:
    if not jsonutil.is_integer(value):
        _invalid(f"{what} must be an integer")
    if value < minimum or value > maximum:
        _invalid(f"{what} must be between {minimum} and {maximum}")
    return value


def _email_key(email: str) -> str:
    return email.strip().lower()


# -- normalisation -------------------------------------------------------


def _normalize_users(source: list) -> list:
    users, seen_ids, seen_mail = [], set(), set()
    for entry in source:
        item = _require_object(entry, "user")
        user_id = _text(item.get("id"), "user id")
        if user_id in seen_ids:
            _invalid(f"duplicate user id {user_id}")
        email = item.get("email")
        if not isinstance(email, str) or not email.strip():
            _invalid("user email must be a non-empty string")
        email = email.strip()
        if "@" not in email or any(character.isspace() for character in email):
            _invalid(f"user email {email!r} is not local@domain")
        key = _email_key(email)
        if key in seen_mail:
            _invalid(f"duplicate user email {email}")
        display_name = item.get("display_name")
        if display_name is None:
            display_name = email.split("@", 1)[0]
        elif not isinstance(display_name, str):
            _invalid("user display_name must be a string")

        if isinstance(item.get("password_hash"), str) and item["password_hash"]:
            # Import path: the hash travels unchanged so login survives it.
            password_hash = item["password_hash"]
        else:
            password = item.get("password")
            if not isinstance(password, str):
                _invalid("user password must be a string")
            password_hash = hash_password(password)

        created_at = item.get("created_at", item.get("created_at_us"))
        created_at = timeutil.now_micros() if created_at is None else _integer(
            created_at, "user created_at", minimum=-(2**62), maximum=2**62
        )
        seen_ids.add(user_id)
        seen_mail.add(key)
        users.append({
            "id": user_id,
            "email": email,
            "email_key": key,
            "password_hash": password_hash,
            "display_name": display_name,
            "created_at": created_at,
        })
    return users


def _normalize_restaurants(source: list, table_ids: set, ordinal_base: int) -> list:
    restaurants = []
    seen = set()
    for entry in source:
        item = _require_object(entry, "restaurant")
        restaurant_id = _text(item.get("id"), "restaurant id")
        if restaurant_id in seen:
            _invalid(f"duplicate restaurant id {restaurant_id}")
        seen.add(restaurant_id)
        name = item.get("name")
        if not isinstance(name, str):
            _invalid("restaurant name must be a string")
        timezone_name = _text(item.get("timezone"), "restaurant timezone", max_length=255)
        try:
            timeutil.zone(timezone_name)
        except UnknownZone:
            _invalid(f"unknown IANA timezone {timezone_name}")

        slot_minutes = _integer(item.get("slot_minutes"), "slot_minutes", minimum=1, maximum=1440)
        duration = _integer(
            item.get("reservation_duration_minutes"),
            "reservation_duration_minutes",
            minimum=1,
            maximum=1440,
        )
        cutoff = _integer(
            item.get("cancellation_cutoff_minutes"),
            "cancellation_cutoff_minutes",
            minimum=0,
            maximum=10080,
        )

        hours, seen_days = [], set()
        for position, raw_hour in enumerate(item.get("opening_hours") or []):
            hour = _require_object(raw_hour, "opening hour")
            weekday = hour.get("weekday")
            if not isinstance(weekday, str) or weekday.lower() not in WEEKDAY_INDEX:
                _invalid(f"unknown weekday {weekday!r}")
            weekday = weekday.lower()
            if weekday in seen_days:
                _invalid(f"duplicate opening hours for {weekday}")
            seen_days.add(weekday)
            opens = timeutil.parse_clock(hour.get("opens"))
            closes = timeutil.parse_clock(hour.get("closes"))
            if opens is None:
                _invalid(f"invalid opens {hour.get('opens')!r}")
            if closes is None:
                _invalid(f"invalid closes {hour.get('closes')!r}")
            if closes <= opens:
                _invalid("opening hours never cross midnight, so closes must be later than opens")
            hours.append({
                "weekday": weekday,
                "opens_min": opens,
                "closes_min": closes,
                "ordinal": position,
            })

        tables = []
        for position, raw_table in enumerate(item.get("tables") or []):
            table = _require_object(raw_table, "table")
            table_id = _text(table.get("id"), "table id")
            if table_id in table_ids:
                _invalid(f"duplicate table id {table_id}")
            table_ids.add(table_id)
            label = table.get("label")
            if label is None:
                label = table_id
            elif not isinstance(label, str):
                _invalid("table label must be a string")
            tables.append({
                "id": table_id,
                "restaurant_id": restaurant_id,
                "label": label,
                "capacity": _integer(table.get("capacity"), "table capacity", minimum=1, maximum=10000),
                "ordinal": position,
            })

        restaurants.append({
            "id": restaurant_id,
            "name": name,
            "timezone": timezone_name,
            "slot_minutes": slot_minutes,
            "duration": duration,
            "cutoff": cutoff,
            "ordinal": ordinal_base,
            "opening_hours": hours,
            "tables": tables,
        })
    return restaurants


def _normalize_reservations(source: list, plan_restaurants: dict, plan_tables: dict) -> list:
    reservations, seen_ids, seen_refs = [], set(), set()
    for position, entry in enumerate(source):
        item = _require_object(entry, "reservation")
        reservation_id = _text(item.get("id"), "reservation id")
        reference = _text(item.get("reference"), "reservation reference")
        if reservation_id in seen_ids:
            _invalid(f"duplicate reservation id {reservation_id}")
        if reference in seen_refs:
            _invalid(f"duplicate reservation reference {reference}")
        seen_ids.add(reservation_id)
        seen_refs.add(reference)

        user_id = _text(item.get("user_id"), "reservation user_id")
        restaurant_id = _text(item.get("restaurant_id"), "reservation restaurant_id")
        table_id = _text(item.get("table_id"), "reservation table_id")
        restaurant = plan_restaurants.get(restaurant_id)
        if restaurant is None:
            _invalid(f"unknown restaurant {restaurant_id}")
        table = plan_tables.get(table_id)
        if table is None or table["restaurant_id"] != restaurant_id:
            _invalid(f"unknown table {table_id} for restaurant {restaurant_id}")

        party_size = _integer(item.get("party_size"), "reservation party_size", minimum=1, maximum=2**62)
        status = item.get("status", "confirmed")
        if status not in STATUSES:
            _invalid(f"unknown reservation status {status!r}")

        zone = timeutil.zone(restaurant["timezone"])
        starts_local = item.get("starts_local", item.get("starts_at_local"))
        starts_local = _text(starts_local, "reservation starts_at_local", max_length=64)
        naive = timeutil.parse_local(starts_local)
        if naive is None:
            _invalid(f"invalid reservation starts_at_local {starts_local!r}")

        starts_us = item.get("starts_us", item.get("starts_at"))
        if starts_us is None:
            instant = timeutil.resolve_local(naive, zone)
            if instant is None:
                _invalid(f"reservation start {starts_local} does not exist in {restaurant['timezone']}")
            starts_us = timeutil.to_micros(instant)
        else:
            starts_us = _integer(starts_us, "reservation starts_at", minimum=-(2**62), maximum=2**62)

        ends_us = item.get("ends_us", item.get("ends_at"))
        if ends_us is None:
            ends_us = starts_us + restaurant["duration"] * 60 * timeutil.MICROS
        else:
            ends_us = _integer(ends_us, "reservation ends_at", minimum=-(2**62), maximum=2**62)

        created_at = item.get("created_at", item.get("created_at_us"))
        created_at = timeutil.now_micros() if created_at is None else _integer(
            created_at, "reservation created_at", minimum=-(2**62), maximum=2**62
        )

        reservations.append({
            "id": reservation_id,
            "reference": reference,
            "user_id": user_id,
            "restaurant_id": restaurant_id,
            "table_id": table_id,
            "party_size": party_size,
            "status": status,
            "starts_local": starts_local,
            "starts_us": starts_us,
            "ends_us": ends_us,
            "created_at": created_at,
            "ordinal": position,
        })
    return reservations


def _normalize_receipts(source: list) -> list:
    receipts = []
    seen = set()
    for entry in source:
        item = _require_object(entry, "receipt")
        user_id = _text(item.get("user_id"), "receipt user_id", max_length=MAX_ID_LENGTH)
        key = _text(item.get("key"), "receipt key", max_length=255)
        method = _text(item.get("method"), "receipt method", max_length=16)
        path = _text(item.get("path"), "receipt path", max_length=512)
        identity = (user_id, key, method, path)
        if identity in seen:
            _invalid("duplicate idempotency receipt")
        seen.add(identity)
        if not isinstance(item.get("request_json"), str):
            _invalid("receipt request_json must be a string")
        if not isinstance(item.get("response_json"), str):
            _invalid("receipt response_json must be a string")
        receipts.append({
            "user_id": user_id,
            "key": key,
            "method": method,
            "path": path,
            "request_json": item["request_json"],
            "status_code": _integer(item.get("status_code"), "receipt status_code", minimum=100, maximum=599),
            "response_json": item["response_json"],
            "created_at": _integer(item.get("created_at", 0), "receipt created_at",
                                  minimum=-(2**62), maximum=2**62),
        })
    return receipts


def _normalize_tokens(source: list, user_ids: set) -> list:
    tokens = []
    for entry in source:
        item = _require_object(entry, "token")
        token = _text(item.get("token"), "token", max_length=512)
        user_id = _text(item.get("user_id"), "token user_id")
        if user_ids and user_id not in user_ids:
            _invalid(f"token references unknown user {user_id}")
        tokens.append({
            "token": token,
            "user_id": user_id,
            "created_at": _integer(item.get("created_at", 0), "token created_at",
                                  minimum=-(2**62), maximum=2**62),
        })
    return tokens


def normalize(body: dict) -> dict:
    """Validate a reset fixture or an exported ``state`` into one plan."""
    users = _normalize_users(_require_list(body, "users", "fixture"))
    user_ids = {user["id"] for user in users}

    table_ids: set = set()
    restaurants = _normalize_restaurants(
        _require_list(body, "restaurants", "fixture"), table_ids, ordinal_base=0
    )
    plan_restaurants = {restaurant["id"]: restaurant for restaurant in restaurants}
    plan_tables = {table["id"]: table for restaurant in restaurants for table in restaurant["tables"]}

    reservations = _normalize_reservations(
        _require_list(body, "reservations", "fixture"), plan_restaurants, plan_tables
    )
    for reservation in reservations:
        if user_ids and reservation["user_id"] not in user_ids:
            _invalid(f"reservation {reservation['reference']} names unknown user")

    receipts = _normalize_receipts(_require_list(body, "receipts", "state"))
    tokens = _normalize_tokens(_require_list(body, "tokens", "state"), user_ids)

    return {
        "users": users,
        "restaurants": restaurants,
        "reservations": reservations,
        "receipts": receipts,
        "tokens": tokens,
    }


# -- application ---------------------------------------------------------

_INSERT_USER = "INSERT INTO users(id, email, email_key, password_hash, display_name, created_at) VALUES(?,?,?,?,?,?)"
_INSERT_TOKEN = "INSERT INTO tokens(token, user_id, created_at) VALUES(?,?,?)"
_INSERT_RESTAURANT = (
    "INSERT INTO restaurants(id, name, timezone, slot_minutes,"
    " reservation_duration_minutes, cancellation_cutoff_minutes, ordinal) VALUES(?,?,?,?,?,?,?)"
)
_INSERT_HOURS = "INSERT INTO opening_hours(restaurant_id, weekday, opens_min, closes_min, ordinal) VALUES(?,?,?,?,?)"
_INSERT_TABLE = "INSERT INTO tables(id, restaurant_id, label, capacity, ordinal) VALUES(?,?,?,?,?)"
_INSERT_RESERVATION = (
    "INSERT INTO reservations(id, reference, user_id, restaurant_id, table_id, party_size,"
    " status, starts_local, starts_us, ends_us, created_at, ordinal) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)"
)
_INSERT_RECEIPT = (
    "INSERT INTO receipts(user_id, key, method, path, request_json, status_code,"
    " response_json, created_at) VALUES(?,?,?,?,?,?,?,?)"
)


def apply(connection, plan: dict) -> None:
    """Replace every row with a validated plan, inside the caller's transaction.

    Section 3.3's reset and section 10's import are both wholesale replacement,
    so both land here. Because it runs inside one ``BEGIN IMMEDIATE``, a failure
    anywhere above leaves the previous contents untouched.
    """
    from . import store

    store.wipe(connection)
    for user in plan["users"]:
        connection.execute(_INSERT_USER, (
            user["id"], user["email"], user["email_key"], user["password_hash"],
            user["display_name"], user["created_at"],
        ))
    for token in plan["tokens"]:
        connection.execute(_INSERT_TOKEN, (token["token"], token["user_id"], token["created_at"]))
    for restaurant in plan["restaurants"]:
        connection.execute(_INSERT_RESTAURANT, (
            restaurant["id"], restaurant["name"], restaurant["timezone"],
            restaurant["slot_minutes"], restaurant["duration"], restaurant["cutoff"],
            restaurant["ordinal"],
        ))
        for hour in restaurant["opening_hours"]:
            connection.execute(_INSERT_HOURS, (
                restaurant["id"], hour["weekday"], hour["opens_min"],
                hour["closes_min"], hour["ordinal"],
            ))
        for table in restaurant["tables"]:
            connection.execute(_INSERT_TABLE, (
                table["id"], table["restaurant_id"], table["label"],
                table["capacity"], table["ordinal"],
            ))
    for reservation in plan["reservations"]:
        connection.execute(_INSERT_RESERVATION, (
            reservation["id"], reservation["reference"], reservation["user_id"],
            reservation["restaurant_id"], reservation["table_id"], reservation["party_size"],
            reservation["status"], reservation["starts_local"], reservation["starts_us"],
            reservation["ends_us"], reservation["created_at"], reservation["ordinal"],
        ))
    for receipt in plan["receipts"]:
        connection.execute(_INSERT_RECEIPT, (
            receipt["user_id"], receipt["key"], receipt["method"], receipt["path"],
            receipt["request_json"], receipt["status_code"], receipt["response_json"],
            receipt["created_at"],
        ))
