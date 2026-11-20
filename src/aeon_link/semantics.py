"""ÆON-Link Semantic Contract extension 0.2 (experimental).

A small, deterministic, executable interpretation contract. This is not a
formal proof of natural-language understanding or a grant of tool permissions.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any, Iterable

from .canonical import canonical_bytes, digest

PROFILE = "aeon.semantic.contract/0.2"
MAX_CLAUSES = 64
MAX_CASES = 64
OPS = frozenset(("eq", "ne", "exists", "gt", "gte", "lt", "lte", "in"))
MODES = frozenset(("require", "forbid"))
STATUSES = frozenset(("satisfied", "violated", "incomplete"))
MISSING = object()


class ContractError(ValueError):
    pass


def _safe(value: Any) -> None:
    try:
        canonical_bytes(value)
    except (ValueError, TypeError) as exc:
        raise ContractError(f"Invalid canonical data: {exc}") from exc


def _tokens(pointer: str) -> list[str]:
    if not isinstance(pointer, str) or not pointer.startswith("/") or len(pointer) > 256:
        raise ContractError("Use a nonempty JSON Pointer, max 256 chars")
    parts = pointer[1:].split("/")
    out = []
    for part in parts:
        if "~" in part:
            import re
            if re.search(r"~(?![01])", part):
                raise ContractError("Invalid JSON Pointer escape")
        token = part.replace("~1", "/").replace("~0", "~")
        if token in ("__proto__", "constructor", "prototype"):
            raise ContractError("Dangerous JSON Pointer token")
        import re
        if not re.fullmatch(r"(?:[A-Za-z_][A-Za-z0-9_.-]*|0|[1-9][0-9]*)", token):
            raise ContractError("Path token unsupported by AEON canonical profile")
        out.append(token)
    return out


def normalize_contract(contract: dict) -> dict:
    _safe(contract)
    if not isinstance(contract, dict) or set(contract) != {"profile", "clauses", "allowed_actions"}:
        raise ContractError("Invalid contract keys")
    if contract["profile"] != PROFILE:
        raise ContractError("Unsupported semantic profile")
    clauses, actions = contract["clauses"], contract["allowed_actions"]
    if not isinstance(clauses, list) or not 1 <= len(clauses) <= MAX_CLAUSES:
        raise ContractError("Clauses must be a nonempty bounded list")
    if not isinstance(actions, list) or not actions or len(actions) > 32:
        raise ContractError("Invalid allowed actions")
    if any(not isinstance(a, str) or not a or len(a) > 128 for a in actions):
        raise ContractError("Invalid action")
    if len(set(actions)) != len(actions):
        raise ContractError("Duplicate action")
    ids = set()
    normalized = []
    for clause in clauses:
        if not isinstance(clause, dict) or not {"id", "mode", "path", "op"}.issubset(clause):
            raise ContractError("Malformed clause")
        if set(clause) - {"id", "mode", "path", "op", "value"}:
            raise ContractError("Unexpected clause fields")
        cid, mode, op = clause["id"], clause["mode"], clause["op"]
        if not isinstance(cid, str) or not cid or len(cid) > 128 or cid in ids:
            raise ContractError("Invalid or duplicated clause ID")
        ids.add(cid)
        if not isinstance(mode, str) or not isinstance(op, str) or mode not in MODES or op not in OPS:
            raise ContractError("Unknown mode or predicate operator")
        _tokens(clause["path"])
        if (op == "exists") == ("value" in clause):
            raise ContractError("exists requires no value; all other operators require one")
        if op in ("gt", "gte", "lt", "lte") and (type(clause["value"]) is not int):
            raise ContractError("Comparison requires a safe integer")
        if op == "in" and (not isinstance(clause["value"], list) or not clause["value"] or len(clause["value"]) > 64):
            raise ContractError("in requires nonempty list")
        normalized.append(clause.copy())
    return {"profile": PROFILE, "allowed_actions": sorted(actions),
            "clauses": sorted(normalized, key=lambda c: c["id"])}


def contract_fingerprint(contract: dict) -> str:
    """Hash of a *structural* agreement, not proof of semantic comprehension."""
    return digest(normalize_contract(contract))


def _lookup(state: dict, pointer: str):
    node: Any = state
    for token in _tokens(pointer):
        if isinstance(node, dict):
            if token not in node:
                return MISSING
            node = node[token]
        elif isinstance(node, list):
            if not token.isascii() or not token.isdecimal() or (len(token) > 1 and token[0] == '0'):
                return MISSING
            index = int(token)
            if index >= len(node):
                return MISSING
            node = node[index]
        else:
            return MISSING
    return node


def _predicate(clause: dict, state: dict):
    actual = _lookup(state, clause["path"])
    op = clause["op"]
    if op == "exists":
        return actual is not MISSING
    if actual is MISSING:
        return None  # unknown, *not* false
    expected = clause["value"]
    if op == "eq":
        return type(actual) is type(expected) and canonical_bytes(actual) == canonical_bytes(expected)
    if op == "ne":
        return not (type(actual) is type(expected) and canonical_bytes(actual) == canonical_bytes(expected))
    if op == "in":
        return any(type(actual) is type(e) and canonical_bytes(actual) == canonical_bytes(e) for e in expected)
    if type(actual) is not int:
        return None
    return {"gt": actual > expected, "gte": actual >= expected,
            "lt": actual < expected, "lte": actual <= expected}[op]


def evaluate_contract(contract: dict, state: dict, action: str) -> dict:
    """Pure deterministic evaluation. Never executes an action or trusts evidence truth."""
    normalized = normalize_contract(contract)
    if not isinstance(state, dict) or not isinstance(action, str):
        raise ContractError("Invalid evaluation state or action")
    _safe(state)
    if action not in normalized["allowed_actions"]:
        return {"status": "violated", "violations": ["action:unauthorized"], "unknown": []}
    violations, unknown = [], []
    for clause in normalized["clauses"]:
        result = _predicate(clause, state)
        if result is None:
            unknown.append(clause["id"])
        elif (clause["mode"] == "require" and not result) or (clause["mode"] == "forbid" and result):
            violations.append(clause["id"])
    status = "violated" if violations else "incomplete" if unknown else "satisfied"
    return {"status": status, "violations": violations, "unknown": unknown}


@dataclass(frozen=True)
class ChallengeKey:
    nonce: str
    contract_digest: str
    expected: tuple[tuple[str, str], ...]


def create_challenge(contract: dict, cases: list[dict]) -> tuple[dict, ChallengeKey]:
    """The key MUST remain with the trusted challenger, not the tested agent."""
    d = contract_fingerprint(contract)
    if not isinstance(cases, list) or not 1 <= len(cases) <= MAX_CASES:
        raise ContractError("Expected 1..64 challenge cases")
    public_cases, expected = [], []
    seen = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "state", "action"}:
            raise ContractError("Malformed test case")
        cid = case["id"]
        if not isinstance(cid, str) or not cid or len(cid)>128 or cid in seen:
            raise ContractError("Duplicated challenge case ID")
        seen.add(cid)
        outcome = evaluate_contract(contract, case["state"], case["action"])['status']
        public_cases.append(case)
        expected.append((cid, outcome))
    nonce = secrets.token_hex(16)
    public = {"profile": PROFILE, "nonce": nonce, "contract_digest": d,
              "cases": public_cases}
    _safe(public)
    return public, ChallengeKey(nonce, d, tuple(expected))


def score_challenge(key: ChallengeKey, response: dict) -> dict:
    """Strict scoring without providing expected outcomes to receiver."""
    if not isinstance(key, ChallengeKey) or not isinstance(response, dict):
        raise ContractError("Bad challenge key or response")
    _safe(response)
    if set(response) != {"nonce", "contract_digest", "answers"} or response["nonce"] != key.nonce or response["contract_digest"] != key.contract_digest:
        raise ContractError("Challenge binding mismatch")
    answers = response["answers"]
    if not isinstance(answers, list) or len(answers) != len(key.expected):
        raise ContractError("Missing challenge answers")
    answers_by_id = {}
    for entry in answers:
        if not isinstance(entry, dict) or set(entry) != {"id", "status"} or not isinstance(entry["id"], str) or entry["id"] in answers_by_id or not isinstance(entry["status"], str) or entry["status"] not in STATUSES:
            raise ContractError("Invalid or duplicate answer")
        answers_by_id[entry["id"]] = entry["status"]
    if set(answers_by_id) != {cid for cid, _ in key.expected}:
        raise ContractError("Incorrect challenge case IDs")
    correct = sum(answers_by_id[cid] == status for cid, status in key.expected)
    return {"passed": correct == len(key.expected), "correct": correct,
            "total": len(key.expected)}


def _mutated(state: dict, pointer: str, replacement=MISSING, *, remove=False) -> dict | None:
    """Deep-copy and edit a dictionary-only path; skip ambiguous list/pointer mutations."""
    import copy
    tokens = _tokens(pointer)
    clone = copy.deepcopy(state)
    current = clone
    for token in tokens[:-1]:
        if not isinstance(current, dict) or token not in current or not isinstance(current[token], dict):
            return None
        current = current[token]
    if not isinstance(current, dict):
        return None
    if remove:
        if tokens[-1] not in current:
            return None
        del current[tokens[-1]]
    else:
        if replacement is MISSING:
            return None
        current[tokens[-1]] = replacement
    return clone


def counterfactual_cases(contract: dict, baseline: dict, action: str, *,
                         maximum: int = MAX_CASES) -> list[dict]:
    """Generate deterministic probes that flip a satisfied contract's decisions.

    Candidate values are finite and explicitly disclosed. This does not prove
    human-like understanding or guarantee coverage of all semantic boundaries.
    """
    normalized = normalize_contract(contract)
    if evaluate_contract(normalized, baseline, action)["status"] != "satisfied":
        raise ContractError("Baseline must satisfy the semantic contract")
    if type(maximum) is not int or not 1 <= maximum <= MAX_CASES:
        raise ContractError("Invalid case limit")
    cases: list[dict] = [{"id": "baseline", "state": baseline, "action": action}]
    seen = {(digest(baseline), action)}

    def add(cid: str, candidate: dict, act: str) -> bool:
        if len(cases) >= maximum:
            return False
        tag = (digest(candidate), act)
        if tag in seen:
            return False
        seen.add(tag)
        cases.append({"id": cid, "state": candidate, "action": act})
        return True

    for clause in normalized["clauses"]:
        if len(cases) >= maximum:
            break
        candidates = (True, False, 0, 1, -1, 2, "", "different", None, [])
        for replacement in candidates:
            candidate = _mutated(baseline, clause["path"], replacement)
            if candidate is None:
                continue
            result = evaluate_contract(normalized, candidate, action)
            if clause["id"] in result["violations"]:
                add(f"flip_{clause['id']}", candidate, action)
                break
        missing = _mutated(baseline, clause["path"], remove=True)
        if missing is not None:
            add(f"missing_{clause['id']}", missing, action)
    if len(cases) < maximum:
        action_candidate = "__unauthorized__"
        if action_candidate not in normalized["allowed_actions"]:
            add("unauthorized_action", baseline, action_candidate)
    return cases


def respond_to_challenge(contract: dict, public_challenge: dict) -> dict:
    """Reference deterministic solver, not an LLM nor proof of comprehension."""
    if not isinstance(public_challenge, dict) or set(public_challenge) != {"profile", "nonce", "contract_digest", "cases"}:
        raise ContractError("Malformed public challenge")
    if public_challenge["profile"] != PROFILE or public_challenge["contract_digest"] != contract_fingerprint(contract):
        raise ContractError("Challenge contract mismatch")
    cases = public_challenge["cases"]
    if not isinstance(cases, list) or not 1 <= len(cases) <= MAX_CASES:
        raise ContractError("Invalid challenge size")
    seen = set()
    answers = []
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "state", "action"}:
            raise ContractError("Malformed case")
        cid = case["id"]
        if not isinstance(cid, str) or not cid or cid in seen:
            raise ContractError("Invalid case ID")
        seen.add(cid)
        answers.append({"id": cid, "status": evaluate_contract(contract, case["state"], case["action"])["status"]})
    return {"nonce": public_challenge["nonce"],
            "contract_digest": public_challenge["contract_digest"], "answers": answers}
