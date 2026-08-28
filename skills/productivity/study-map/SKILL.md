---
name: study-map
description: "Build and refresh a tiered 'study map stack' for an obsidian-study-loop vault: a Home index MOC, per-chapter maps, zoomable section sub-maps, cross-cutting concept maps with labeled edges, tag-lens maps, and an objective prerequisite map. Every node, edge, and tag is integrity-gated to something that already exists in the vault — no invented tags, no dangling links, no orphan nodes. Delegates visual rendering to mind-map-obsidian and writes only into a Maps/ folder. Use when a study vault has grown past one chapter and needs navigable, multi-level maps. Do not trigger for a single one-off mind map (use mind-map-obsidian), for non-study vaults, or to map content that does not yet exist as real notes/tags."
# --- provenance ---
category: productivity
source: self-authored (this repository)
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-20
---

# Study Map

Turn a growing `obsidian-study-loop` vault into a **navigable knowledge graph** —
not one flat mind map, but a stack of maps at different altitudes and lenses. The
goal is a well-managed brain with **no missing pieces and no fabricated ones**.

This skill plans and gates; it does not draw. Visual rendering is delegated to
[[mind-map-obsidian]] (JSON Canvas / Mermaid). Note capture stays with
[[knowledge-capture-obsidian]] and [[obsidian-study-loop]]. The calling agent
(any agent — Claude, Gemini, Codex, …) approves the result.

## Prime directive: integrity over volume

A node, edge, or tag is written **only** if it resolves to something real:

- a **node** must be an existing note (`file` node) or a concept the notes
  actually name;
- an **edge** must connect two real nodes and, for a concept map, carry a label
  that states a relationship the notes actually assert;
- a **tag** must already appear in some note's frontmatter;
- a **`[[wikilink]]`** must point to a note that already exists.

If a desired connection has no real backing, **omit it and report it as a gap to
fill** — never invent a tag, link, or node to make a map look complete. Reuse the
`obsidian-study-loop` rules rather than reinventing them: verify a wikilink target
exists before writing it (`SKILL.md:122-126`), keep a verified list of existing
note basenames and avoid orphans (`:622-626`), and use lowercase kebab-case tags
matched to the vault's existing vocabulary (`:649`).

## Map scope — what is mappable

Real ≠ mappable. The vault contains scaffolding files that are real notes but
carry no knowledge, and they must **never** appear as map nodes:

- agent pointer files — `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`
- workflow/config — `STUDY-PROTOCOL.md`, `README.md`, `LICENSE`, `MEMORY.md`
- everything under `_study/` (session logs, state) and `.obsidian/`
- any dotfile or dot-folder

**Content scope defaults to the `Notes/` folder** (plus the `Maps/` folder, since
maps may link to maps). Only notes inside the content scope are candidates for
nodes; everything else is excluded by construction. Override the scope with
`STUDY_MAP_CONTENT_ROOTS="Notes,Refs"` if real content lives elsewhere.

The integrity lint enforces this: a map node or wikilink that points at a real but
out-of-scope/scaffolding file is reported as **UNWARRANTED** (distinct from a
DANGLING reference that points at nothing). Both fail the gate.

> [!TIP]
> This also explains Obsidian's built-in **global graph view** showing
> `AGENTS`/`CLAUDE`/`STUDY-PROTOCOL` etc. — that graph renders every `.md` file
> and is separate from study-map's output. To declutter it, set the graph's
> **Files filter** to `path:Notes/` (show only study notes), or exclude the
> scaffolding: `-file:CLAUDE -file:AGENTS -file:GEMINI -file:STUDY-PROTOCOL -file:README -file:LICENSE -path:_study`.

## The map stack (each tier is vault-derived)

| Tier | Map | Derived only from |
|---|---|---|
| 1 | **Home / index MOC** | every chapter note that exists |
| 2 | **Chapter map** (Canvas) | the chapter note's `##` sections + its `related:` and links to other existing chapters |
| 3 | **Section sub-map** | a section's `###` subsections / key terms inside an existing note |
| 4 | **Concept map** (labeled edges) | relationships the notes explicitly assert (e.g. "preventive *is-a* control type") |
| 5 | **Tag-lens map** | notes grouped by a tag that already exists in frontmatter |
| 6 | **Prerequisite map** | dependencies stated in `## Study content` / learning outcomes / `related` |

Tiers 1–3 and 5 are mechanical from today's vault. Tiers 4 and 6 are built only
from propositions and prerequisites the notes actually state.

## Workflow

1. **Resolve the vault** (same rules as `obsidian-study-loop`: an `.obsidian/`,
   `STUDY-PROTOCOL.md`, or `_study/state.json` marks it). Ask if unknown.
2. **Inventory the real graph — content scope only.** List in-scope note basenames
   (default `Notes/`), the `##`/`###` headings per note, all frontmatter tags
   actually in use, every `related:` and inline `[[wikilink]]`, and any stated
   prerequisites. Exclude scaffolding (see Map scope). This is the allow-list.
3. **Plan each requested tier from the allow-list only.** Drop anything that would
   need a non-existent note/tag/relationship; collect those as a **gap report**.
4. **Render via `mind-map-obsidian`.** Use `file` nodes for real notes; labeled
   edges for concept maps; one Canvas per chapter/section/concept map; a static
   MOC `.md` (wikilink outline) for the Home index and tag-lens maps. Write only
   inside a `Maps/` folder.
5. **Run the integrity lint** (`scripts/integrity-lint.sh <vault>`): every Canvas
   `file` node and MOC `[[wikilink]]` must resolve, every edge must join two real
   nodes, every referenced tag must exist. Fix or drop any finding before
   reporting. Zero dangling references is the release gate.
6. **Report** the maps written, and the **gap report** — the missing notes/links
   that would complete the brain — so the user can fill them with real notes (via
   `obsidian-study-loop`) rather than fabricating.

## Portability

Prefer JSON Canvas (open spec), Mermaid, and static MOC notes — all portable and
consistent with `portable-markdown`. Treat Dataview-generated maps as
Obsidian-only and optional; never make a map depend on a plugin to be readable.

## Lifecycle (with obsidian-study-loop)

Refresh maps at completion milestones, not every edit: when a version 2 chapter
reaches `complete` (or a legacy chapter reaches `reviewed`), rebuild that
chapter's Canvas, refresh the Home index, and update any
concept/tag map that the chapter feeds. Maps are derived artifacts — regenerating
them must never edit `_study/` state, the session log, or note bodies.

## Optional quality pass

For a concept map, a wrong labeled edge teaches a wrong model. When accuracy
matters, route the proposed propositions through `study-consult-panel` (Kimi
verifies the relationships, MiMo tightens labels) before rendering — you remain
the gatekeeper.

## Safety and non-goals

- Writes only inside `Maps/`. Never touches `_study/`, the session log, or note
  bodies — it does not interrupt an active study session.
- Never fabricates a node, edge, or tag to fill a map; missing linkage is reported,
  not invented.
- No new dependencies, no network calls. Rendering and capture stay in their own
  skills.
- Not for one-off single maps (use `mind-map-obsidian` directly).

## Done checklist

- [ ] Vault inventoried; allow-list of real notes/tags/links built.
- [ ] Each tier planned only from the allow-list; gaps reported, not invented.
- [ ] Maps rendered via `mind-map-obsidian` into `Maps/`, portable formats.
- [ ] `integrity-lint.sh` passes — zero DANGLING and zero UNWARRANTED references.
- [ ] No scaffolding (`CLAUDE`/`AGENTS`/`GEMINI`/`STUDY-PROTOCOL`/`_study/` …) in any map.
- [ ] Gap report delivered so the user can complete the brain with real notes.
- [ ] No writes to `_study/`, session log, or note bodies.
