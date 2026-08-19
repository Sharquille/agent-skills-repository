---
name: anti-slop-standard
description: "Authoring-time code standard: write it once, write only what is reached, write the direct thing, put it where it belongs, lock behavior with tests, and apply the handover check before presenting work as done. In force by default for code authoring and handover. Use ai-slop-cleaner for cleanup of existing code and humanizer for a deep rewrite of finished prose; unslop owns prose authoring."
# --- provenance ---
category: engineering
source: self-authored (this repository)
author: Sharquille Andrew
license: MIT
retrieved: 2026-08-19
---

# Anti-Slop Standard

**Slop** is output that looks like work and isn't. It survives a glance and fails a
read: code that runs but carries layers nothing needs, prose that fills a screen and
answers nothing. Slop is not a style preference — it is a defect class, and it is
cheapest to prevent at the moment of writing.

This standard governs authoring. [`ai-slop-cleaner`](../ai-slop-cleaner/SKILL.md) and
[`humanizer`](../../productivity/humanizer/SKILL.md) remediate what already shipped;
they are the expensive path. Writing to this standard is the cheap one.

## Standing rule

This standard governs authoring and handover. It is in force by default, but it does
not override user instructions, required legal or security wording, technical
precision, or established repository conventions.

`anti-slop-standard` owns code authoring, scope discipline, and the handover check.
`unslop` owns the light prose pass. `humanizer` is an explicit deep-rewrite workflow,
not a second always-on authority.

It applies to what you write and to what you accept from a delegated lane (Codex,
OpenCode, or any subagent) before you fold that work into a deliverable. A
consultant's output is a draft, and it meets this bar before it lands.

## Writing code

**Write it once.** Search for the existing helper, type, or pattern before adding one.
A second implementation of something the repo already does is slop even when both
copies work. *Test: could this call something that already exists?*

**Write only what is reached.** Every branch, parameter, option, and export exists
because something reaches it today. No speculative generality, no configuration for a
case nobody asked for, no `TODO` scaffolding for imagined futures. *Test: what calls
this? If the answer is "nothing yet", delete it.*

**Write the direct thing.** A function that forwards to one other function, a class
wrapping a single call, an interface with one implementation and no second in sight —
each adds a hop and hides the real work. Indirection earns its place by absorbing
complexity, not by relocating it. *Test: does removing this layer lose anything but
the layer?*

**Write it where it belongs.** Put logic at the layer that owns the concern. Data
access does not reach into rendering, transport does not know business rules, and a
utility file is not a home for logic that has one caller. *Test: does this file's name
still describe everything inside it?*

**Lock behavior as you write it.** New behavior arrives with the test that pins it, in
the same change. A test asserting that a mock was called is not coverage — assert the
observable outcome. *Test: would this test fail if the feature broke?*

**Match the surrounding code.** Comment density, naming, error handling, and idiom
follow the file you are editing, not your defaults. A change should be hard to pick
out of a blame view by style alone.

**Comment the why.** Explain the non-obvious decision, the constraint, the gotcha the
code cannot state. A comment that restates the line below it is slop with a `//` in
front.

## Writing prose

[`unslop`](../../productivity/unslop/SKILL.md) is the always-on, preservation-first
prose authority. Apply it to prose you author without mechanically rewriting technical
terms or unchanged sentences.

Use [`technical-writing`](../../productivity/technical-writing/SKILL.md) for document
mode, structure, sentence load, and ambiguity. Use
[`portable-markdown`](../../productivity/portable-markdown/SKILL.md) for Markdown
portability. Use [`humanizer`](../../productivity/humanizer/SKILL.md) only when the
user asks for a deliberate deep rewrite of finished prose.

Domain precision and required wording take precedence over stylistic cleanup.

## The handover check

Before presenting work as done, run these against the actual diff or draft:

1. **Reach** — does everything I added have a caller, a reader, or a test?
2. **Once** — did I add a second way to do something the repo already does?
3. **Evidence** — is every claim in my summary something I verified, and is every
   skipped or failed step named?
4. **Specific** — could a reader act on my summary without opening the diff?
5. **Trim** — what can I delete with nothing lost?

A "no" on any of these is a fix before handover, not a caveat in the summary.

## Scope discipline

Slop also enters as work nobody asked for. Fix what was asked; when you spot adjacent
problems, name them and let the user choose. An unrequested refactor bundled into a
requested fix makes the real change unreviewable, however good the refactor is.

## When this yields

- **Generated or vendored code** — leave it as the generator emits it.
- **Established repo conventions** — a repo-wide pattern beats this document; match it
  and say so if it looks like a mistake.
- **Deliberate scaffolding** — a spike, a throwaway prototype, or a teaching example
  may carry structure that production code should not. Say which it is.
- **Domain and legal register** — compliance, security, and academic writing have
  required phrasing. Precision wins over plainness there.

## Remediation

| Situation | Reach for |
|---|---|
| Any prose, at authoring time | [`unslop`](../../productivity/unslop/SKILL.md) |
| Existing code is bloated, duplicated, over-abstracted | [`ai-slop-cleaner`](../ai-slop-cleaner/SKILL.md) |
| Finished prose needs a voice-matched rewrite | [`humanizer`](../../productivity/humanizer/SKILL.md) |
| A doc's structure, mode, or sentence load is wrong | [`technical-writing`](../../productivity/technical-writing/SKILL.md) |
| A skill or agent doc needs tightening | [`writing-for-agents`](../../productivity/writing-for-agents/SKILL.md) |
| UI looks templated or unconsidered | [`baseline-ui`](../../design/baseline-ui/SKILL.md) |
