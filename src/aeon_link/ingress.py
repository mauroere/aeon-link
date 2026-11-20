"""Hardened AEON-Link inbound gate.

The caller MUST provide the recipient identity and local policy.  This gate
performs no side effects except recording the replay token.  It does not
execute tools, prove semantic comprehension, or validate evidence truth.

Wire format and ontology remain 0.4.0 in this SDK 0.5.0 release.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Mapping

from .canonical import CanonicalizationError, parse_canonical
from .core import LocalPolicy, ProtocolError, authorize_task
from .auth import TrustedKey, verify_signed
from .replay import SQLiteReplayGuard


@dataclass(frozen=True)
class InboundReceipt:
    """Validated receipt. Treat the nested envelope as read-only."""
    envelope: dict
    verified_sender: str
    recipient: str
    message_id: str
    key_id: str
    expires_at: int
    replay_recorded: bool


def receive_signed(
    raw: bytes, *, trusted_keys: Mapping[str, TrustedKey],
    local_recipient: str, local_policy: LocalPolicy | None,
    replay_guard: SQLiteReplayGuard, now: int,
) -> InboundReceipt:
    """Validate canonical wire -> verify HMAC -> destination -> policy -> replay.

    Caller must only dispatch the returned envelope after this returns.
    Non-task messages still require signature, matching recipient and replay
    checks; local_policy is required only for tasks.

    Concurrent processes need shared replay storage.  This method cannot
    atomically commit external business actions with the SQLite replay token;
    consumers should use idempotent action execution as well.
    """
    if not isinstance(local_recipient, str) or not local_recipient or len(local_recipient) > 256:
        raise ProtocolError('Receiver must identify local recipient')
    if not isinstance(replay_guard, SQLiteReplayGuard):
        raise ProtocolError('A durable replay guard is required')
    if type(now) is not int:
        raise ProtocolError('Verified wall-clock seconds required')
    try:
        signed = parse_canonical(raw)
    except (CanonicalizationError, RecursionError) as exc:
        raise ProtocolError(f'Invalid canonical inbound wire data: {exc}') from exc
    verified = verify_signed(signed, trusted_keys, now=now)
    env = verified.envelope
    if env['recipient'] != local_recipient:
        raise ProtocolError('Authenticated message addressed to another recipient')
    if env['kind'] == 'task':
        if not isinstance(local_policy, LocalPolicy):
            raise ProtocolError('Task requires receiver-supplied local policy')
        if local_policy.verified_sender != verified.verified_sender:
            raise ProtocolError('Local policy bound to wrong authenticated sender')
        authorize_task(env, local_policy)
    # Protect replay state only after authentication and policy checks.
    replay_guard.check(verified, now=now)
    # A separate copy prevents mutating the upstream parsed signed object.
    return InboundReceipt(copy.deepcopy(env), verified.verified_sender,
                          local_recipient, env['message_id'], verified.key_id,
                          verified.expires_at, True)
