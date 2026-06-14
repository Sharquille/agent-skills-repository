---
name: security-scan
description: "Scan your Claude Code configuration (.claude/ directory) for security vulnerabilities, misconfigurations, and injection risks using AgentShield."
category: engineering
source: https://skillrepo.dev/skills/affaan-m/security-scan
author: Affaan Mustafa
license: MIT
retrieved: 2026-06-14
---

# Security Scan

Audit your Claude Code configuration directories for security issues, prompt-injection surfaces, and misconfigurations using AgentShield.

## When to Use

- Setting up a new Claude Code project or onboarding to a new repository.
- After modifying `.claude/settings.json`, `CLAUDE.md`, or MCP server configurations.
- Prior to committing local configurations to public repositories.
- Periodic security hygiene audits of local agent capabilities and configurations.

## When NOT to Use

- Standard web application source-code security hardening → use [[security-and-hardening]] instead.
- Scanning network-layer configurations (BGP summary analysis, loopback routing states) → use [[network-bgp-diagnostics]] instead.
- Troubleshooting physical switch interfaces, duplex auto-negotiations, or cable diagnostics → use [[network-interface-health]] instead.

---

## Scan Directory Framework

AgentShield scans these key files for specific vulnerabilities:

| Target File | Scanned Parameters / Vulnerabilities |
|---|---|
| **`CLAUDE.md`** | Hardcoded secrets, auto-run commands, hidden instructions, prompt injection patterns. |
| **`settings.json`** | Overly permissive allow lists, missing deny lists, dangerous system bypass flags. |
| **`mcp.json`** | Unsecured MCP servers, hardcoded environment credentials, `npx` supply-chain vulnerabilities. |
| **`hooks/`** | Command injection via shell interpolation, unmonitored data exfiltration, silent error suppressions. |
| **`agents/*.md`** | Unrestricted tool access, prompt injection boundaries, missing model specifications. |

---

## Prerequisites & Installation

AgentShield must be installed. Check and install if needed:

```bash
# Check if installed
npx ecc-agentshield --version

# Install globally (recommended)
npm install -g ecc-agentshield

# Or run directly via npx (no install needed)
npx ecc-agentshield scan .
```

---

## Usage Examples

### 1. Basic Configurations Scan
Run against the current project's `.claude/` directory:

```bash
# Scan current project
npx ecc-agentshield scan

# Scan a specific path
npx ecc-agentshield scan --path /path/to/.claude

# Scan with minimum severity filter
npx ecc-agentshield scan --min-severity medium
```

### 2. Output Format Configurations

```bash
# Terminal output (default) — colored report with grade
npx ecc-agentshield scan

# JSON — for CI/CD integration
npx ecc-agentshield scan --format json

# Markdown — for documentation
npx ecc-agentshield scan --format markdown

# HTML — self-contained dark-theme report
npx ecc-agentshield scan --format html > security-report.html
```

### 3. Automated Remediations
Apply safe, auto-fixable security remediations automatically:

```bash
npx ecc-agentshield scan --fix
```
*What it does:*
- Replaces hardcoded credentials with environment variables references.
- Tightens wildcards or permissive scopes to explicit boundaries.
- Ignores manual-only configurations requiring developer oversight.

### 4. Deep Adversarial Analysis (Opus 4.6)
Execute the adversarial three-agent pipeline for deeper analysis (requires API key):

```bash
export ANTHROPIC_API_KEY=your-key
npx ecc-agentshield scan --opus --stream
```
*This triggers:*
1. **Attacker (Red Team):** Discovers novel prompt-injection and hook-escape vectors.
2. **Defender (Blue Team):** Suggests targeted, precise hardening rules.
3. **Auditor:** Synthesizes the results into a final security verdict.

### 5. Initialize Secure Baseline
Scaffold a secure, default-hardened `.claude/` configurations profile from scratch:

```bash
npx ecc-agentshield init
```

---

## Severity Scale & Grades

AgentShield scores your configurations on a scale from `A` to `F`:

| Grade | Score | Security Posture |
|---|---|---|
| **A** | 90-100 | Secure configuration (Best Practice) |
| **B** | 75-89 | Minor issues (Needs minor hardening) |
| **C** | 60-74 | Needs attention (Permissive rules detected) |
| **D** | 40-59 | Significant risks (Potential injection vectors) |
| **F** | 0-39 | Critical vulnerabilities (Action needed immediately) |

---

## Findings Triage Reference

### Critical Findings (Remediate Immediately)
- Hardcoded API credentials, private keys, or tokens in config files.
- `Bash(*)` in the tool allow list (unrestricted shell execution boundaries).
- Command injection in git hooks via unsanitized `${file}` string interpolation.
- Running unverified or unpinned third-party MCP servers.

### High Findings (Remediate Before Committing)
- Auto-run instructions in `CLAUDE.md` (promotes unconsented prompt executions).
- Missing deny lists inside permissions.
- Custom subagents granted unrestricted terminal access.

### Medium Findings (Recommended Hardening)
- Silent error suppression in custom hooks (e.g., `2>/dev/null` or `|| true` bypasses).
- Missing `PreToolUse` security hooks in settings.
- `npx -y` dynamic auto-installers in MCP server configurations.

## See Also

- Skill: [[security-and-hardening]] (for secure coding boundaries)
- Skill: [[security-best-practices]] (for language audits)
- Skill: [[audit-repo-for-agents]] (for workspace integrity checking)
