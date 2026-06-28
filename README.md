# Agent Skills Repository

A curated, secure-by-default registry of high-signal skills for AI agents like **Claude Code**, **Claude Desktop**, **Gemini CLI**, **Codex**, and **OpenCode**.

This repository serves as a personal collection of self-authored and audited third-party skills, providing a central place to manage, version, and deploy advanced capabilities to your local coding assistants.

## 🚀 Getting Started

### Quick Install
Install repo-backed skills for Claude, Gemini, Codex, and OpenCode, then install the tracked safety guardrails:
```bash
./install.sh
```

### Full Deployment
Run the canonical deployment script directly:
```bash
./scripts/deploy.sh
```

Useful options:

```bash
./scripts/deploy.sh --safety-only
./scripts/deploy.sh --opencode-only
./scripts/deploy.sh --skip-safety
```

See [deploy-agent-skills](skills/engineering/deploy-agent-skills/SKILL.md) for the full deployment and safety behavior.

## 📂 Repository Structure

- `skills/`: The core registry, categorized for easy discovery.
  - `design/`: UI/UX, site architecture, and visual planning.
  - `engineering/`: Security, network forensics, cloud architecture, and development workflows.
  - `productivity/`: Brainstorming, resume review, and knowledge management.
- `scripts/`: Automation for deployment and maintenance.
- `skills/engineering/deploy-agent-skills/assets/safety/`: Tracked safety templates for OpenCode, Claude, Gemini, and Codex.
- `REGISTRY.md`: The "Source of Truth" table tracking every skill, its author, and provenance.
- `NOTICE.md`: Detailed attribution and licensing information.

## 🛡️ Security & Auditing

Every third-party skill in this repository has been vetted before inclusion. We recommend using the built-in [vet-skill](skills/engineering/vet-skill/) to audit any new skills before adding them to your registry.

The repository also includes [command-risk-review](skills/engineering/command-risk-review/), a target-aware destructive command review skill. It is intended to catch cases where a command like `rm -rf` becomes dangerous because of the target path, such as `.claude`, `.agents`, `.codex`, `.gemini`, vaults, repositories, or app support data.

### How to add a new skill
1. Download the skill files to a temporary directory.
2. Run the audit: `skills/engineering/vet-skill/scripts/audit.sh /tmp/new-skill`.
3. If clean, move to the appropriate category in `skills/`.
4. Update `REGISTRY.md`.
5. Run `./scripts/deploy.sh` to update your global agent environment.

## 📜 License & Attribution

This repository uses a **mixed-licensing model**:
- Original curation, tooling, and self-authored skills are under the **MIT License**.
- Third-party skills retain their original licenses (e.g., Apache-2.0, MIT).

See [NOTICE.md](NOTICE.md) for full details and proper attribution for all contributors.
