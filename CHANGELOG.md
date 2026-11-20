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

## SDK 0.5.0 (experimental; wire profile remains 0.4.0)

- Add receiver-side authenticated, recipient-bound and policy-bound ingress
  with durable Python replay registration and awaited host-provided Node replay (explicit success confirmation required).
- Refuse non-plain Node objects, accessors, sparse arrays, negative zero, and
  reserved prototype-property keys in canonical JSON; mirror reserved keys in
  Python to preserve parity.
- Fix eleven Python/Node validator disagreements found by paired differential
  tests (sender/recipient length, invalid date-time values and related cases).
- Add counterfactual plus invariant semantic probes, deterministic decision
  receipts and a multi-agent response scoring helper.
- Validate 400 randomized canonical encodings, 121 paired validator cases and
  seven cross-language decision receipts, in addition to unit test suites.
- Add explicit documentation of semantic and operational security gaps.

- Fix environment-dependent RFC3339 handling: Python now validates dates
  with a built-in strict parser instead of relying on optional jsonschema extras.
