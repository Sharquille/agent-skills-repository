# Skills Registry

A personal registry of Claude Code skills collected from the internet and other sources.

## How to add a skill
1. Download the raw files into a quarantine dir (e.g. `/tmp/skill-audit`) — literal bytes, not a paraphrasing fetch.
2. **Audit before installing:** `skills/engineering/vet-skill/scripts/audit.sh /tmp/skill-audit` and eyeball every match.
3. On a clean verdict, copy the audited bytes into `skills/<category>/<skill-name>/` and add the provenance header (see `skills/_template/`).
4. Keep any `LICENSE` file for attribution, then `diff -r` quarantine vs. installed to prove no drift.
5. Add an entry to the table below and delete the quarantine dir.

---

## Skills

| Skill | Category | Author | Source | License | Added |
|-------|----------|--------|--------|---------|-------|
| [name-skill](skills/engineering/name-skill/) | engineering | agent-skills-repository (self-authored) | this repo | same-as-repo | 2026-06-13 |
| [vet-skill](skills/engineering/vet-skill/) | engineering | agent-skills-repository (self-authored) | this repo | same-as-repo | 2026-06-13 |
| [security-threat-model](skills/engineering/security-threat-model/) | engineering | OpenAI (openai/skills) | [github.com/openai/skills](https://github.com/openai/skills/tree/main/skills/.curated/security-threat-model) | Apache-2.0 | 2026-06-13 |
