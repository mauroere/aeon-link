"""Offline evidence CONTENT integrity check (does not verify truth or source identity)."""
import hashlib
from .core import ProtocolError


def verify_evidence_content(evidence: dict, content: bytes) -> bool:
    if not isinstance(evidence, dict) or not isinstance(content, bytes):
        raise ProtocolError('Expected evidence record and immutable content bytes')
    expected = evidence.get('sha256')
    if not isinstance(expected, str) or len(expected) != 64:
        raise ProtocolError('Evidence record must include sha256 digest')
    import hmac
    actual = hashlib.sha256(content).hexdigest()
    if not hmac.compare_digest(actual, expected):
        raise ProtocolError('Evidence bytes do not match claimed SHA-256')
    return True
