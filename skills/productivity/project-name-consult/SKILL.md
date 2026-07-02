---
name: project-name-consult
description: "Consult Kimi K2.7 Code and MiMo v2.5 Pro for a domain-accurate, professional project name during project-build-loop bootstrap. Use when the user gives a rough project description and needs a clean title, slug, and category that captures the right technical concepts (Kimi), reads well for a portfolio (MiMo), and benefits from conductor-led synthesis. Runs both models sealed and bounded via the tuned OpenCode wrapper exposed by agent-orchestra, then the conductor independently selects, rewrites, or creates the final ranked shortlist. Do not trigger for naming skills (use name-skill), for renaming variables (use naming-analyzer), or outside a project-build-loop context."
# --- provenance ---
category: productivity
source: self-authored; part of the project orchestra (docs/plans/project-orchestra-plan.md)
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-27
---

# Project Name Consult

Get a proper project name by routing through two specialist models:

- **Kimi K2.7 Code** (technical lane): does the name capture the right domain
  concepts, protocols, tools, and archetype? Is it technically accurate and
  unambiguous to a practitioner?
- **MiMo v2.5 Pro** (prose lane): is the name clean, professional, readable,
  and discoverable for a portfolio? Does it avoid jargon overload while staying
  specific?

Both run **sealed and timeout-bounded** via the tuned `agent-orchestra` OpenCode wrapper
(no repo access, advisory only). The conductor treats their output as raw signal,
adds its own naming judgment, and presents a refined ranked shortlist: title,
slug, category, and the recommended pick.

## When to use

Called by `project-build-loop` during **Phase 1 (intake)** after the user gives a
rough project description but before the bootstrap writes anything. Can also be
invoked standalone when naming or renaming a project.

## Workflow

1. **Collect context.** The user's project description, intended archetype, key
   technologies/protocols, and environment (e.g. EVE-NG, cloud, app).
2. **Build two prompts** from the context — one per lane. Each receives the same
   description; the technical prompt asks for domain accuracy, the prose prompt
   asks for clarity and portfolio readability.
3. **Run sequentially** (opencode shares one SQLite DB). Both sealed, both
   bounded at 120s (naming is a lightweight call).
4. **Synthesize as conductor.** Treat both model outputs as advisory ingredients,
   not ballot results. Identify the real engineering story in the project
   description, then select, rewrite, combine, or create names that better carry
   that story. The conductor may introduce names absent from both consults when
   they are more accurate, cleaner, or more useful for the project path.
5. **Apply naming judgment.** Prefer names that foreground the durable technical
   capability over implementation trivia. Use precise domain terms when they
   clarify the work, but avoid pathologically long slugs, alarmist wording, and
   unexplained jargon. For portfolio-facing projects, favor names that make a
   hiring manager understand the value while still satisfying a practitioner.
6. **Present a refined shortlist** (3 to 5 options): title, inferred slug (the
   bootstrap's `slugify` output), recommended category, and a single conductor
   recommendation with brief reasoning. The user picks or edits; the conductor
   proceeds with the confirmed name.

## Invocation

```text
# Technical naming (Kimi) — domain accuracy
agent-orchestra/scripts/consult-opencode.sh --sealed --timeout 120 \
  --model openrouter/moonshotai/kimi-k2.7-code -- "<naming prompt>"

# Prose naming (MiMo) — readability and portfolio fit
agent-orchestra/scripts/consult-opencode.sh --sealed --timeout 120 \
  --model openrouter/xiaomi/mimo-v2.5-pro -- "<naming prompt>"
```

## Prompt template

```text
You are naming a cybersecurity/networking lab project for a professional
portfolio. Given the description below, suggest exactly 3 project titles ranked
by fit. For each, give: the title, the kebab-case slug, and the recommended
category (networking-and-cybersecurity or software-development). Be specific to
the actual work — not generic. Output only the 3 suggestions, no commentary.

Description: <user's rough description>
Technologies: <key tools/protocols mentioned>
Environment: <EVE-NG / cloud / local / production>
Archetype hint: <if known>
```

The technical prompt adds: "Ensure the title uses correct protocol names, tool
names, and domain terminology. Flag any technically inaccurate or ambiguous
phrasing."

The prose prompt adds: "Ensure the title reads well on a portfolio page — clean,
professional, specific but not jargon-heavy. Flag anything that would confuse a
non-specialist hiring manager scanning the portfolio."

## Safety

- No secrets or real infrastructure names in the naming prompt.
- Advisory only; the conductor picks the final name. Models never write to disk.
- Graceful skip: if the wrapper or models are unavailable, the conductor falls
  back to its own inference (as it does today).
