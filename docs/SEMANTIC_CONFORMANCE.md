# Semantic Contract Profile v0.2 (ÆON-Link 0.4, experimental)

**The semantics of this profile are deterministic and restricted.** Its claims should not be confused with proof of subjective reasoning, proof of factual truth, cryptographic authorization, or semantic equivalence of unrestricted natural language.

## Structure

```json
{
  "profile": "aeon.semantic.contract/0.2",
  "allowed_actions": ["observe", "read"],
  "clauses": [
    {"id":"dns", "mode":"require", "path":"/dns/resolved", "op":"eq", "value":true},
    {"id":"config", "mode":"forbid", "path":"/changes/config", "op":"eq", "value":true}
  ]
}
```

Clause IDs and action IDs use ASCII identifier syntax. Clauses: `require` or `forbid`; operators: `eq`, `ne`, `exists`, `gt`, `gte`, `lt`, `lte`, `in`. Paths use a constrained JSON Pointer subset with ASCII identifier keys and nonnegative array indices. Comparison of booleans to integers is disallowed; missing data yields **unknown**, never false, unless the operation explicitly checks existence.

Results have statuses `satisfied`, `violated`, `incomplete` plus ordered violated and unknown clause IDs. If action is not allowed, the result is immediately `violated`. Evaluation runs in an isolated pure function without executing tools or system changes.

## Challenges and counterfactuals

`create_challenge(contract, cases)` gives a public challenge with a random nonce and contract digest plus **a private answer key** that remains at the verifier. `respond_to_challenge` is a transparent reference implementation, not a model connection. `score_challenge` checks exact case IDs, nonce, digest and per-case outcomes.

`counterfactual_cases` creates a bounded set of deterministic mutations (one clause at a time; candidate Boolean, integer, empty and missing-state variants), plus an unauthorized-action case. **It is not exhaustive**, and finding the expected answer from a machine-readable contract is expected. If a test agent has evaluator code available it can pass without interpreting a human's original intent.

Do not use a passing challenge as authorization to call tools. Authorization belongs to the host and must be enforced separately after authentication, at execution time.

## Evidence relation graph v0.1

Nodes are typed `claim` or `evidence`; claims include `subject`, `predicate`, `value` and optional `context`. Typed links are `supports`, `refutes`, or `depends_on`. Support/refutation are evidence→claim; dependency is claim→claim. Cyclic dependencies are rejected. A claim is *linked* only when it has a support relation from an **externally trusted evidence ID** and all dependencies are linked. A verified refutation yields `contested`. Missing links yield `ungrounded` or `unresolved`. This models **declared links**, not the logical validity or veracity of propositions.

Two claims with identical subject, predicate and context but different values trigger `potential_contradictions`. Context boundaries prevent conflating observations of different environments.

## Cross-language conformance

`examples/generate_semantic_vectors.py` creates `fixtures/semantic-vectors.json` from the Python evaluator. Node runs the same contract and checks each outcome, including unauthorized actions, missing paths and Boolean-vs-integer mismatches. Fingerprints must match the restricted canonicalization profile; **not RFC 8785**.

## Real-model scientific evaluation (not completed)

1. Pre-register at least 100 unseen problems and their reference constraints.
2. Compare plain JSON/A2A baseline to AEON-Link with equivalent context and budgets.
3. Randomize problem order and replicate across multiple model/provider families.
4. Report correct outcomes, unsupported conclusions, latency, tokens, dollar cost and confidence intervals.
5. Publish failures and negative results. A protocol is not superior merely because an agent can echo its hash or run the provided interpreter.

## Limits and security

Hard caps: 64 clauses/cases, 128 graph nodes, 256 edges, canonical messages ≤1 MiB and maximum nesting 64. Do not run messages as code. No unsigned remote message can grant permissions. Secret test answers should remain outside shared contexts; untrusted agents may still infer machine-readable rules, so assessment measures reproducible decisions, not hidden mental states.
