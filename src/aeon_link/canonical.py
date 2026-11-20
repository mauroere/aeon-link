"""Restricted AEON canonical JSON profile for reproducible SHA-256/HMAC on Python and Node.

This is intentionally NOT RFC 8785/JCS. The v0.3 profile supports only JSON
null, booleans, strings, arrays, ASCII-keyed objects, and safe integers.
Floating-point numbers are rejected rather than silently produce divergent hashes.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")
RESERVED_KEYS = frozenset({"__proto__", "constructor", "prototype"})
MAX_INTEGER = 2**53 - 1
MAX_BYTES = 1_048_576
MAX_DEPTH = 64


class CanonicalizationError(ValueError):
    pass


def _check(value: Any, depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        raise CanonicalizationError("Maximum JSON depth exceeded")
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if abs(value) > MAX_INTEGER:
            raise CanonicalizationError("Integers must be within JavaScript safe range")
        return
    if isinstance(value, str):
        try:
            value.encode('utf-8', errors='strict')
        except UnicodeError as e:
            raise CanonicalizationError("Unpaired Unicode surrogate") from e
        return
    if isinstance(value, list):
        for item in value:
            _check(item, depth + 1)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or KEY.fullmatch(key) is None or key in RESERVED_KEYS:
                raise CanonicalizationError("Object keys must be ASCII identifiers")
            _check(item, depth + 1)
        return
    raise CanonicalizationError(f"Unsupported JSON value: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    _check(value)
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(',', ':'), allow_nan=False).encode('utf-8')
    if len(encoded) > MAX_BYTES:
        raise CanonicalizationError("Canonical data exceeds 1 MiB")
    return encoded


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def parse_canonical(raw: bytes) -> Any:
    """Parse canonical wire bytes; reserialization check detects duplicate keys.

    For transports that exchange already-decoded objects use canonical_bytes before
    signing, but never treat an untrusted JSON parser's result as proof that its
    original wire encoding had no duplicate keys.
    """
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise CanonicalizationError("Expected canonical bytes within 1 MiB")
    try:
        value = json.loads(raw.decode('utf-8', errors='strict'))
        if canonical_bytes(value) != raw:
            raise CanonicalizationError("Noncanonical wire bytes or duplicate keys")
        return value
    except (UnicodeError, json.JSONDecodeError) as e:
        raise CanonicalizationError("Invalid JSON/UTF-8") from e
