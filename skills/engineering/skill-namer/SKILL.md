---
name: skill-namer
description: "Propose the most intuitive, discoverable name for a skill based on what it actually does, and check the name is not already taken. Trigger when importing a skill whose name is cryptic, vendor-specific, or non-obvious, when renaming an existing skill, or when the user asks what to call a skill. Produces a recommended kebab-case name plus alternatives, and the exact rename steps (directory, frontmatter name, REGISTRY entry). Do not trigger for naming variables, files, or anything that is not a Claude skill."
# --- provenance ---
category: engineering
source: self-authored (this repository)
author: agent-skills-repository
license: same-as-repo
retrieved: 2026-06-13
---

# Skill Namer

A skill's `name:` is its entire discovery surface: it is what the user types as
`/name` and a strong signal the model uses to decide when to trigger. A cryptic,
vendor-prefixed, or codenamed skill is effectively invisible no matter how good
its body is. Rename on import so the name describes the job, not its origin.

## What makes a name intuitive

A good skill name passes the **"could someone guess this exists?"** test — if a
user wanted this capability, would they reach for this word?

Rules, in priority order:
1. **kebab-case, lowercase** — `pdf-form-filler`, not `PDFFormFiller` or `pdf_form_filler`.
2. **Describe the job, not the source** — drop vendor/author prefixes and internal
   codenames (`acme-x7-helper` → `changelog-writer`).
3. **Lead with the domain or the verb** — `<domain>-<action>` (`invoice-parser`)
   or `<action>-<object>` (`summarize-pr`). Pick whichever a user would say aloud.
4. **Concrete over clever** — no puns, no abstractions. `commit-message-writer`
   beats `git-whisperer`.
5. **2–4 words, ~30 chars max** — long enough to be unambiguous, short to type.
6. **Match the directory name** — the folder under `skills/<category>/` should
   equal the frontmatter `name`. Keep them in sync.
7. **Disambiguate from neighbors** — if a similar skill exists, the name must make
   the difference obvious (`threat-model-repo` vs `threat-model-design-doc`).

Anti-patterns: bare nouns that could mean anything (`helper`, `tools`, `assistant`),
the word "skill" inside the name (it's already a skill), and acronyms a newcomer
would not expand.

## Workflow

### 1) Understand what the skill does
Read its `description` and body. Write one plain sentence: *"This skill <verb>
<object> [for <who/when>]."* That sentence is the raw material for the name.

### 2) Generate 3–5 candidates
Produce candidates that satisfy the rules above. Cover both framings
(`<domain>-<action>` and `<action>-<object>`) so the user can pick the phrasing
that matches how they'd ask for it.

### 3) Check for collisions
Grep the registry so the new name doesn't duplicate or clash with an existing one:
```text
grep -i "<candidate>" REGISTRY.md
```
Also scan sibling folders under `skills/`. If taken, either the skills are
duplicates (don't install) or both names need a disambiguating qualifier.

### 4) Recommend one + alternatives
Lead with a single recommendation and one sentence on why. List the runners-up so
the user can override. Defer to the user's wording if they have a preference.

### 5) Apply the rename (on approval)
Keep all three in sync, or the skill won't load cleanly:
- Rename the directory: `skills/<category>/<old>/` → `.../<new>/`
- Update `name:` in `SKILL.md` frontmatter to match.
- Update the row in `REGISTRY.md` (and any cross-links).
Leave a note of the original upstream name in the provenance `source:` so the
lineage back to where you found it is never lost.
