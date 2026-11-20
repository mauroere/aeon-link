# ÆON-Link — experimental semantic interoperability for AI agents

[![Status: experimental](https://img.shields.io/badge/status-experimental-orange)](#status) 

**Current release: 0.4.0 (proof of concept).** This is **not** an adopted industry standard, does **not** connect to real LLM APIs, and does **not** independently authenticate agents or verify the truth of sources. It is a proposal and runnable SDK for semantically tagged messages between different agent systems.

**Positioning:** AEON-Link is an optional *semantic payload layer*. It is designed to sit **on top of** existing agent protocols; it does not replace A2A, MCP, HTTP, OAuth, or provider SDKs.

[Leer en español](README.es.md)

## What works today

- Strict JSON Schema Draft 2020-12 envelope validation (schema packaged with the Python SDK).
- Version + core ontology + feature handshake that fails closed on incompatibility.
- Explicit `fact`, `hypothesis`, `unknown` claim classification and evidence ID referential integrity.
- Objective/constraint acknowledgment using reproducible Python JSON digests.
- Host-provided authorization decisions; sender assertions do not grant permissions.
- In-memory duplicate message detection.
- Standalone examples mapping AEON-Link envelopes into A2A DataParts and MCP tool-result `structuredContent`. **Mappings are not full A2A or MCP implementations.**
- Offline demo and automated tests without API credentials or external network access.
- Minimal Node.js runtime with shared fixtures; **cross-language handshake/digest/acknowledgment checks** validated against the Python implementation.

## Install and run

Requires Python 3.10+.

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python examples/demo.py
node --test js/test.mjs
node js/create-ack.mjs < fixtures/python-task.json > /tmp/aeon-node-ack.json
python examples/check_node_ack.py /tmp/aeon-node-ack.json
```

Validate a file: `aeon-link path/to/envelope.json`, or `aeon-link -` for stdin.

## Example: two agent endpoints sharing a semantic contract

```python
from aeon_link import hello, negotiate, message, LocalPolicy, authorize_task

left = hello("agent-x", "agent-y")
right = hello("agent-y", "agent-x")
agreement = negotiate(left, right, required_features=["claims.v1"])

task = message("task", "agent-x", "agent-y", {
    "objective": {"id": "investigate-1", "text": "Assess the outage", "success_criteria": ["List evidence gaps"]},
    "constraints": {"read_only": True},
    "action": "observe", "claims": [], "evidence": [],
})
# The host supplies this policy after authenticating the peer.
authorize_task(task, LocalPolicy(frozenset({"observe"}), verified_sender="agent-x"))
```

See `examples/demo.py` for task/result acknowledgment and payload adapters.

## Status and limitations

These are intentional boundaries of the current prototype:

1. A reference such as `source_uri` **does not prove the source is authentic or true**. The validator checks that a cited evidence ID exists, nothing more.
2. LocalPolicy checks a host-supplied identity but does **not** authenticate that identity. An HTTP deployment needs TLS, authentication and signed authorization outside this package.
3. An acknowledgment digest proves receipt of *identical encoded content*, not that the remote model genuinely understands the meaning.
4. The pack/unpack adapters are payload mappings only; neither a live A2A implementation nor a live MCP server is included.
5. No objective execution, agent network communication, API access, distributed storage, telemetry or persistent replay protection is implemented.
6. The Node.js validator is a manually written subset of the Python JSON Schema contract; it is **not yet a complete independent conformance implementation**.
7. `canonical_bytes` is reproducible for ordinary JSON objects in the same Python implementation; it is **not RFC 8785 / JCS** and cross-language agreement is not established.
8. Since the SDK does not execute instructions, it is not an authorization or sandbox boundary for a separate execution engine.

## Roadmap toward broader adoption

1. Complete independent interoperability suite (Python ⇄ TypeScript ⇄ Rust) and cross-language canonicalization (RFC 8785).
2. Real A2A 1.0 and MCP 2026-07-28 adapters, plus test agents using their official SDKs.
3. Signed evidence and provenance receipts (inspired by W3C PROV-O), identity and authorization.
4. Semantic compatibility tests using independent LLM providers and human-graded correctness.
5. Public conformance suite with test vectors, fuzzing and versioned registries.
6. Peer review, implementer feedback and open specification governance.

## Documents

- [Normative-ish experimental specification](docs/SPEC.md)
- [Security limitations](docs/SECURITY.md)
- [Contributing and governance](docs/GOVERNANCE.md)
- [Adoption and benchmarks](docs/BENCHMARKS.md)

## References

- A2A 1.0: https://a2a-protocol.org/v1.0.0/specification/
- MCP 2026-07-28: https://modelcontextprotocol.io/specification/2026-07-28
- JSON Schema Draft 2020-12: https://json-schema.org/draft/2020-12/
- W3C PROV-O: https://www.w3.org/TR/prov-o/

## License

MIT — see [LICENSE](LICENSE).

## v0.3.0 security and interoperability hardening

- The Python and Node.js implementations now reject floating-point values, unsafe integers, unpaired Unicode surrogates and non-ASCII object keys in canonicalized data. This deliberate profile is NOT RFC 8785.
- Message authentication using externally provisioned 32-byte-or-longer HMAC keys (HS256), key-to-sender binding, signature-verified expiry and time-skew checks.
- Process-restart-safe replay protection with Python SQLite (transactional UNIQUE constraint).
- Explicit content SHA-256 checking for locally provided evidence bytes; this is **not source verification**.
- Bidirectional Python↔Node signed-message test with Unicode content. No model API or secret is necessary to run the fixture.

Run security tests:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
node --test js/*.test.mjs js/test.mjs
python examples/cross_runtime_security.py
```

### Verified receipt pattern

1. Receive over authenticated transport (HTTPS/TLS).
2. Parse canonical bytes and validate JSON/schema.
3. Verify signature, source key binding and expiry against a LOCAL trust registry.
4. Reject replays with a shared/durable replay store.
5. Authorize the action using the verified identity and LOCAL policies.
6. Only then evaluate/expose the request to a model or tool. The SDK itself runs no external action.

Do not use demo keys in production. Real external AI model communication, semantics benchmarking, provider adapters and PKI remain unimplemented.


## v0.4.0: executable semantic contracts and evidence relations

A new optional **semantic decision profile** represents requirements and prohibitions as deterministic predicates over JSON state. The challenger can generate counterfactual cases, retain the expected outcomes privately, and score an agent's answers by exact case ID, nonce and contract digest. The responder can also use a reference deterministic evaluator; passing alone **does not prove that an LLM understands natural language**, only that the contract's machine-readable decisions are reproduced.

The new **evidence relationship graph** validates support, refutation and dependency links, rejects cycles and duplicate IDs, and reports potential claim contradictions with context separation. **External verification is mandatory** before marking any evidence as trusted. This is not a truth detector or provenance oracle.

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
node --test js/*.test.mjs
python examples/generate_semantic_vectors.py
```

Read [Semantic profile and test protocol](docs/SEMANTIC_CONFORMANCE.md). These features are a research extension, not a standardized feature of A2A or MCP.

A local [paired semantic benchmark scorer](src/aeon_link/benchmark.py) is included; the sample data are synthetic and **do not** show a performance improvement over baseline protocols.

## SDK 0.5.0 hardening — wire format remains 0.4.0

This release adds a receiver-side signed-message gate, persistent replay checks
(Python), awaited host-provided replay (Node), stricter cross-runtime JSON
validation, metamorphic counterfactual/invariance tests and portable semantic
decision receipts. **These are deterministic engineering controls, not a proof
of AI understanding or superiority over A2A/MCP.**

Run the expanded suite after `pip install -e .`:

```sh
python -m unittest discover -s tests -v
node --test js/*.test.mjs
python examples/generate_canonical_fuzz.py > /tmp/aeon-fuzz.json
node js/verify-fuzz.mjs /tmp/aeon-fuzz.json
python examples/generate_validation_vectors.py > /tmp/aeon-validate.json
node js/verify-validation.mjs /tmp/aeon-validate.json
python examples/generate_receipt_vectors.py > /tmp/aeon-receipts.json
node js/verify-receipts.mjs /tmp/aeon-receipts.json
```

The canonical fuzz fixture contains 400 reproducible inputs; the validation
parity corpus contains 121 inputs; the decision receipt corpus contains seven.
See [inbound security](docs/INBOUND_SECURITY.md) and
[decision receipt limitations](docs/DECISION_RECEIPTS.md).

**Protocol wire version:** 0.4.0 · **SDK version:** 0.5.0. The canonical
profile rejects prototype-reserved object keys that were previously allowed;
implementations must fail closed rather than silently reinterpret data.

## SDK 0.6.0 — verifiable progress toward independent assessment

The wire envelope remains `0.4.0`. Version 0.6.0 adds **optional** official-API HTTP adapters for OpenAI Responses, Anthropic Messages and Gemini generateContent, a deliberately opt-in **paid live paired evaluation** harness, GitHub CodeQL automated security workflow, Dependabot configuration, vulnerability-reporting instructions and an external-assessor checklist. No API keys or model connections were available during this implementation: provider responses were mocked in the tests, **not run live**. CodeQL is an external scanner, **not** a completed human independent audit.

Additional fix: Python's SQLite replay guard now closes its database connection after initialization. HTTP adapters use fixed HTTPS origins, reject redirects, bound messages and avoid logging provider error bodies or API keys.

```bash
python -m unittest discover -s tests -v
node --test js/*.test.mjs js/test.mjs
python examples/live_provider_benchmark.py --help
```

See [status and adoption ledger](docs/INDEPENDENT_REVIEW_AND_ADOPTION.md) and [security reporting](SECURITY.md). A2A and MCP are not alternatives to AEON-Link payloads; benchmark the **same protocol with and without** the enriched semantic payload, not these different layers against one another.


## New in v0.7: falsifiable three-condition research

[Pre-registered evaluation protocol](docs/PREREGISTERED_EXPERIMENT.md). The new `aeon_link.research_eval` module compares natural-language, structured JSON and AEON semantic payloads on 360 synthetic, oracle-scored cases across six domains, with pilot/evaluation splits, adversarial data, paired exact McNemar tests, 97.5% bootstrap intervals and per-domain reporting. **No commercial model performance results have been collected.** No A2A/MCP protocol comparison is claimed.

```sh
python examples/preregistered_research.py generate --output aeon-research-corpus.json
python examples/preregistered_research.py live --provider openai --model YOUR_MODEL --limit 5 --i-accept-api-costs
```

This does not silently call external APIs, and `--i-accept-api-costs` is always required for live trials.


**Optional GitHub Actions pilot:** `Manual paid LLM pilot (opt-in only)` requires a preconfigured provider API secret and an explicit paid-call selection; max 12 cases (36 calls), no automatic trigger.
