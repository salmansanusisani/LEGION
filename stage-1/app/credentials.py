"""Credential storage.

Section 6 forbids plaintext passwords and asks for a password-hashing function
such as bcrypt, scrypt or Argon2. ``hashlib.scrypt`` is in the standard library,
needs no wheel at build time, and its memory-hard cost is configurable, so the
image pulls nothing at build and nothing at run time.

Password hashes travel in exports verbatim (section 10 requires hashed-password
login to survive an import), so the stored encoding is a self-describing string
and not a set of parallel columns.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

from . import config

SCHEME = "scrypt"
SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=config.SCRYPT_N,
        r=config.SCRYPT_R,
        p=config.SCRYPT_P,
        dklen=config.SCRYPT_DKLEN,
        maxmem=config.SCRYPT_N * config.SCRYPT_R * 256 + (1 << 20),
    )
    return "$".join((
        SCHEME,
        str(config.SCRYPT_N),
        str(config.SCRYPT_R),
        str(config.SCRYPT_P),
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    ))


def verify_password(password: str, stored: str) -> bool:
    parts = (stored or "").split("$")
    if len(parts) != 6 or parts[0] != SCHEME:
        return False
    try:
        n, r, p = int(parts[1]), int(parts[2]), int(parts[3])
        salt = base64.b64decode(parts[4], validate=True)
        expected = base64.b64decode(parts[5], validate=True)
    except (ValueError, TypeError):
        return False
    if n > 1 << 20:
        return False
    candidate = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=n,
        r=r,
        p=p,
        dklen=len(expected),
        maxmem=n * r * 256 + (1 << 20),
    )
    return hmac.compare_digest(candidate, expected)


def new_token() -> str:
    return secrets.token_urlsafe(32)


def new_id(prefix: str) -> str:
    """An opaque id well inside the 64-character limit of section 3.4."""
    return f"{prefix}_{secrets.token_hex(8)}"


def new_reference() -> str:
    """6 to 12 characters of ``A-Z0-9``, per section 8."""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(8))
