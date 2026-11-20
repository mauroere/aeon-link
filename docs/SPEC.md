# ÆON-Link 0.3.0 — Experimental Semantic Payload Specification

> **Experimental draft:** not a ratified standard or a security certification. Uppercase requirement words below are design requirements for this prototype, not assertions of industry adoption.

## Goals

Different autonomous agents should be able to exchange tasks with (a) a known semantic profile; (b) explicitly classified claims; (c) references to supporting evidence; (d) hard-coded restrictions; and (e) verifiable task acknowledgments. We aim for transport independence and fail-closed semantics.

## Envelope

Each message is a JSON object conforming to `src/aeon_link/schema.json`. Required keys:

- `protocol`: fixed `aeon-link`.
- `version`: fixed `0.3.0` in this implementation.
- `ontology`: fixed `urn:aeon-link:ontology:core:0.3.0`.
- `message_id`: a UUID.
- `kind`: `hello`, `task`, `result`, or `error`.
- `sender` and `recipient`: string identities **as claimed in data**, not authenticated identities.
- `body`: strictly defined by `kind`.

Unknown envelope and body fields MUST be rejected. Additional transport metadata SHOULD be managed outside this message.

## Handshake

Agents send reciprocal `hello` messages containing `versions`, `ontologies`, `features`. This release requires `0.3.0` and the exact registered core ontology. No downgrade or implicit ontology translation is permitted. Features are intersected and required features can be asserted. A host MUST validate a handshake before relying on the semantics of incoming task messages.

## Claim semantics

`fact`: an assertion with >=1 `evidence_id` referencing an evidence object present in the same task. **FACT does not mean independently verified truth.**

`hypothesis`: candidate explanation. The evidence reference list may be empty. Never upgrade hypothesis to fact solely because another agent has high confidence.

`unknown`: information not established. The evidence reference list may be empty.

`evidence`: a local ID plus `source_uri`; an optional SHA-256 digest of referenced content and timestamp. Authenticity, retrieval, existence and digest checking require a separate verifier, not implemented in 0.3.0 by the core (optional local SHA-256 content checks are available). A verifier SHOULD label its verification status independently of claim status in a future revision.

Claim IDs and evidence IDs MUST be unique within the task. Every referenced evidence ID MUST exist. Agents SHOULD preserve the underlying source and distinguish observation from inference.

## Task semantics

A task includes a uniquely identified objective, a human-readable text intent, nonempty success criteria, constraints, a requested action, claims, and evidence. `read_only=true` prohibits `write` and `execute`. Hosts MUST check action permissions against authenticated authorization context, not on authority of the sender or `constraints` alone. This reference implementation **never performs actions**.

## Result and acknowledgment

A result references `in_reply_to`, `objective_id`, plus `objective_digest` and `constraints_digest`, which are SHA-256 over `canonical_bytes()` produced by the Python SDK. `verify_ack` checks sender/recipient direction, reply target, the two hashes and exact objective text. This shows the correct payload was returned, **not** semantic equivalence or successful execution. Hashes use the deliberately restricted canonical JSON profile (ASCII keys, UTF-8 strings, safe integers only). This is NOT RFC 8785/JCS; any profile disagreement MUST fail closed.

## A2A and MCP mapping

A2A: place the whole AEON envelope in a structured-data Part, for example `{"data":{"aeon_link":...}}`. The official A2A SDK / transport remains responsible for actual AgentCard, task state, authentication and message framing. No AgentCard or A2A networking is implemented in this release.

MCP: a tool may return the envelope via `structuredContent.aeon_link`. The official MCP SDK is responsible for tool descriptions, auth, security and JSON-RPC framing. The payload mapping provided here is *not* a functioning MCP server.

## Errors and compatibility

Malformed frames, unknown fields, mismatched ontologies or missing critical feature support MUST fail with an error. Implementations MUST treat model-generated messages as untrusted input. Implementations MUST NOT claim cryptographic proof of provenance, authorization, semantic comprehension or model correctness based on schema validation alone.

## Compatibility / release policy

0.3.0 is intentionally a single-profile research implementation, not a full extensible registry. Proposed additions and their threat models should be reviewed before accepting more expressive message kinds. Do not advertise compatibility with a provider until tested using the provider's actual API.

## Cross-language vector

`fixtures/cross-language-vectors.json` contains a complete Python-generated message and digests. `js/test.mjs` confirms Node.js obtains identical hashes for this fixture. `js/create-ack.mjs` then emits a Node-generated result that Python `verify_ack` checks. This is a very small interoperability smoke test, not an exhaustive cross-language guarantee.

## Signed wrapper (optional, v0.3.0)

An HMAC wrapper contains `envelope`, `meta` (`alg=HS256`, `key_id`, `issued_at`, `expires_at`) and a hex `signature`. Signature input is `HMAC_SHA256(secret, b"AEON-LINK-HMAC-SHA256-v1\x00" + canonical_bytes({"envelope":...,"meta":...}))`. The receiver MUST obtain the key-to-sender mapping from a trusted source outside the message. This is shared-secret authentication only, not a distributed PKI.

The trusted receiver SHOULD verify the signature and message lifetime, apply `SQLiteReplayGuard.check` before doing any side effects, then evaluate the request under independent host-side policy. Replay expiry is taken from the verified signature metadata (not from caller-supplied fields). Clock skew allowance: 30 seconds. Maximum signed message lifetime: 300 seconds.

The restricted canonical encoding uses JSON with ASCII identifier keys, Unicode strings without unpaired surrogates, booleans, null, arrays and safe signed integers. No floating-point or numbers larger than 2^53-1. It sorts object keys lexicographically and emits compact UTF-8; raw canonical parsing compares input bytes against reserialized bytes, rejecting duplicate keys and alternative encodings. **This is not RFC 8785.**

There is no proof of semantic understanding, no automatic agent discovery, no network transport, no cross-organizational key exchange and no authority to execute an action.
