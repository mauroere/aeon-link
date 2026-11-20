# Evaluation plan: how to disprove or validate value

**No benchmark results yet:** the current offline unit tests check strictness of message parsing and simulated acknowledgments, not communication performance or actual cross-model comprehension.

## Baselines

- A2A 1.0 structured message without AEON-Link tags.
- A2A 1.0 structured message with AEON-Link claims/evidence/constraints.
- Plain JSON prompt with equivalent information and no AEON-Link-specific protocol.

## Controlled measurements

1. **Correct interpretation** of goals, facts/hypotheses, constraints (human-defined reference cases and blind reviewers).
2. **Safety violations**, including permission errors, hallucinated evidence, and assertion promotion.
3. **Data transferred** (bytes and model tokens) per correctly completed task.
4. **End-to-end latency and total monetary cost** for equal problem difficulty and budget.
5. **Schema acceptance** across independent Python / TypeScript / Rust implementations.
6. **Retransmissions and recoveries** with malformed, unsupported and stale inputs.

## Protocol

Use a pre-registered test set of >=100 independent tasks, 3 or more provider/model families if accessible, replicated trials, and fixed model versions / prompts / temperature where available. Use A/B randomization, confidence intervals, and publish failures. If AEON-Link does not outperform the baselines, report it clearly rather than claiming universal superiority.


## Reproducible scorer added in v0.4

The local `aeon_link.benchmark.score_records` API accepts recorded cases for two or more methods, requires **identical case IDs and ground truth across methods**, counts explicit errors as failures, and reports Wilson 95% accuracy intervals, mean latencies and token counts. It does not collect model outputs or contain measured superiority data. Try `python examples/benchmark_sample.py`; its rows are explicitly **synthetic** and must not be cited as empirical performance.
