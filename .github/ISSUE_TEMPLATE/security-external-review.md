---
name: Independent security review request
description: Coordinate an external, qualified security review (do not post vulnerabilities publicly)
title: 'Security review: scope and independent assessor'
labels: [security, external-review]
---

## Scope
Review AEON-Link Python/Node SDK, canonical JSON handling, signed envelopes, key binding, replay protection, authorization boundary, test/CI supply chain, and semantic receipts. Relevant threat models: forged identity, replay, confused deputy, parser differential, denial of service, dependency attacks, malicious tool outputs.

## Independence
Please identify assessor, affiliation, conflicts, exact commit, methods, findings severity, reproducible evidence, remediation and retest. Automated CodeQL scans are **not** a substitute for this review.

**Report vulnerabilities privately** using GitHub private vulnerability reporting/security advisories where available, rather than public issues.
