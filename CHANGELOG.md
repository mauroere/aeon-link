# Changelog

## 0.4.0 (experimental)
- Executable semantic contracts, 3-valued predicate evaluator, nonce-bound challenge scoring.
- Deterministic counterfactual test-case generation and independent Python/Node conformance vectors.
- Evidence relationship DAG with explicit external-trust boundary, contested claims, potential contradictions.
- Versioned protocol envelope and capability negotiation for semantic/graph extensions.
- Regression CI covering Python 3.10–3.13 and Node.js.
- Paired benchmark scorer with Wilson confidence intervals, validation and explicit failure accounting (no measured model claims).
- Limitations stated: no real LLM benchmark or independently verified semantic comprehension.

# Changelog

## 0.3.0 — security and cross-runtime hardening
- Added restricted canonical JSON profile shared by Python and Node.js, stable for Unicode strings and safe integers.
- Added HS256 signed wrapper, trusted sender bindings and signed expiry.
- Added durable transactional SQLite replay detection, and local evidence byte hash checking.
- Added negative tests for tampering/expiry/unsafe numbers and bidirectional signed cross-runtime fixture.
- Kept no external model APIs, no provider-specific interoperability claim, no endorsement.



## 0.2.0 — 2026-11-20

- Separated semantic payload from transport protocol.
- Added exact ontology & feature negotiation and fail-closed validation.
- Added JSON Schema 2020-12 and referential integrity checks.
- Added local-policy authorization and deterministic acknowledgment validation.
- Added A2A/MCP payload mappings and 35 Python unit tests plus 8 Node.js checks and cross-language acknowledgment.
- Added security, conformance and adoption documentation.

## 0.1.0 — proof-of-concept predecessor

- Simple envelope, claim tagging, deterministic simulated acknowledgment.
