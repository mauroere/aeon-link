# Security model (experimental)

## Threats explicitly NOT mitigated in 0.2.0

- Impersonated agents or replay across processes. `sender` and `message_id` are strings; no signature or authenticated channel is implemented.
- Fabricated evidence. A `source_uri` or `sha256` property is not independently verified.
- Prompt injection. Never forward untrusted `claim.text` or `objective.text` to a model as higher-priority instructions.
- Unsafe tool execution. `authorize_task` only checks local parameters; it is not a sandbox or tool authority, and does not execute actions.
- Unbounded input / denial of service. Callers must impose request size, depth, time and rate limits before parsing.
- Privacy leakage via logs, evidence URIs or result messages. Sensitive content needs minimization, retention limits and access controls.
- Distributed duplicate requests. `ReplayGuard` is local, ephemeral, nonpersistent.

## Production prerequisites

- Establish TLS and mutual agent identity before processing any envelope.
- Bind the authorized identity to the actual session, not to the claimed `sender` string.
- Authorize every requested operation at the service boundary using minimum permissions and explicit approvals for side effects.
- Provide authenticated and tamper-evident evidence and signed receipts if provenance is claimed.
- Require transport-layer idempotency keys, durable deduplication and audit logs for effectful operations.
- Independent validation of outputs and defense-in-depth against prompt injection.
- Fuzz schema validation and support downgrade-safe version negotiation.

**Never deploy this proof of concept as a publicly reachable privileged agent gateway.**

## v0.3.0 hardening

- `sign_envelope` / `verify_signed` (Python) and `signEnvelope` / `verifySigned` (Node) implement optional HS256 over the restricted canonical profile. Shared secrets MUST be at least 32 bytes and provisioned securely; never commit real secrets.
- Keys are bound to a trusted sender by the receiver's local registry. Never trust `sender`, `key_id`, or `constraints` as proof of permission.
- `SQLiteReplayGuard` persists authenticated `(sender,message_id)` entries with a transaction. It cannot coordinate independent installations using unrelated databases; large distributed deployments need shared storage and monitoring.
- `parse_canonical` and `parseCanonical` reject duplicate JSON keys on the wire by enforcing canonical reserialization. JSON decoded by a permissive parser is NOT automatically guaranteed duplicate-safe.
- Content-hash checks verify the exact bytes of provided evidence, not the veracity of any claim or identity of its source.
- Transport must provide TLS, peer authentication, time synchronization, key rotation, capacity limits and logging. HMAC is not an authorization grant or an alternative to OAuth.
