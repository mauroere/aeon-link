"""Portable verifiable semantic decision receipts (not cryptographic proofs).

A decision receipt commits to a formal contract, input state and decision
trace. Verification recomputes from the disclosed inputs; it says nothing
about a language model's private reasoning, external truth or authorization.
"""
from __future__ import annotations

from .canonical import canonical_bytes, digest, CanonicalizationError
from .semantics import (ContractError, normalize_contract, evaluate_contract,
                        contract_fingerprint, _predicate)

PROFILE = 'aeon.semantic.receipt/0.1'


def make_decision_receipt(contract: dict, state: dict, action: str) -> dict:
    norm = normalize_contract(contract)
    if not isinstance(state, dict) or not isinstance(action, str):
        raise ContractError('Expected JSON state and action string')
    try:
        canonical_bytes(state)
    except CanonicalizationError as exc:
        raise ContractError('Invalid decision state') from exc
    decision = evaluate_contract(norm, state, action)
    trace = []
    if action not in norm['allowed_actions']:
        trace.append({'id': 'action:unauthorized', 'outcome': 'fail'})
    else:
        for clause in norm['clauses']:
            result = _predicate(clause, state)
            if result is None:
                outcome = 'unknown'
            else:
                failed = (clause['mode'] == 'require' and not result) or (clause['mode'] == 'forbid' and result)
                outcome = 'fail' if failed else 'pass'
            trace.append({'id': clause['id'], 'outcome': outcome})
    return {'profile': PROFILE, 'contract_digest': contract_fingerprint(norm),
            'state_digest': digest(state), 'action': action,
            'decision': decision, 'trace': trace}


def verify_decision_receipt(contract: dict, state: dict, action: str, receipt: dict) -> bool:
    if not isinstance(receipt, dict):
        raise ContractError('Expected decision receipt')
    try:
        canonical_bytes(receipt)
    except CanonicalizationError as exc:
        raise ContractError('Invalid receipt') from exc
    expected = make_decision_receipt(contract, state, action)
    if receipt != expected:
        raise ContractError('Receipt does not match authoritative deterministic evaluation')
    return True
