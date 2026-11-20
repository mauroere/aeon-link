# Semantic challenge and verifiable decision receipts

SDK 0.5.0 adds:

- `metamorphic_cases`: generates targeted counterfactuals plus invariant
  perturbations outside the paths named in the contract.
- `prepare_semantic_probe`: returns a public challenge and a private answer key.
- `analyze_responses`: scores externally supplied agent decisions against that
  key, without contacting an LLM or inventing measurements.
- `make_decision_receipt` and `verify_decision_receipt`: produce/recompute a
  deterministic trace of each clause's `pass`, `fail`, or `unknown` outcome,
  binding it to the contract hash, state hash and action.

Python and Node.js agree on seven checked cross-runtime receipt fixtures.

**A verified receipt is not a cryptographic signature and does not prove that
an AI actually understood natural language.** A transparent deterministic
solver can create receipts. Receipts allow reproducible decision **auditing**;
a downstream operation still needs authentication, authorization and evidence
validation. Combine with a signed AEON envelope when tamper evidence is needed.

A complete model-to-model scientific benchmark remains future work. To claim
superiority, compare against a budget-matched baseline using unseen cases,
independently checked outcomes, multiple provider families, pre-registered
metrics and statistical confidence estimates.
