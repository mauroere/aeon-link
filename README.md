# ÆON-Link — experimental semantic interoperability for AI agents

**Status: experimental, pre-alpha reference implementation.** This is not a universal standard, is not endorsed by any AI provider, and has not been tested with real LLM interoperability.

[Español](README.es.md) · [Python reference](aeon_link.py) · [Tests](tests/test_reference.py) · [MIT license](LICENSE)

## What's in this repository

- `aeon_link.py`: minimal, dependency-free Python reference implementation of message envelopes, version/ontology/capability negotiation, epistemic claim tags, evidence reference checks, local authorization checks and objective acknowledgments.
- `tests/test_reference.py`: five reference tests.
- `README.es.md`: Spanish quickstart.

Run:

```bash
python -m unittest discover -s tests -v
```

## What is not here (yet)

The broader **v0.2.0 extended prototype** previously developed also includes JSON Schema, Node.js, cross-language fixtures and additional tests. **It has not yet been imported in full into this repository.** This GitHub repository contains a reduced working reference, not the entire ZIP distribution.

The reference implementation does **not** run remote agents, call model APIs, provide a live A2A/MCP adapter, authenticate peer identities, verify source truth, guarantee semantic understanding, or establish cross-language canonical JSON equivalence.

The protocol is intended as an optional *semantic payload layer* compatible with existing infrastructure; it does not replace A2A, MCP, HTTP, or OAuth.

## Design principles

1. Express goals, constraints and uncertainty explicitly.
2. Keep verified facts distinct from hypotheses and unknowns.
3. Require references for asserted facts, while acknowledging that a reference is **not proof of truth**.
4. Reject incompatible ontology or capability claims.
5. Enforce authorization using **host-provided policy**, never untrusted message assertions.
6. Keep semantic-understanding tests separate from byte-for-byte acknowledgement checks.
7. Develop open conformance fixtures and independent benchmarks before making superiority claims.

## Next milestones

- Import and audit the extended v0.2.0 package, including schema, Node.js implementation and CI.
- Implement actual A2A/MCP payload adapters using current SDKs.
- Compare multiple LLM providers using blinded semantic-reconstruction benchmarks.
- Add cryptographic provenance and transport authentication.
- Publish versioned conformance results and a governance model.

MIT license. Contributions and criticism welcome.
