---
name: security-bounty-hunter
description: "Hunt for exploitable, bounty-worthy security issues in repositories. Focuses on remotely reachable vulnerabilities that qualify for real reports instead of noisy local-only findings."
category: engineering
source: https://skillrepo.dev/skills/affaan-m/security-bounty-hunter
author: Affaan Mustafa
license: MIT
retrieved: 2026-06-14
---

# Security Bounty Hunter

Use this skill when the goal is practical vulnerability discovery for responsible disclosure or bug bounty submission, not a broad compliance or best-practices code review.

## When to Use

- Scanning a repository for remotely exploitable vulnerabilities.
- Preparing a Huntr, HackerOne, Bugcrowd, or similar bug bounty platform submission.
- Performing triage where the core question is "does this actually pay / can this be exploited?" rather than "is this theoretically unsafe?"

## When NOT to Use

- Conducting general network-layer audits (e.g., BGP configurations, switch interface health diagnostics).
- Setting up cloud hosting parameters or general server ops pipelines.
- Editing frontend user interface layouts, visual styling, or writing standard software unit tests.

---

## How It Works

Bias toward remotely reachable, user-controlled attack paths and throw away patterns that platforms routinely reject as informative or out of scope.

### In-Scope High-Impact Patterns
These are the kinds of issues that consistently yield valid, high-severity bounties:

| Pattern | CWE | Typical Impact |
|---|---|---|
| **SSRF (Server-Side Request Forgery)** | CWE-918 | Internal network access, cloud metadata credentials theft |
| **Auth Bypass** | CWE-287 | Unauthorized account, admin panel, or sensitive data access |
| **Deserialization & Upload RCE** | CWE-502 / CWE-434 | Remote code execution (RCE) on the server |
| **SQL Injection (SQLi)** | CWE-89 | Data exfiltration, authentication bypass, database destruction |
| **Command Injection** | CWE-78 | Complete server compromise / code execution |
| **Path Traversal** | CWE-22 | Arbitrary system file read (e.g., `/etc/passwd`) or arbitrary write |
| **Auto-triggered XSS (Stored)** | CWE-79 | Active session theft, cookie hijacking, admin compromise |

### Skip/Filter Patterns (Low Signal)
These are routinely rejected as informative, low-impact, or out-of-scope by bounty programs:
- Local-only `pickle.loads`, `torch.load`, or equivalent with no remote input path.
- `eval()` or `exec()` used in local CLI-only tooling or build scripts.
- `shell=True` on fully hardcoded command strings without user variables.
- Missing security headers (e.g., `X-Content-Type-Options`) by themselves without a companion exploit.
- Generic rate-limiting or brute-force complaints without demonstrated exploit impact.
- Self-XSS requiring the victim to copy-paste code manually into their developer console.
- CI/CD injection paths that are outside the target program's production codebase scope.
- Demonstration, example, or test-only files.

---

## Practical Triage Workflow

1. **Check Program Scope**: Always verify rules in `SECURITY.md`, the platform page (HackerOne, Bugcrowd, etc.), and listed exclusions before testing.
2. **Map Entrypoints**: Identify public HTTP handlers, file upload routes, background worker queues, webhook endpoints, file parsers, and external integrations.
3. **Execute Static Analysis**: Run targeted tools (e.g., Semgrep) as initial triage inputs only.
4. **End-to-End Analysis**: Trace user-controlled inputs sequentially from the entrypoint to the hazardous sink (database query, shell execute, file write).
5. **Confirm Exploitability**: Attempt to construct a safe, minimal, non-destructive Proof of Concept (PoC) to verify impact.
6. **Deduplicate**: Search existing advisories, CVEs, or issues to verify the bug is not already known.

### Triage Snippet (Semgrep Filter Loop)
Run static scans and manually filter out low-signal matches:
```bash
semgrep --config=auto --severity=ERROR --severity=WARNING --json
```
- **Filter checklist:**
  - [ ] Drop tests, demos, fixtures, and vendored code.
  - [ ] Drop local-only or non-reachable paths.
  - [ ] Retain only findings with a clear network-facing or user-controlled route.

---

## Report Structure

When drafting a bounty report, use this structure:

```markdown
## Description
[Clear, technical summary of what the vulnerability is and why it matters]

## Vulnerable Code
[File path, line range, and a small snippet of the vulnerable sink]

## Proof of Concept
[Minimal, self-contained working HTTP request, curl command, or exploit script]

## Impact
[Demonstrated impact of what an attacker can achieve (e.g., read private files, execute code)]

## Affected Version
[Tested version, commit hash, or active deployment target]
```

---

## Quality Gate (Self-Audit)

Before submitting any report, verify:
- [ ] The code path is reachable from a real user or network boundary.
- [ ] The input is genuinely user-controlled without strict whitelisting.
- [ ] The sink is meaningful and exploitable (RCE, Auth Bypass, SQLi, SSRF, File Read).
- [ ] The PoC is working, clean, and self-contained.
- [ ] The issue is not already covered by an open ticket, advisory, or advisory commit.
- [ ] The target host or directory is explicitly in-scope for the bounty program.

## See Also

- Skill: [[security-and-hardening]] (for secure coding patterns)
- Skill: [[security-best-practices]] (for baseline language auditing rules)
- Skill: [[security-threat-model]] (for mapping trust boundaries)
