"""Optional message authentication: HMAC-SHA256 for pre-shared, out-of-band keys.

Not a transport or public-key identity solution. Callers still need TLS and
identity/key provisioning. Never infer permission from the signed envelope.
"""
from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Mapping

from .canonical import canonical_bytes
from .core import ProtocolError, validate_envelope

DOMAIN = b'AEON-LINK-HMAC-SHA256-v1\x00'
MAX_TTL = 300
CLOCK_SKEW = 30


@dataclass(frozen=True)
class TrustedKey:
    sender: str
    secret: bytes


@dataclass(frozen=True)
class VerifiedMessage:
    envelope: dict
    verified_sender: str
    key_id: str
    expires_at: int


def _mac(envelope: dict, meta: dict, secret: bytes) -> str:
    return hmac.new(secret, DOMAIN + canonical_bytes({'envelope': envelope, 'meta': meta}), hashlib.sha256).hexdigest()


def sign_envelope(envelope: dict, *, key_id: str, secret: bytes, issued_at: int | None = None,
                  ttl_seconds: int = 60) -> dict:
    validate_envelope(envelope)
    if not isinstance(key_id, str) or not key_id or not isinstance(secret, bytes) or len(secret) < 32:
        raise ProtocolError('HMAC requires a key identifier and >=32-byte secret')
    if not isinstance(ttl_seconds, int) or isinstance(ttl_seconds, bool) or not 1 <= ttl_seconds <= MAX_TTL:
        raise ProtocolError('Invalid message time-to-live')
    now = int(time.time()) if issued_at is None else issued_at
    if not isinstance(now, int) or isinstance(now, bool):
        raise ProtocolError('Invalid issued_at timestamp')
    meta = {'alg': 'HS256', 'key_id': key_id, 'issued_at': now, 'expires_at': now + ttl_seconds}
    signature = _mac(envelope, meta, secret)
    return {'envelope': envelope, 'meta': meta, 'signature': signature}


def verify_signed(signed: dict, trusted_keys: Mapping[str, TrustedKey], *, now: int | None = None) -> VerifiedMessage:
    if not isinstance(signed, dict) or set(signed) != {'envelope', 'meta', 'signature'}:
        raise ProtocolError('Invalid signed wrapper')
    envelope, meta = signed['envelope'], signed['meta']
    validate_envelope(envelope)
    if not isinstance(meta, dict) or set(meta) != {'alg', 'key_id', 'issued_at', 'expires_at'} or meta['alg'] != 'HS256':
        raise ProtocolError('Invalid authentication metadata')
    key_id = meta['key_id']
    trusted = trusted_keys.get(key_id) if isinstance(key_id, str) else None
    if not isinstance(trusted, TrustedKey) or not isinstance(trusted.secret, bytes) or len(trusted.secret) < 32:
        raise ProtocolError('Unknown or invalid trusted key')
    start, end = meta['issued_at'], meta['expires_at']
    if any(isinstance(x, bool) or not isinstance(x, int) for x in (start, end)) or not 1 <= end - start <= MAX_TTL:
        raise ProtocolError('Invalid signed time window')
    clock = int(time.time()) if now is None else now
    if isinstance(clock, bool) or not isinstance(clock, int) or start > clock + CLOCK_SKEW or end < clock:
        raise ProtocolError('Expired or future signed message')
    sig = signed['signature']
    if not isinstance(sig, str) or len(sig) != 64 or not hmac.compare_digest(sig, _mac(envelope, meta, trusted.secret)):
        raise ProtocolError('Invalid message signature')
    if envelope['sender'] != trusted.sender:
        raise ProtocolError('Authenticated key does not belong to declared sender')
    return VerifiedMessage(envelope, trusted.sender, key_id, end)
