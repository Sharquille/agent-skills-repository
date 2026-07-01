---
name: portable-markdown
description: "Write or reformat Markdown so it renders cleanly and elegantly in EVERY tool, not just one editor. Enforces GitHub-Flavored Markdown alerts (the 5 standard types), HTML-comment machinery, and disciplined typography (comparison tables, key-term bolding, section rules). Use when notes or docs must look polished on GitHub AND Obsidian AND VS Code AND pandoc, when stripping editor-specific syntax (Obsidian %% comments, custom [!callout] types) that leaks as literal text elsewhere, or when an agent asks how to format study notes / READMEs / docs portably. Do not trigger for prose de-AI-ing (use humanizer), for HTML/CSS UI work, or for non-Markdown formats."
# --- provenance ---
category: productivity
source: self-authored (this repository)
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-18
---

# Portable Markdown

Markdown is only "portable" if it looks the same — and looks good — wherever it
is read. The trap is editor-specific syntax that renders beautifully in one tool
and leaks as literal junk in the next. This skill defines one standard that is
**both portable and elegant**, and a way to check files against it.

The two most common leaks:

- **Obsidian `%% ... %%` comments** — hidden in Obsidian, but shown verbatim as
  `%%...%%` on GitHub, GitLab, VS Code preview, pandoc, and most static-site
  generators.
- **Custom callout types** (`[!example]`, `[!question]`, `[!todo]`, `[!success]`,
  `[!info]`, …) — only Obsidian styles these. Everywhere else they degrade to a
  plain blockquote with the literal `[!example]` tag visible.

## When to use

- Writing or reformatting notes, READMEs, or docs meant to be read in more than
  one tool.
- Stripping Obsidian-only or other editor-only syntax from an existing file.
- Any agent (e.g. a study-notes workflow) that needs a house formatting standard
  so its output is portable by default.

Do **not** use this for de-AI-ing prose (that is `humanizer`), HTML/CSS UI work,
or non-Markdown formats.

## The standard

### 1. Callouts: the five GFM-standard alerts only

GitHub-Flavored Markdown defines exactly five alert types. These render as
styled, icon'd boxes on **GitHub, Obsidian, and VS Code**, and degrade to a
clean labeled blockquote in pandoc and elsewhere. Use ONLY these:

```markdown
> [!NOTE]
> Neutral information, context, or a worked example.

> [!TIP]
> Helpful advice, a shortcut, a "watch out" pointer, or study feedback.

> [!IMPORTANT]
> Something the reader must not miss — a key takeaway or required action.

> [!WARNING]
> A caveat, a common mistake, or an uncertain detail to verify.

> [!CAUTION]
> A stronger warning — risk of real harm, data loss, or a serious error.
```

Map every formatting intent onto one of the five — never invent a type:

| Intent | Use |
|---|---|
| Worked example / scenario | `> [!NOTE]` with a bold **Example** lead-in |
| Definition aside / context | `> [!NOTE]` |
| Tip, shortcut, feedback, "partial" understanding | `> [!TIP]` |
| Key takeaway, required action, "research needed" | `> [!IMPORTANT]` |
| Caveat, common mistake, detail to verify | `> [!WARNING]` |
| Serious risk (data loss, security, irreversible) | `> [!CAUTION]` |

Rules:
- The type token is **UPPERCASE** (`[!NOTE]`, not `[!note]`) — required by GitHub.
- The alert title line carries no other text; put content on the lines below.
- Continue every line of the box with `> `, including blank lines (`>`).

### 2. Hidden machinery: HTML comments only

For anchors, IDs, and machine-readable markers a renderer should never show, use
standard HTML comments. They are hidden in **every** Markdown-to-HTML renderer,
including Obsidian.

```markdown
<!-- marker:some-stable-id -->
```

Never use `%% ... %%` for this — it is Obsidian-only and leaks everywhere else.

### 3. Typography

Portable does not mean plain. Use the standard constructs well:

- **Headings carry the structure.** One `##` per concept; nest with `###`. Never
  skip a level. Headings — not horizontal rules — are what separate sections.
- **Default to prose and tight bullets.** A short paragraph plus a bolded bullet
  pair reads cleaner than a table for almost everything. For an "X vs Y" contrast,
  write a one-line framing then two bullets:

  ```markdown
  Both act after prevention fails, but at different moments.

  - **Detective** — *during* the incident: identify or record it (IDS alert, audit log).
  - **Corrective** — *after* the incident: reduce or undo the damage (restore from backup).
  ```

- **Tables are a last resort, not the default.** Use one only for a genuine
  reference matrix (3+ rows × 2+ real attribute columns) and only with a real
  header row. **Never** a header-less `| | A | B |` two-column comparison — the
  empty top-left cell looks clunky and a bullet pair says the same thing better.
- **Key terms:** bold the term, then define — `- **Term**: definition.`
- **Horizontal rules are rare.** Do not put a `---` between sections; the headings
  already do that. Reserve at most one `---` to fence a trailing metadata or
  `## Review` block, or use none.
- **Lists:** tight and parallel; no trailing `etc.`; no one-item lists.
- **Examples:** exactly one concise example per concept, in a `> [!NOTE]` box.
- **No decorative emoji** in body text or headings.
- **Spacing:** exactly one blank line between blocks; a blank line before and after
  every alert (and any table you do keep); never two blank lines in a row; no
  trailing spaces.

## Reformatting an existing file

1. Read the file. Identify every `%%...%%`, every `[!type]` callout, and any
   editor-specific embed.
2. Convert `%% x %%` → `<!-- x -->`.
3. Map each callout to one of the five standard alerts (table above). Preserve
   the content; only the wrapper changes.
4. Keep "X vs Y" contrasts as a one-line framing plus a bolded bullet pair —
   do not build a table for them. Demote any header-less `| | A | B |` table you
   find to prose/bullets.
5. Strip `---` rules between sections (headings separate them); keep at most one
   before a trailing `## Review` block. Ensure heading levels and blank-line
   spacing around alerts.
6. Run the lint check (below) and confirm zero findings.


## Lifecycle Project Notes

For `project-build-loop` notes, use the lifecycle house style in
`rules/lifecycle.md` in addition to the base portability standard. The lifecycle
checks catch problems the base lint intentionally does not cover: contradictory
task status, stale routed work, malformed Markdown table rows, skipped heading
levels, overgrown task-note checklists, and table overuse in focused task notes.

Run the lifecycle gate on touched lifecycle Markdown before checkpoint, consult,
or publish handoff:

```text
scripts/lifecycle-lint.sh build-log/task-1.5.md build-log/task-1.5.steps.md
```

The gate is intentionally scoped. Do not recurse through the entire `build-log/`
unless the task is an explicit cleanup pass; old historical notes should not
block new work unless they are being edited or promoted.

## Lint check

`scripts/lint.sh <file-or-dir>` flags anything non-portable: any `%%` sequence,
any `[!TYPE]` alert whose type is not one of
`NOTE | TIP | IMPORTANT | WARNING | CAUTION`, and any alert with text after the
tag on the same line (it must sit alone). Exit code 0 = portable, 1 = findings.

Quick manual equivalent:

```bash
grep -nE '%%|\[![A-Za-z]' file.md   # inspect every hit; only the 5 UPPERCASE alert tags are allowed
```

## Portability matrix

| Construct | GitHub | Obsidian | VS Code preview | pandoc / generic |
|---|---|---|---|---|
| `> [!NOTE]` … `[!CAUTION]` | styled box | styled box | styled box | plain blockquote (tag visible) |
| custom `[!example]` etc. | **plain quote, tag visible** | styled box | plain quote | plain quote, tag visible |
| `<!-- comment -->` | hidden | hidden | hidden | hidden |
| `%% comment %%` | **literal `%%…%%`** | hidden | **literal** | **literal** |
| tables, `---`, `**bold**` | yes | yes | yes | yes |

The standard above lives entirely in the top "portable everywhere" rows.
