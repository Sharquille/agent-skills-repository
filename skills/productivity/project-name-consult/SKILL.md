---
name: project-name-consult
description: "Generate a domain-accurate, professional project name during project-build-loop bootstrap using the current harness, bounded web research, and conductor synthesis. Use when the user gives a rough project description and needs a clean title, slug, and category. External model wrappers are optional and never a prerequisite. Do not trigger for naming skills (use name-skill), for renaming variables (use naming-analyzer), or outside a project-build-loop context."
# --- provenance ---
category: productivity
source: self-authored; part of the project orchestra (docs/plans/project-orchestra-plan.md)
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-27
---

# Project Name Consult

Get a proper project name by combining bounded native-harness advice, targeted
research, and conductor judgment:

- **Technical lane:** checks domain concepts, protocols, tools, and archetype
  accuracy.
- **Security lane:** checks trust-boundary, defensive, least-privilege, and
  audit terminology.
- **Portfolio lane:** checks readability, discoverability, and repository fit.
- **Research lane:** runs five bounded searches for adjacent terminology and
  naming patterns. Search results are vocabulary input, not authority for the
  final name.

Native-harness agents are advisory, bounded, and must not write project files.
The conductor treats their output and search results as raw signal, adds its own
naming judgment, and presents a refined ranked shortlist: title, slug, category,
and the recommended pick. If native agents or web search are unavailable, the
conductor proceeds with local inference rather than blocking bootstrap.

## When to use

Called by `project-build-loop` during **Phase 1 (intake)** after the user gives a
rough project description but before the bootstrap writes anything. Can also be
invoked standalone when naming or renaming a project.

## Workflow

1. **Collect context.** The user's project description, intended archetype, key
   technologies/protocols, and environment (e.g. EVE-NG, cloud, app).
2. **Build bounded prompts** from the context for the technical, security, and
   portfolio lanes. Each receives the same sanitized description.
3. **Run native-harness lanes** when available, then make five focused web search
   calls. Suggested search themes are: the project's core capability, adjacent
   operations terminology, security/trust-boundary language, audit/provenance
   language, and homelab or portfolio naming patterns. Do not include secrets,
   real infrastructure names, addresses, credentials, or private URLs.
4. **Synthesize as conductor.** Treat agent outputs and search results as advisory ingredients,
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

Use the current harness's bounded agent tool for the technical, security, and
portfolio lanes. Run five separate web searches with sanitized, project-specific
queries. Do not require OpenCode, a provider wrapper, or a plugin. Keep all lanes
read-only and pass only the project description and non-sensitive terminology.

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
- Graceful skip: if native agents or web search are unavailable, the conductor
  falls back to its own inference and records the missing advisory lanes.
- No external wrapper is a lifecycle prerequisite. A naming failure must not
  block a safe, local bootstrap when the user confirms a title.
