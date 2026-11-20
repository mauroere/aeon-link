# ÆON-Link — experimental semantics for AI-agent communication

**SDK 0.6.0 · Wire protocol 0.4.0 · MIT · pre-alpha**

[Español](README.es.md) · [Specification](docs/SPEC.md) · [Security](SECURITY.md) · [Independent review & adoption status](docs/INDEPENDENT_REVIEW_AND_ADOPTION.md) · [Changelog](CHANGELOG.md)

ÆON-Link is an **optional semantic payload format**, intended to complement—not replace—A2A, MCP, HTTP, OAuth or official model APIs. It represents objectives, restrictions, epistemic status and evidence references, and provides bounded deterministic checks. It is **not** an adopted standard; tests do not establish universal semantic understanding, source truth, or superiority over established protocols.

## What exists in 0.6

- Python SDK and Node.js implementation of a restricted, reproducible JSON profile, schema checks, version/ontology/capability handshake, and signed-message validation.
- Optional HMAC-SHA256 signatures bound to pre-provisioned sender identity, expiry, local authorization checks and SQLite replay detection. This does **not** replace transport security, key management or host-side execution policy.
- Executable semantic contracts, counterfactual / invariance probes, decision receipts and evidence-reference graphs. These only assess defined behaviors, not intrinsic model understanding or the truth of claims.
- Minimal **payload mappings** for A2A data parts and MCP tool results; not full network protocol servers.
- Three **optional** commercial provider HTTP clients: OpenAI Responses, Anthropic Messages and Gemini generateContent, isolated from tool execution.
- Opt-in paid live experiments: paired plain-JSON-vs-semantic-payload tests and a restricted task relay from model A to model B. **No live commercial provider calls were made in preparing this release:** tests mock their responses.
- Python/Node automated tests, CodeQL security-extended workflow, Dependabot, security-reporting guidance and an [external-assessor request](.github/ISSUE_TEMPLATE/security-external-review.md).

## Install and verify

Python 3.10+ and Node.js 22+ for cross-runtime tests:

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
node --test js/*.test.mjs js/test.mjs
```

If the environment is offline but `jsonschema` is installed, from the repository root use `PYTHONPATH=src python -m unittest discover -s tests -v` instead of an editable installation.

Run the reference examples:

```sh
python examples/demo.py
python examples/semantic_demo.py
python examples/benchmark_sample.py     # synthetic data, not real model results
```

See [the semantic conformance profile](docs/SEMANTIC_CONFORMANCE.md), [authenticated inbound gate](docs/INBOUND_SECURITY.md), [decision receipts](docs/DECISION_RECEIPTS.md) and [benchmark methodology](docs/BENCHMARKS.md).

## Optional live model experiments

These calls may incur provider charges. Set API keys through environment variables or a secret manager: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`. **Never put secrets in commits or issue reports.** Models must be available to your account.

```sh
python examples/live_provider_benchmark.py --provider openai --model <MODEL_ID> --limit 12 --i-accept-api-costs
python examples/live_model_relay.py --provider-a openai --model-a <MODEL_ID_A> --provider-b anthropic --model-b <MODEL_ID_B> --action write --i-accept-api-costs
```

The relay does **not** execute the action being evaluated. The benchmark checks paired *payload formats* under the same model, rather than claiming that AEON-Link competes with A2A or MCP as a transport. Its starter dataset is only 36 deterministic cases—too small and too synthetic to demonstrate universal superiority.

## Security and independent assessment

Treat all model-generated text and external evidence as untrusted. The SDK is **not an execution sandbox**. Signed content alone does not grant privileges. Production deployments need end-to-end HTTPS/TLS, trustworthy peer registration, key rotation, rate limits, a durable coordinated replay store and host-side idempotency.

GitHub CodeQL provides **third-party automated static scanning**, not an independent human security audit. A qualified external reviewer has not yet completed an assessment, and no adoption as a universal standard has been demonstrated. See the [status ledger](docs/INDEPENDENT_REVIEW_AND_ADOPTION.md) and [private disclosure policy](SECURITY.md).

## Research questions

The next measured questions are whether semantic payloads reduce interpretation errors on independently graded, preregistered tasks; whether they increase token or latency costs; and whether independent implementations agree on edge cases. Publish both improvements and regressions without conflating structured data exchange with model comprehension.

## References

- [A2A 1.0](https://a2a-protocol.org/v1.0.0/specification/)
- [MCP 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28)
- [OpenAI Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create)
- [Anthropic Messages API](https://platform.claude.com/docs/en/api/messages)
- [Gemini generateContent](https://ai.google.dev/api/generate-content)
- [GitHub CodeQL](https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-code-scanning)