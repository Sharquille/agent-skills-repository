---
name: knowledge-capture-obsidian
description: "Transform conversations, discussions, and handwritten GoodNotes notes into structured, linked Markdown notes in an Obsidian vault. Captures insights, decisions, and knowledge from chat context, formats by content type, and saves into the vault with frontmatter, tags, wikilinks, and MOC indexing for discovery. Use when asked to save knowledge to Obsidian, capture a decision/FAQ/how-to, write up a discussion, or turn a GoodNotes export into a searchable note. Do not trigger for Notion or other non-Obsidian destinations."
# --- provenance ---
category: productivity
source: https://github.com/makenotion/notion-cookbook/tree/main/skills/claude/knowledge-capture
author: Notion (notion-cookbook) — adapted for Obsidian + GoodNotes
license: MIT
retrieved: 2026-06-13
modified-by: Sharquille Andrew (enhancements/adaptation — MIT, see provenance note)
# note: ported from the Notion knowledge-capture skill. Storage layer fully
# retargeted from the Notion API to Obsidian vault files; GoodNotes path added.
---

# Knowledge Capture (Obsidian + GoodNotes)

Transform conversations, discussions, insights, and handwritten GoodNotes notes
into structured, linked Markdown in an Obsidian vault. The *thinking* (what to
capture, how to structure it) is platform-neutral; the *storage* is plain
Markdown files with frontmatter, `#tags`, and `[[wikilinks]]`.

## Setup

- **Vault path:** ask the user for their vault root if it is not already known
  (e.g. `~/Documents/ObsidianVault`). All notes are written inside it.
- **Attachments folder:** default to the vault's configured attachments folder,
  else `attachments/` at the vault root. GoodNotes exports (PDF/image) live here.
- Never write outside the vault. Confirm the destination folder before creating
  a note if it is ambiguous.

## Quick start

When asked to save knowledge to Obsidian:

1. **Extract** the key information from the conversation (or GoodNotes export).
2. **Classify** the content type (see Content Types).
3. **Locate** the right spot: Grep/Glob the vault for an existing note on the
   topic before creating a new one.
4. **Write** a Markdown note with frontmatter + structured body.
5. **Link** it: add `[[wikilinks]]` to related notes and a line in the relevant
   MOC (Map of Content) so it is not orphaned.

## Obsidian conventions (the storage layer)

| Need | Obsidian mechanism |
|------|--------------------|
| Create a note | Write a `.md` file into the vault |
| Find existing notes | Grep/Glob the vault (titles, `#tags`, content) |
| Update a note | Edit the existing `.md` |
| "Properties" / database fields | YAML **frontmatter** at the top of the note |
| Categories | **Folders** + frontmatter `tags:` |
| Links between notes | `[[Note Name]]` wikilinks (backlinks are automatic) |
| Hub / index page | A **MOC note** (Map of Content) listing `[[links]]` |
| Database views / tables | **Dataview** queries over frontmatter |
| Status, owner, dates | frontmatter fields (`status:`, `created:`, etc.) |

### Standard frontmatter

```yaml
---
title: How to Deploy to Production
type: how-to            # concept | how-to | decision | faq | learning | reference
tags: [deployment, ci-cd]
status: published       # draft | published
created: 2026-06-13
updated: 2026-06-13
source: conversation     # conversation | goodnotes | meeting
related: ["[[CI Pipeline]]", "[[Rollback Procedure]]"]
---
```

## Workflow

### Step 1 — Identify content to capture
From the conversation (or GoodNotes export) extract: key concepts/definitions,
decisions + rationale, how-to procedures, insights/learnings, Q&A pairs,
examples and use cases.

### Step 2 — Classify the content type
Concept · How-To · Decision Record · FAQ · Meeting Summary · Learning/Post-mortem
· Reference. This drives the body structure (below).

### Step 3 — Structure the body
Use the matching template from **Content Types**, add clear `##` headings,
examples, and a `## Related` section with `[[wikilinks]]`.

### Step 4 — Choose the destination folder
Search the vault first (`Grep`/`Glob`). Then pick a folder, e.g.:
`Notes/` (general), `Projects/<name>/`, `Decisions/`, `FAQs/`, `Learnings/`,
`Reference/`. Match the user's existing structure if one exists — inspect the
vault layout rather than imposing a new scheme.

### Step 5 — Write the note
File name = the title in Title Case (Obsidian uses the filename as the note
title), e.g. `How to Deploy to Production.md`. Include frontmatter + structured
body. If it belongs in a "database", that is just a folder of notes sharing the
same frontmatter fields — queried later with Dataview.

### Step 6 — Make it discoverable (avoid orphans)
1. Add `[[links]]` to related notes (backlinks appear automatically).
2. Add a bullet under the right heading in the relevant **MOC note**
   (e.g. `Engineering MOC.md`, `Home.md`). Create the MOC if none exists.
3. Set `tags:` and `status:` in frontmatter.
4. Optional: add a Dataview block to an index note so the new note surfaces
   automatically, e.g.:
   ````markdown
   ```dataview
   table type, status, updated
   from #deployment
   sort updated desc
   ```
   ````

## Capturing from GoodNotes

GoodNotes notes are handwritten/PDF — they cannot be edited directly. Capture
them *into* the vault as searchable companion notes:

1. **Locate the export.** Ask the user to export the GoodNotes page(s) as PDF or
   image into the vault's attachments folder (GoodNotes: Share → Export → PDF).
   Confirm the file path.
2. **Embed the source** in a new Markdown note so the original is one click away:
   `![[my-handwritten-note.pdf]]` (or the image file).
3. **Transcribe / summarize** the handwritten content into structured Markdown —
   this is what makes it searchable and linkable. If the user provides the text
   or you can read an image export, structure it by content type; otherwise ask
   the user to dictate or paste the key points.
4. **Frontmatter** `source: goodnotes` and tag it, so handwritten material is
   filterable from typed notes.
5. **Link** it into the relevant MOC and related notes like any other note.

The result: the handwriting stays as the canonical artifact (embedded PDF), but
a structured, searchable, linked text layer sits on top of it in the vault.

## Content Types (body structure)

- **Concept**: Overview → Definition → Characteristics → Examples → Use Cases → Related
- **How-To**: Overview → Prerequisites → Steps (numbered) → Verification → Troubleshooting → Related
- **Decision**: Context → Decision → Rationale → Options Considered → Consequences → Related
- **FAQ**: Short Answer → Detailed Explanation → Examples → When to Use → Related Questions
- **Learning/Post-mortem**: What Happened → What Went Well → What Didn't → Root Causes → Learnings → Actions

## Content extraction patterns

- **Chat discussion**: key points, conclusions, resources, action items, Q&A
- **Problem-solving**: problem statement, approaches tried, solution, why it worked, future considerations
- **Knowledge sharing**: concept explained, examples, best practices, common pitfalls, resources
- **Decision discussion**: question, options, trade-offs, decision, rationale, next steps

## Formatting best practices

- **Structure**: filename = title; `##` for sections, `###` for subsections.
- **Writing**: open with a one-line overview, use bullets, short paragraphs, examples.
- **Linking**: prefer `[[wikilinks]]` over bare text for any concept that is (or
  could become) its own note — Obsidian auto-creates the backlink.
- **Metadata**: keep frontmatter consistent so Dataview can query it.
- **Searchability**: clear titles, natural-language keywords, consistent tags.

## Create vs. update

- **Create new** when content is substantive (>2 paragraphs), will be referenced
  repeatedly, or needs its own discoverable note.
- **Update existing** when adding to a topic, correcting, or expanding — Grep the
  vault first; if a note exists, edit it and bump `updated:` in frontmatter.
- **Versioning**: for significant changes, add a `## Update history` section
  (date — what changed — why).

## Common issues

- **"Not sure where to save"** → default to `Notes/`, link it into a MOC; folders
  are cheap to reorganize later.
- **"Already exists"** → search first; update the existing note instead of duplicating.
- **"Fragmentary"** → group related fragments into one cohesive note.
- **"Too informal"** → clean up the language while preserving the original insight.
- **"GoodNotes is just an image"** → embed the image/PDF and capture the key
  points as text alongside it; ask the user to dictate if you cannot read it.
