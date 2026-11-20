# Inbound security boundary (SDK 0.5.0, wire 0.4.0)

The experimental helper `receive_signed` (Python) and `receiveSigned` (Node)
provide a **receiver-side validation gate**, not a sandbox or IAM system.

## Enforced order

1. Parse canonical UTF-8 **wire bytes** (reject duplicate/ambiguous JSON).
2. Validate the AEON-Link envelope and HMAC with a locally trusted key registry.
3. Check that the authenticated envelope is addressed to the **local recipient**.
4. For tasks, require receiver-provided policy bound to the authenticated sender
   and permit only actions in the policy.
5. Reject replay before returning an envelope to downstream processing.

Python's SQLiteReplayGuard uses a transactional unique key across process restarts.
Node's `receiveSigned` is **async** and awaits a host-supplied
`replayGuard.checkAndRecord(sender, messageId, expiresAt, now)`; the host
**MUST** return `true` only after atomic, durable insertion; reject duplicates
with an exception or `false`. A missing/undefined return is rejected. The host
**MUST** implement durable atomicity across processes. An in-memory Set in
unit tests is NOT suitable for production.

This ordering deliberately makes bad signatures and unauthorized tasks fail
without consuming a replay token. An authenticated request is not authorization
to execute arbitrary operations. All tool invocations must pass their own
service-layer permission checks and run with minimum permissions.

## Explicit non-guarantees

- A signature proves possession of a prearranged shared secret, not authority
  to operate infrastructure or that the claimed source is truthful.
- A message marked `fact` with a digest does not become verified evidence.
- SQLite replay registration and downstream actions are not one atomic
  transaction. To avoid duplicate side effects after a crash, downstream tools
  need independent idempotency keys / transactional outbox design.
- Clock accuracy, key rotation, confidential storage, TLS, DoS rate limits,
  identity provisioning and privacy-sensitive logging remain the responsibility
  of the host.
- This is an **optional** secure-ingress profile, not a formal security audit
  or a claim of vendor-certified interoperability.

## Wire compatibility

The SDK release is 0.5.0 and the envelope still uses the unchanged **0.4.0**
version and ontology. Existing v0.4 canonical payloads with reserved JS prototype
keys are now rejected, a deliberate security hardening incompatible with that
small input subset. Treat this as a profile restriction and fail closed.

The task validator independently verifies evidence timestamps in Python and
Node (valid calendar dates, valid clock and UTC offsets); optional JSON Schema
format-checking packages cannot silently relax this rule. Leap seconds are
not accepted by this deliberately strict subset.
