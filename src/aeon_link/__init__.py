"""Public interface for the experimental AEON-Link SDK 0.7.0 (wire 0.4.0)."""
from .core import (
    VERSION, ONTOLOGY, FEATURES, Agreement, LocalPolicy, ProtocolError,
    ReplayGuard, authorize_task, canonical_bytes, digest, hello, make_ack_result,
    message, negotiate, validate_envelope, verify_ack,
)
from .adapters import as_a2a_data_part, from_a2a_data_part, as_mcp_tool_result, from_mcp_tool_result

__all__ = [
    "VERSION", "ONTOLOGY", "FEATURES", "Agreement", "LocalPolicy", "ProtocolError",
    "ReplayGuard", "authorize_task", "canonical_bytes", "digest", "hello", "make_ack_result",
    "message", "negotiate", "validate_envelope", "verify_ack",
    "as_a2a_data_part", "from_a2a_data_part", "as_mcp_tool_result", "from_mcp_tool_result",
]

from .canonical import CanonicalizationError, parse_canonical
from .auth import TrustedKey, VerifiedMessage, sign_envelope, verify_signed
from .replay import SQLiteReplayGuard
__all__ += ['CanonicalizationError', 'parse_canonical', 'TrustedKey',
            'VerifiedMessage', 'sign_envelope', 'verify_signed', 'SQLiteReplayGuard']

from .evidence import verify_evidence_content
__all__ += ['verify_evidence_content']

from .semantics import (PROFILE as SEMANTIC_PROFILE, ContractError, normalize_contract,
    contract_fingerprint, evaluate_contract, counterfactual_cases, create_challenge,
    score_challenge, respond_to_challenge)
from .evidence_graph import (PROFILE as EVIDENCE_GRAPH_PROFILE, GraphError,
    validate_graph, analyze_graph)
__all__ += ['SEMANTIC_PROFILE', 'ContractError', 'normalize_contract',
    'contract_fingerprint', 'evaluate_contract', 'counterfactual_cases',
    'create_challenge', 'score_challenge', 'respond_to_challenge',
    'EVIDENCE_GRAPH_PROFILE', 'GraphError', 'validate_graph', 'analyze_graph']

from .benchmark import score_records, BenchmarkError
__all__ += ["score_records", "BenchmarkError"]
from .ingress import InboundReceipt, receive_signed
from .metamorphic import metamorphic_cases, prepare_semantic_probe, analyze_responses
from .receipts import make_decision_receipt, verify_decision_receipt
__all__ += ['InboundReceipt','receive_signed','metamorphic_cases','prepare_semantic_probe',
            'analyze_responses','make_decision_receipt','verify_decision_receipt']
