# Security policy — experimental project

This project is pre-alpha. Do not use it as the sole authorization or sandbox boundary.

Please report exploitable vulnerabilities privately using GitHub's "Report a vulnerability" feature (if enabled), or contact repository maintainers through a secure channel. **Do not post proof-of-concept exploits, user data, or secrets in public issues.** Maintainers should acknowledge and triage reports, fix issues in a private branch, coordinate advisories and remediation, then publish a release and detailed changelog.

## Independent review

An independent human security assessment has **not yet been completed**. CodeQL is third-party automated static analysis and cannot establish absence of vulnerabilities. The project includes a scope template for independent assessors. No external assessor has endorsed this code.

## Boundary

AEON-Link provides data-format and limited authentication checks, not trust in message claims or a complete execution sandbox. Upstream endpoints must enforce TLS, peer authentication, local least-privilege authorization, quotas, transport security and idempotency.
