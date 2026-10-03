"""Password hashing and token primitives for authentication.

Design decisions:
- Argon2id via argon2-cffi, using the library defaults that align with
  OWASP recommendations (time_cost=3, memory_cost=64 MiB, parallelism=4).
- Tokens are 256 bits of CSPRNG output, URL-safe base64 encoded.
- Only SHA-256 hashes of tokens are ever stored; the raw token exists
  solely inside the cookie and is unrecoverable from the database.
- Comparisons use constant-time helpers to prevent timing attacks.
"""

import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a password with Argon2id. Returns a PHC-format string."""
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Constant-time password verification.

    Returns False for wrong passwords AND for malformed stored hashes —
    a corrupted hash in the database must never surface as a 500.
    """
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except InvalidHashError:
        return False


def password_needs_rehash(password_hash: str) -> bool:
    """True when a stored hash used weaker parameters than current defaults.

    Wired into login in a later step so hashes transparently upgrade
    without forcing users to reset their passwords.
    """
    return _password_hasher.check_needs_rehash(password_hash)


def generate_token() -> str:
    """Generate a 256-bit cryptographically random, URL-safe token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """SHA-256 hex digest of a token — the only form we ever store."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def tokens_match(token: str, token_hash: str) -> bool:
    """Constant-time comparison of a raw token against a stored hash."""
    return secrets.compare_digest(hash_token(token), token_hash)
