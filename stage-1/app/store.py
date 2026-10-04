"""The one transactional store.

Every state change in this service happens inside :meth:`Store.write`, which
opens ``BEGIN IMMEDIATE`` on a connection guarded by a process-wide lock. The
occupancy predicate in :func:`conflicting_reservation` is evaluated on that same
connection, so availability is never checked outside the transaction that then
writes. That is what makes section 1's "two confirmed reservations must never
occupy the same table at overlapping times, including during concurrent
requests" a structural property rather than a hopeful one.

Reads use per-thread connections against the same WAL file, so they never block
the writer and never observe a half-applied batch.
"""
from __future__ import annotations

import contextlib
import os
import sqlite3
import threading

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id             TEXT PRIMARY KEY,
    email          TEXT NOT NULL,
    email_key      TEXT NOT NULL UNIQUE,
    password_hash  TEXT NOT NULL,
    display_name   TEXT NOT NULL,
    created_at     INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS tokens (
    token      TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS tokens_user ON tokens(user_id);

CREATE TABLE IF NOT EXISTS restaurants (
    id                              TEXT PRIMARY KEY,
    name                            TEXT NOT NULL,
    timezone                        TEXT NOT NULL,
    slot_minutes                    INTEGER NOT NULL,
    reservation_duration_minutes    INTEGER NOT NULL,
    cancellation_cutoff_minutes     INTEGER NOT NULL,
    ordinal                         INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS opening_hours (
    restaurant_id TEXT NOT NULL,
    weekday       TEXT NOT NULL,
    opens_min     INTEGER NOT NULL,
    closes_min    INTEGER NOT NULL,
    ordinal       INTEGER NOT NULL,
    PRIMARY KEY (restaurant_id, weekday)
);

CREATE TABLE IF NOT EXISTS tables (
    id            TEXT PRIMARY KEY,
    restaurant_id TEXT NOT NULL,
    label         TEXT NOT NULL,
    capacity      INTEGER NOT NULL,
    ordinal       INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS tables_restaurant ON tables(restaurant_id, ordinal);

CREATE TABLE IF NOT EXISTS reservations (
    id            TEXT PRIMARY KEY,
    reference     TEXT NOT NULL UNIQUE,
    user_id       TEXT NOT NULL,
    restaurant_id TEXT NOT NULL,
    table_id      TEXT NOT NULL,
    party_size    INTEGER NOT NULL,
    status        TEXT NOT NULL,
    starts_local  TEXT NOT NULL,
    starts_us     INTEGER NOT NULL,
    ends_us       INTEGER NOT NULL,
    created_at    INTEGER NOT NULL,
    ordinal       INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS reservations_occupancy
    ON reservations(table_id, status, starts_us, ends_us);
CREATE INDEX IF NOT EXISTS reservations_owner
    ON reservations(user_id, starts_us);

CREATE TABLE IF NOT EXISTS receipts (
    user_id       TEXT NOT NULL,
    key           TEXT NOT NULL,
    method        TEXT NOT NULL,
    path          TEXT NOT NULL,
    request_json  TEXT NOT NULL,
    status_code   INTEGER NOT NULL,
    response_json TEXT NOT NULL,
    created_at    INTEGER NOT NULL,
    PRIMARY KEY (user_id, key, method, path)
);
"""

TABLES_IN_DELETE_ORDER = (
    "receipts",
    "reservations",
    "tables",
    "opening_hours",
    "restaurants",
    "tokens",
    "users",
)


class Store:
    def __init__(self, path: str) -> None:
        self._path = path
        self._write_lock = threading.RLock()
        self._local = threading.local()
        self._writer: sqlite3.Connection | None = None

    # -- connections ----------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._path, timeout=30.0, isolation_level=None, check_same_thread=False
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    def start(self) -> None:
        """Create the schema up front so /health is only green when the store can serve."""
        parent = os.path.dirname(self._path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        writer = self._connect()
        writer.execute("PRAGMA journal_mode = WAL")
        writer.execute("PRAGMA synchronous = NORMAL")
        writer.execute("PRAGMA foreign_keys = OFF")
        writer.executescript(SCHEMA)
        self._writer = writer
        self._local.connection = self._connect()

    def close_thread_connection(self) -> None:
        """Release the calling thread's reader connection.

        Called once a request finishes so a thread-per-connection server does not
        accumulate one open SQLite handle per client connection.
        """
        connection = getattr(self._local, "connection", None)
        if connection is not None:
            with contextlib.suppress(Exception):
                connection.close()
            self._local.connection = None

    def close(self) -> None:
        if self._writer is not None:
            with contextlib.suppress(Exception):
                self._writer.close()
        with contextlib.suppress(Exception):
            self._local.connection.close()

    def reader(self) -> sqlite3.Connection:
        """The calling thread's read connection.

        One handle per thread rather than per request: opening a SQLite handle
        is cheap but not free, and a thread-per-connection server already keeps
        the count bounded by the in-flight request count.
        """
        connection = getattr(self._local, "connection", None)
        if connection is None:
            connection = self._connect()
            self._local.connection = connection
        return connection

    # -- transactions ---------------------------------------------------

    @contextlib.contextmanager
    def write(self):
        """A serialized, all-or-nothing write transaction.

        The process-wide lock makes write transactions strictly serial, so a
        create, an amendment or a batch move can never interleave with another
        writer. The lock is also what makes concurrent identical idempotent
        requests resolve to exactly one first use: the second request cannot
        read the receipts table until the first has committed its receipt.
        """
        if self._writer is None:
            raise RuntimeError("store not started")
        with self._write_lock:
            connection = self._writer
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
            except BaseException:
                with contextlib.suppress(Exception):
                    connection.execute("ROLLBACK")
                raise
            else:
                connection.execute("COMMIT")

    @contextlib.contextmanager
    def read(self):
        """A consistent read snapshot, which is what export needs."""
        connection = self.reader()
        connection.execute("BEGIN")
        try:
            yield connection
        finally:
            with contextlib.suppress(Exception):
                connection.execute("COMMIT")


def wipe(connection: sqlite3.Connection) -> None:
    """Empty every data table. Import and reset are replacement, never merge."""
    for table in TABLES_IN_DELETE_ORDER:
        connection.execute(f"DELETE FROM {table}")


def conflicting_reservation(
    connection: sqlite3.Connection,
    table_id: str,
    starts_us: int,
    ends_us: int,
    *,
    exclude_ids: frozenset[str] = frozenset(),
):
    """The overlap predicate: half-open ``[starts, ends)``.

    A booking starting exactly when another ends is *not* a conflict, because
    ``starts_us < ends_us AND ends_us > starts_us`` excludes the touching case.
    Runs on the caller's write transaction, so it sees and locks nothing
    uncommitted and no other writer can slip a booking in between the check and
    the insert.
    """
    sql = (
        "SELECT id FROM reservations"
        " WHERE table_id = ? AND status = 'confirmed'"
        "   AND starts_us < ? AND ends_us > ?"
    )
    params: list = [table_id, ends_us, starts_us]
    if exclude_ids:
        placeholders = ",".join("?" for _ in exclude_ids)
        sql += f" AND id NOT IN ({placeholders})"
        params.extend(sorted(exclude_ids))
    sql += " LIMIT 1"
    return connection.execute(sql, params).fetchone()
