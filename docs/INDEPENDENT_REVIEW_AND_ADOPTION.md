# External review, live interoperability and adoption — status ledger

**Last edited:** 2026-11-20 | **Release:** SDK 0.6.0, wire envelope 0.4.0

| Goal | State | Evidence needed to close |
| --- | --- | --- |
| Independent security audit | **OPEN** | Named independent human assessor, signed assessment, finding triage, fix verification |
| Third-party automated static analysis | **CONFIGURED** | Completed GitHub CodeQL scan and reviewed alerts for both Python and JavaScript |
| Commercial IA-to-IA communication | **INTEGRATION CODE WRITTEN / LIVE NOT RUN** | Authorized API keys, executed multi-vendor tasks with recorded request identifiers and validated outputs |
| Demonstrated superiority | **NOT PROVEN** | Pre-registered tasks, comparable payload and model settings, independent grading, paired statistical analysis and replication |
| Universal adoption | **NOT ACHIEVED** | Independent maintainers and implementations, open governance, standardization and adoption evidence |

## Security audit engagement

The repository includes a GitHub issue template specifying review scope. CodeQL is a **third-party automated scan**, not a replacement for an independent human security assessment. Finding no alerts cannot establish absence of vulnerabilities. Review should cover canonicalization, replay concurrency, auth/key lifecycle, unsafe API redirects, denial of service, trust decisions, prompt injection threats, CI dependencies, supply chain and unsafe examples. Vulnerabilities must be privately disclosed; public issues contain only scoping requests.

## Real-model experiment

Three **optional** HTTP adapters are supplied for OpenAI Responses, Anthropic Messages and Gemini generateContent. They do not run unless a user supplies credentials and invokes the explicit command. The adapters are isolated from agent tool execution. No API responses or keys are persisted by the harness, except **status, model identifier, token counts when returned, and latency**. Do not run on sensitive customer data. API calls can cost money.

    OPENAI_API_KEY=... python examples/live_provider_benchmark.py --provider openai --model <MODEL_ID> --limit 12 --i-accept-api-costs
    ANTHROPIC_API_KEY=... python examples/live_provider_benchmark.py --provider anthropic --model <MODEL_ID> --limit 12 --i-accept-api-costs
    GEMINI_API_KEY=... python examples/live_provider_benchmark.py --provider gemini --model <MODEL_ID> --limit 12 --i-accept-api-costs

`<MODEL_ID>` must be an existing model available to that account. Pass credentials through your secret manager/environment; **never paste them in an issue, commit, or chat**. The live script makes 2 calls per case to a single provider, using a 36-case deterministic task generator. Its report explicitly does **not** establish a vendor-independent advantage. For future research use at least 100 preregistered independent tasks (this starter suite is too small), multiple models, blinded judgments, repeated trials and statistical uncertainty reporting.

## Meaningful protocol comparison

A2A and MCP are transport/interoperability protocols and AEON-Link is a semantic *payload layer*. Comparing them as if they were alternatives is a category error. Instead assess **A2A without** versus **A2A with** AEON-Link payloads, and/or plain tool-result JSON versus equivalent enriched payloads over MCP. Keep transport, base model, tool access, task, and budget constant. This repository's paired harness examines only the payload-prompt axis, **not full A2A or MCP interoperability**.

## Adoption without fabricated claims

Steps available to third parties: fork, run CI, open implementation issues, propose extensions, supply independent security reviews, test separate-language clients, and evaluate the protocol with an independent benchmark. None have been asserted to have happened. Publication in a public repo does not mean standardization or worldwide adoption.

Sources:
- A2A 1.0: https://a2a-protocol.org/v1.0.0/specification/
- MCP 2026-07-28: https://modelcontextprotocol.io/specification/2026-07-28
- GitHub CodeQL: https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-code-scanning
- API references: https://developers.openai.com/api/reference/resources/responses/methods/create , https://platform.claude.com/docs/en/api/messages , https://ai.google.dev/api/generate-content
