"""Conformance probes for semantic invariance and counterfactual sensitivity.

This is deterministic behavioral testing of a disclosed formal contract. It
is *not* an empirical demonstration of LLM comprehension, and may be solved
by an agent executing the same disclosed reference evaluator.
"""
from __future__ import annotations

import copy
import secrets
from typing import Any

from .canonical import canonical_bytes, digest, CanonicalizationError
from .semantics import (ContractError, MAX_CASES, normalize_contract,
                        evaluate_contract, counterfactual_cases,
                        create_challenge, score_challenge, _tokens)


def _safe_contract_state(state: dict) -> None:
    if not isinstance(state, dict):
        raise ContractError('State must be an object')
    try:
        canonical_bytes(state)
    except CanonicalizationError as exc:
        raise ContractError(f'Invalid state: {exc}') from exc


def metamorphic_cases(contract: dict, baseline: dict, action: str, *,
                      maximum: int = MAX_CASES) -> list[dict]:
    """Generate counterfactuals and unrelated-change invariant probes.

    Decoy fields are placed only at the top level outside all referenced
    JSON pointer roots, preserving the value of every referenced pointer.
    Invariants are checked by the reference evaluator before publication.
    """
    norm = normalize_contract(contract)
    _safe_contract_state(baseline)
    if type(maximum) is not int or not 1 <= maximum <= MAX_CASES:
        raise ContractError('Case limit must be an integer within bounds')
    cases = counterfactual_cases(norm, baseline, action, maximum=maximum)
    if len(cases) >= maximum:
        return cases
    used_roots = { _tokens(clause['path'])[0] for clause in norm['clauses'] }
    fingerprints = {(digest(c['state']), c['action']) for c in cases}
    baseline_outcome = evaluate_contract(norm, baseline, action)
    for suffix, value in [('boolean', True), ('null', None), ('unicode', 'é 🚀'),
                          ('nested', {'flag': False, 'count': 2})]:
        if len(cases) >= maximum:
            break
        field = f'aeon_unrelated_{suffix}'
        if field in used_roots or field in baseline:
            continue
        state = copy.deepcopy(baseline)
        state[field] = value
        if evaluate_contract(norm, state, action) != baseline_outcome:
            raise ContractError('Internal invariance check failed')
        tag = (digest(state), action)
        if tag not in fingerprints:
            cases.append({'id': f'invariant_{suffix}', 'state': state, 'action': action})
            fingerprints.add(tag)
    return cases


def prepare_semantic_probe(contract: dict, baseline: dict, action: str, *,
                           maximum: int = MAX_CASES):
    """Return public challenge + private key; never send the key to the responder."""
    cases = metamorphic_cases(contract, baseline, action, maximum=maximum)
    return create_challenge(contract, cases)


def analyze_responses(key, responses: dict[str, dict]) -> dict:
    """Compare a set of submitted responses against a private test key.

    Only scores pre-recorded observations; refuses missing or duplicate agent
    identity and does not claim agents are independent or outperform baselines.
    """
    if not isinstance(responses, dict) or not responses:
        raise ContractError('At least one named response is required')
    scores = {}
    for agent_id, response in sorted(responses.items()):
        if not isinstance(agent_id, str) or not agent_id or len(agent_id) > 128:
            raise ContractError('Invalid agent label')
        scores[agent_id] = score_challenge(key, response)
    return {'profile': 'aeon.semantic.probe/0.1', 'agents': scores,
            'note': 'Behavioral conformity to formal predicates; not a proof of AI comprehension.'}
