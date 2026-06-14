---
name: build-security-policy
description: "Draft a concise, enforceable security policy for an application that handles sensitive data (PII, PHI, financial, secrets, regulated content). Produces a single normative document — threat model, data classification, trust boundaries, authn/session and secrets policy, logging/audit, retention/deletion, and an incident-response runbook — using RFC 2119 MUST/SHOULD/MAY language. Use when a user needs a security policy, security baseline, threat model write-up, data-handling rules, or a go/no-go security checklist for an app. Do not trigger for general code review or non-security documentation."
# --- provenance ---
category: engineering
source: self-authored (this repository)
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-13
# concept note: inspired by the general idea of a normative app "security policy book";
# written from scratch grounded in public standards (OWASP ASVS, NIST CSF/800-53,
# RFC 2119) — no third-party text reused.
---

# Build Security Policy

Produce one short, real, enforceable security policy for an application that
handles sensitive data — not a generic checklist. Every requirement is testable
and uses normative language so a reviewer can mark it pass/fail. Grounded in
public frameworks: OWASP ASVS (verification requirements), NIST CSF (functions),
and RFC 2119 (MUST/SHOULD/MAY).

## Normative language (RFC 2119)

- **MUST / MUST NOT** — hard requirement; violation is a release blocker.
- **SHOULD / SHOULD NOT** — strong default; deviations need a written, approved reason.
- **MAY** — optional/permitted.

Prefer MUST for anything protecting confidentiality, integrity, or regulated data.
If a control is required but unavailable, **fail closed** and call it out explicitly.

## Workflow

### 1) Gather scope (ask only what's missing)
Ask up to ~6 short questions, then proceed with safe defaults marked `TODO` for
anything unanswered:
- **Data classes** handled? (PII, PHI, financial/PCI, auth secrets, user content)
- **Trust boundaries** — client, server, third parties, internal services?
- **Identity** — how do users authenticate? (OAuth/OIDC, SSO/SAML, password, device sessions)
- **Storage** — databases, object storage, logs, analytics, caches?
- **Third parties / connectors** — what data leaves the system, to whom?
- **Retention & deletion** — defaults plus user-initiated deletion expectations?

### 2) Draft the policy
Load `references/policy-template.md` and fill each section. Keep it concise and
deterministic — a developer should be able to implement directly from it. Replace
unknowns with `TODO:` plus an explicit assumption, never a guess presented as fact.

### 3) Map to a recognized framework
Tag the most safety-critical requirements with their control family so the policy
is auditable:
- **NIST CSF function**: Identify / Protect / Detect / Respond / Recover
- **OWASP ASVS chapter** where relevant (e.g. V2 Authentication, V3 Session, V7 Logging, V8 Data Protection)

This makes the policy defensible to an auditor and easy to extend.

### 4) Enforce guardrails
- **Never** embed real secrets, tokens, keys, or credentials in the document.
- **Least scope** — document only what the app needs; do not invent features or controls.
- **Fail closed** — if a required capability is missing, state it as a blocking gap.
- Keep every requirement **testable** — if you can't write a pass/fail check for it, rewrite it.

### 5) Quality gate
Confirm the policy contains all of:
- [ ] Threat model — assumptions, in-scope, explicitly out-of-scope
- [ ] Data classification table + handling rule per class
- [ ] Trust boundaries + the control at each boundary
- [ ] Authentication & session policy
- [ ] Authorization model (least privilege, role/attribute basis)
- [ ] Secrets & token handling (storage, rotation, exposure rules)
- [ ] Logging & audit policy (what's logged, what's NEVER logged, retention)
- [ ] Data retention & deletion (default + user-initiated)
- [ ] Incident-response mini-runbook (detect → contain → eradicate → recover → review)
- [ ] Security gates / go-no-go release checklist
- [ ] Open `TODO`s and assumptions listed at the top

## Output
Write the policy to `SECURITY_POLICY.md` (or a path the user specifies). Lead with
a one-paragraph scope statement and the open `TODO`/assumptions list, then the
sections above. Close by summarizing the blocking gaps (any unmet MUST) so the
reader knows the current go/no-go status.
