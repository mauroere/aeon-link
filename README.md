# ÆON-Link — experimental semantic interoperability for AI agents

[![Status: experimental](https://img.shields.io/badge/status-experimental-orange)](#status) 

**Current release: 0.2.0 (proof of concept).** This is **not** an adopted industry standard, does **not** connect to real LLM APIs, and does **not** independently authenticate agents or verify the truth of sources. It is a proposal and runnable SDK for semantically tagged messages between different agent systems.

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