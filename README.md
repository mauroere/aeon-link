# ÆON-Link — experimental AI-to-AI semantic messages

**Version: 0.3.0 · pre-alpha · open source (MIT)**

[Español](README.es.md) · [Reference code](aeon_link.py) · [Security tests](tests/test_security.py) · [CI](.github/workflows/ci.yml)

ÆON-Link is an experimental, optional **semantic envelope** for communication between AI agents. It is **not** a universal standard, a replacement for A2A/MCP, or a proven solution to agent understanding. No AI vendor endorses it.

## What changed in 0.3.0

- Deterministic, restricted UTF-8 JSON encoding for Python and Node.js (`aeon_canonical.py`, `js/aeon.mjs`). Object keys are ASCII identifiers; values support Unicode strings, arrays, booleans, null and safe integers. Floating point and large integers fail closed. **Not RFC 8785/JCS.**
- Optional HMAC-SHA256 envelope signatures with locally trusted key-to-sender binding, signed expiry and clock skew checks (`aeon_auth.py`, `js/aeon.mjs`).
- Transactional, persistent replay detection with SQLite (`aeon_replay.py`). Check **after** signature verification and **before** side effects.
- Optional SHA-256 equality check over provided evidence bytes. This does **not** prove the evidence source is authentic or the claim is true.
- Automated security unit tests for Python and Node.js.

## Try it

Requires Python 3.10+ and/or Node.js 22+; no third-party Python packages.

```sh
python -m unittest discover -s tests -v
node --test js/*.test.mjs
```

Python sample:

```python
from aeon_link import hello, message
from aeon_auth import TrustedKey, sign_envelope, verify_signed
from aeon_replay import SQLiteReplayGuard

secret = b"example-key-only-not-for-production-32bytes!"
task = message("task", "alpha", "beta", {
    "objective": {"id": "o1", "text": "Analyze an incident"},
    "constraints": {"read_only": True},
    "action": "observe",
    "claims": [], "evidence": [],
})
wire = sign_envelope(task, key_id="alpha-key", secret=secret)
verified = verify_signed(wire, {"alpha-key": TrustedKey("alpha", secret)})
SQLiteReplayGuard("seen.sqlite").check(verified, now=wire["meta"]["issued_at"])
# Only NOW consider a separate host-side authorization decision.
```

**The sample keys are demonstrations; never commit real secrets.** Production also needs HTTPS/TLS, separate authentication and authorization policy, secure key provisioning, rate limiting, observability and shared replay storage when using multiple processes/hosts.

## Repository scope

This GitHub repository publishes a **minimal standalone Python/Node hardening reference**. The independently packaged expanded **v0.3.0 proof of concept** (Python SDK with JSON Schema, full adapters, extended tests and cross-runtime signed fixture) is distributed separately with the project development artifacts. The two distributions are not yet identical.

The repository reference intentionally has **no real model API integration, no provider-certified A2A/MCP SDK, no real tool execution and no semantic comprehension benchmark**. A response echoing a hash is **not** proof of understanding.

### Design priorities
1. Strict, versioned meaning and data shape.
2. Receiver-provided trust and local authorization, never self-asserted access.
3. Verifiable message integrity, expiry, replay detection and error cases.
4. Cross-runtime conformance vectors and external independent benchmarks.
5. Vendor-neutral interoperability through established A2A/MCP transport mechanisms.

MIT-licensed experimental research. Issues and critical review are welcome.