"""AEON-Link v0.2.0 experimental core. No remote model or tool execution."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from importlib import resources
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker

VERSION = "0.4.0"
ONTOLOGY = "urn:aeon-link:ontology:core:0.4.0"
FEATURES = frozenset({"claims.v1", "evidence.refs.v1", "objective.ack.v1", "semantic.contract.v1", "evidence.graph.v1"})

with resources.files("aeon_link").joinpath("schema.json").open("r", encoding="utf-8") as stream:
    SCHEMA = json.load(stream)
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


class ProtocolError(ValueError):
    """The received data violates a defined AEON-Link invariant."""


from .canonical import canonical_bytes, digest, CanonicalizationError

from datetime import date

_RFC3339 = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})[Tt](\d{2}):(\d{2}):(\d{2})(?:\.\d+)?([Zz]|[+-]\d{2}:\d{2})$"
)

def _valid_observed_at(value: object) -> bool:
    """Stable strict RFC3339 subset independent of optional jsonschema extras.

    Fractional seconds supported; leap second 60 intentionally rejected.
    This validator never uses system timezone, wall clock or external packages.
    """
    if not isinstance(value, str):
        return False
    m = _RFC3339.fullmatch(value)
    if m is None:
        return False
    year, month, day, hour, minute, second = map(int, m.groups()[:6])
    if year < 1 or hour > 23 or minute > 59 or second > 59:
        return False
    try:
        date(year, month, day)
    except ValueError:
        return False
    zone = m.group(7)
    if len(zone) == 6 and (int(zone[1:3]) > 23 or int(zone[4:6]) > 59):
        return False
    return True



def validate_envelope(envelope: dict) -> dict:
    """Validate JSON shape and limited *referential* invariants; not truth or authenticity."""
    try:
        canonical_bytes(envelope)
    except CanonicalizationError as exc:
        raise ProtocolError(f"Unsupported canonical JSON profile: {exc}") from exc
    problems = sorted(VALIDATOR.iter_errors(envelope), key=lambda e: (list(map(str, e.absolute_path)), e.message))
    if problems:
        raise ProtocolError("Schema violation: " + "; ".join(f"{'.'.join(map(str,e.path)) or '$'}: {e.message}" for e in problems))
    body = envelope["body"]
    if envelope["kind"] == "task":
        ev_ids = [e["id"] for e in body["evidence"]]
        claim_ids = [c["id"] for c in body["claims"]]
        if len(ev_ids) != len(set(ev_ids)) or len(claim_ids) != len(set(claim_ids)):
            raise ProtocolError("Evidence and claim IDs must be unique within the task")
        for evidence in body["evidence"]:
            if "observed_at" in evidence and not _valid_observed_at(evidence["observed_at"]):
                raise ProtocolError("Invalid date-time: observed_at")
        known = set(ev_ids)
        for claim in body["claims"]:
            if any(eid not in known for eid in claim["evidence_ids"]):
                raise ProtocolError(f"Claim {claim['id']} refers to unavailable evidence")
        if body["constraints"]["read_only"] and body["action"] in ("write", "execute"):
            raise ProtocolError("Write/execute contradict read_only constraint")
    return envelope


def message(kind: str, sender: str, recipient: str, body: dict) -> dict:
    envelope = {
        "protocol": "aeon-link", "version": VERSION, "ontology": ONTOLOGY,
        "message_id": str(uuid.uuid4()), "kind": kind,
        "sender": sender, "recipient": recipient, "body": copy.deepcopy(body),
    }
    return validate_envelope(envelope)


def hello(sender: str, recipient: str, *, versions: Iterable[str] = (VERSION,),
          ontologies: Iterable[str] = (ONTOLOGY,), features: Iterable[str] = FEATURES) -> dict:
    return message("hello", sender, recipient, {
        "versions": sorted(set(versions)),
        "ontologies": sorted(set(ontologies)),
        "features": sorted(set(features)),
    })


@dataclass(frozen=True)
class Agreement:
    version: str
    ontology: str
    features: frozenset[str]


def _version_key(value: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"\d+\.\d+\.\d+", value):
        raise ProtocolError(f"Unsupported version syntax: {value}")
    return tuple(map(int, value.split(".")))


def negotiate(local: dict, remote: dict, *, required_features: Iterable[str] = ()) -> Agreement:
    """Fail closed: no silent fallbacks to incompatible semantics."""
    validate_envelope(local)
    validate_envelope(remote)
    if local["kind"] != "hello" or remote["kind"] != "hello":
        raise ProtocolError("Handshake requires two hello envelopes")
    if local["sender"] != remote["recipient"] or remote["sender"] != local["recipient"]:
        raise ProtocolError("Handshake participants do not agree")
    common_versions = set(local["body"]["versions"]) & set(remote["body"]["versions"])
    common_ontologies = set(local["body"]["ontologies"]) & set(remote["body"]["ontologies"])
    if VERSION not in common_versions or ONTOLOGY not in common_ontologies:
        raise ProtocolError("No supported common version/ontology; refusing semantic fallback")
    features = frozenset(local["body"]["features"]) & frozenset(remote["body"]["features"])
    if not set(required_features).issubset(features):
        raise ProtocolError("Required features not supported by both agents")
    return Agreement(VERSION, ONTOLOGY, features)


@dataclass(frozen=True)
class LocalPolicy:
    """Policy supplied by the authenticated host, NEVER by remote message data."""
    allowed_actions: frozenset[str]
    verified_sender: str


def authorize_task(task: dict, policy: LocalPolicy) -> None:
    validate_envelope(task)
    if task["kind"] != "task":
        raise ProtocolError("Expected task")
    if task["sender"] != policy.verified_sender:
        raise ProtocolError("Sender does not match authenticated host identity")
    if task["body"]["action"] not in policy.allowed_actions:
        raise ProtocolError("Action not permitted by host-side policy")
    # This only validates a decision. No network/FS/system action is executed here.


def make_ack_result(task: dict, responder: str) -> dict:
    """Deterministic simulator: confirms bytes and constraints; no model comprehension test."""
    validate_envelope(task)
    if task["kind"] != "task":
        raise ProtocolError("Cannot acknowledge a non-task")
    if task["recipient"] != responder:
        raise ProtocolError("Wrong recipient")
    b = task["body"]
    return message("result", responder, task["sender"], {
        "in_reply_to": task["message_id"],
        "objective_id": b["objective"]["id"],
        "objective_digest": digest(b["objective"]),
        "constraints_digest": digest(b["constraints"]),
        "status": "needs_clarification",
        "understood_objective": b["objective"]["text"],
        "findings": [],
        "uncertainties": ["No external checks or model reasoning performed"],
        "actions_executed": [],
    })


def verify_ack(task: dict, result: dict) -> bool:
    """Checks *byte-level agreement* and message linkage; not equal semantic understanding."""
    validate_envelope(task)
    validate_envelope(result)
    if task["kind"] != "task" or result["kind"] != "result":
        raise ProtocolError("Ack comparison expects task + result")
    tb, rb = task["body"], result["body"]
    expected = (
        result["sender"] == task["recipient"],
        result["recipient"] == task["sender"],
        rb["in_reply_to"] == task["message_id"],
        rb["objective_id"] == tb["objective"]["id"],
        rb["objective_digest"] == digest(tb["objective"]),
        rb["constraints_digest"] == digest(tb["constraints"]),
        rb["understood_objective"] == tb["objective"]["text"],
    )
    if not all(expected):
        raise ProtocolError("Acknowledgment does not match original task")
    return True


class ReplayGuard:
    """Process-local duplicate detection; not durable or distributed."""
    def __init__(self):
        self._seen: set[tuple[str, str]] = set()

    def check(self, envelope: dict) -> None:
        validate_envelope(envelope)
        token = (envelope["sender"], envelope["message_id"])
        if token in self._seen:
            raise ProtocolError("Duplicate message_id for sender")
        self._seen.add(token)
