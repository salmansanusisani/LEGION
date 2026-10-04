"""Section 6 authentication.

Passwords are hashed with scrypt (see :mod:`app.credentials`); the hash, never
the password, is what a fixture, an export or the database holds. Tokens are
opaque random strings in their own table, so an account can hold several at once
and none of them expires.
"""
from __future__ import annotations

from . import credentials, errors, timeutil, validation

_SELECT = "SELECT id, email, email_key, password_hash, display_name, created_at FROM users"


def _public(row, token: str) -> dict:
    return {"user_id": row["id"], "display_name": row["display_name"], "token": token}


def signup(store, body) -> tuple:
    email = validation.email_field(body)
    password = validation.password_field(body)
    display_name = validation.display_name_field(body, email)

    with store.write() as connection:
        email_key = email.strip().lower()
        existing = connection.execute(
            "SELECT 1 FROM users WHERE email_key = ?", (email_key,)
        ).fetchone()
        if existing is not None:
            raise errors.email_taken()

        user_id = credentials.new_id("usr")
        token = credentials.new_token()
        connection.execute(
            "INSERT INTO users(id, email, email_key, password_hash, display_name, created_at)"
            " VALUES(?,?,?,?,?,?)",
            (user_id, email, email_key, credentials.hash_password(password),
             display_name, timeutil.now_micros()),
        )
        connection.execute(
            "INSERT INTO tokens(token, user_id, created_at) VALUES(?,?,?)",
            (token, user_id, timeutil.now_micros()),
        )
        row = connection.execute(_SELECT + " WHERE id = ?", (user_id,)).fetchone()
        return 201, _public(row, token)


def login(store, body) -> tuple:
    email = validation.optional_email_field(body)
    password = validation.optional_password_field(body)

    with store.read() as connection:
        row = connection.execute(
            _SELECT + " WHERE email_key = ?", (email.strip().lower(),)
        ).fetchone()
        if row is None or not credentials.verify_password(password, row["password_hash"]):
            # Section 6: wrong password and unknown email are the same refusal.
            raise errors.unauthenticated("those credentials are not valid")
        token = credentials.new_token()
    with store.write() as connection:
        connection.execute(
            "INSERT INTO tokens(token, user_id, created_at) VALUES(?,?,?)",
            (token, row["id"], timeutil.now_micros()),
        )
    return 200, _public(row, token)


def bearer_token(headers) -> str:
    """The token from an ``Authorization: Bearer <token>`` header."""
    raw = headers.get("Authorization") or ""
    parts = raw.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise errors.unauthenticated()
    token = parts[1].strip()
    if not token:
        raise errors.unauthenticated()
    return token


def identify(store, headers):
    """The caller for a protected endpoint, or a 401.

    An absent, malformed or unknown token are all ``401 unauthenticated``; nothing
    here distinguishes them, and a public endpoint never calls it.
    """
    token = bearer_token(headers)
    connection = store.reader()
    row = connection.execute(
        "SELECT u.id AS id, u.email AS email, u.email_key AS email_key,"
        " u.password_hash AS password_hash, u.display_name AS display_name,"
        " u.created_at AS created_at"
        " FROM tokens t JOIN users u ON u.id = t.user_id WHERE t.token = ?",
        (token,),
    ).fetchone()
    if row is None:
        raise errors.unauthenticated("that bearer token is not valid")
    return row
