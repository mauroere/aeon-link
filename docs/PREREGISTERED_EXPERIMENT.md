# ÆON-Link v0.8 — prospective synthetic comparison with disjoint logical groups

**Status: methodology update, not a successful model experiment.** As of 2026-11-20 there are no authorized commercial-model API results in this project. Previous 0.7 protocol and its original digest are preserved in [the archived document](PREREGISTERED_EXPERIMENT_V07_ARCHIVE.md), instead of silently rewriting the old analysis plan.

## Why 0.8 supersedes 0.7

The 0.7 generator separated rows without keeping their underlying scenarios in one split. When the noise fields `observation_id` and `comment` were ignored, **65 decision-equivalent groups appeared in both pilot and evaluation**. That made the held-out evaluation vulnerable to prompt or strategy tuning on near-identical examples. This flaw was identified before collecting commercial-model outcomes.

## Locked synthetic dataset v2

- Generator: `aeon.research.eval/0.2`, seed `20261120`, 360 cases, six template domains.
- **SHA-256**: `0c859bebae91607648836c49f604c68c1eeeebffabe091d6bd222855a097ddd8`.
- Pilot: **144** rows, **114** logical groups (60 satisfied, 56 violated, 28 incomplete).
- Evaluation: **216** rows, **174** logical groups (84 satisfied, 88 violated, 44 incomplete).
- Overlap in logical groups: **0**; verified with `assert_split_integrity`.
- Grouping equivalence ignores observation ID and untrusted comment text, preserving all policy, action and decision-relevant state. This is a domain-specific equivalence rule, not a general-purpose semantic equivalence proof.
- Each policy family varies a decision-relevant numeric observation and its associated threshold, rather than varying only decoy IDs. Case classes are approximately stratified across splits.
- All evaluations recompute the deterministic oracle labels; `score_records` rejects a contaminated full corpus.

Run:

```sh
python -m pip install -e .
python examples/audit_research_corpus.py
python -m unittest discover -s tests -v
node --test js/*.test.mjs js/test.mjs
```

## Predeclared contrasts

On the same model, transport, task facts and budget compare explicit natural-language rules (`natural`), structured JSON (`structured-json`), and ÆON semantic envelopes (`aeon-semantic`). The receiving model returns `satisfied`, `violated` or `incomplete`; invalid/missing outputs count incorrect. Each split is scored in full. The hard-coded oracle and the prompt rules are public, so this is **not** a blind independent benchmark.

Primary exploratory estimate: paired percentage-point accuracy advantage against **each** baseline. Also report logical-group-balanced accuracy, per-domain advantages, errors, prompt tokens, and latency. The scoring code supplies row-level McNemar and bootstrap measures alongside domain-cluster bootstrap diagnostics. **Do not use row-level p-values as evidence of independent generalization:** there are only six reused domain templates, and even logical groups are not independently sampled real tasks.

Prospective practical goal: ≥20% relative error reduction against both baselines, with ≤25% overhead in tokens and latency, replicated on more than one model family and a separately collected external corpus. An entirely successful synthetic result would still justify only further study, not general superiority. Do not interpret a domain-cluster interval with 6 domains as conclusive.

## Research integrity and next requirements

1. Freeze model IDs, sampling settings, date, instructions and financial budget **before** evaluating holdout.
2. Test pilot only for runtime and schema problems. No prompt modifications after inspecting evaluation output.
3. Collect at least 100 **independent external tasks** from independently created source material across more than six domain templates; require blind holdout controlled by reviewers.
4. At least two commercially distinct model families; report all failures and API errors.
5. Independent review of benchmark labels and claim-grading, and independent security assessment.
6. Full A2A/MCP comparisons should fix transport and tools, change only semantic payload; this repo currently benchmarks presentation formats, not those protocols directly.

**No evidence of commercial agent-to-agent superiority or universal adoption exists at this stage.**
