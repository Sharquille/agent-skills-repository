---
name: obsidian-study-loop
description: "Run or install a disk-backed Obsidian study workflow where the agent acts as tutor without calling external LLM APIs. Use when the user wants to set up STUDY-PROTOCOL.md in an Obsidian vault, start a study session from objectives or per-section study content, quiz section-by-section, assess objective mastery, write Obsidian notes with gap placeholders, or review user-filled gap notes. Do not trigger for generic note capture without tutoring or for standalone app/API-based study tools."
# --- provenance ---
category: productivity
source: self-authored from the ComptiaSec+ Obsidian study-loop protocol
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-15
---

# Obsidian Study Loop

Create and run a reusable study system inside an Obsidian vault. The system is
plain Markdown and JSON. The agent reading the protocol is the tutor; do not call
Anthropic, OpenAI, Gemini, or other LLM APIs directly, and do not add API keys.

Use Obsidian file conventions from `knowledge-capture-obsidian` when that skill
is available, but keep this workflow focused on tutoring: session setup, study
break, quiz, assessment, notes, user research, and review.

When installing the workflow into a vault, read
`references/study-protocol-template.md` and copy that canonical template into
`STUDY-PROTOCOL.md`, replacing only the documented placeholders. Do not
reconstruct the protocol from memory when the reference is available.

If the user needs to roll back a mistaken install, wrong-workspace scaffold, or
false-start session, use the companion `undo-obsidian-study-loop` skill instead
of improvising deletion steps.

## Global Invocation Model

This skill is globally available after deployment, so it may be called from any
working directory. The vault-local files still belong inside the target Obsidian
vault. They are what make later sessions seamless when an agent is opened inside
that vault.

When the skill is called from any workspace:

1. Resolve the target vault before writing:
   - Use the current working directory if it already contains `STUDY-PROTOCOL.md`,
     `_study/state.json`, or an `.obsidian/` directory.
   - Use an explicit `VAULT_PATH` if the user provides one.
   - If a previous vault path is visible in the current conversation, confirm it
     before using it.
   - Otherwise, ask for `VAULT_PATH`.
2. Never assume an arbitrary working directory is the vault just because the
   skill was invoked there.
3. After the vault is resolved, create or update the vault-local scaffolding
   there: `STUDY-PROTOCOL.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, and
   `_study/`.
4. For daily study, prefer operating inside the vault once it has been
   scaffolded, because the local pointer files are automatically visible to
   agents that read project instructions.

## Setup a Vault

When the user asks to install or set up the study loop:

1. Resolve `VAULT_PATH`, the Obsidian vault root, using the Global Invocation
   Model above before writing files.
2. Confirm `NOTES_DIR`; default to `<VAULT_PATH>/Notes`.
3. Create this structure:

```text
<VAULT_PATH>/
  STUDY-PROTOCOL.md
  CLAUDE.md
  AGENTS.md
  GEMINI.md
  _study/
    state.json
    sessions/
      .gitkeep
    README.md
```

4. If `CLAUDE.md`, `AGENTS.md`, or `GEMINI.md` already exist, append this block
   instead of overwriting:

```markdown
## Study sessions
When I ask to study, quiz, or review notes, follow the workflow in `STUDY-PROTOCOL.md`.
```

5. Set `_study/state.json` to valid JSON with no active session:

```text
{
  "active_session": null
}
```

6. Copy `references/study-protocol-template.md` to `STUDY-PROTOCOL.md`, replacing
   `<VAULT_PATH>` and `<NOTES_DIR>` with the confirmed paths.
7. If the reference file is unavailable, write a `STUDY-PROTOCOL.md` that
   contains the phase workflow below.

## Phase 1 - Setup a Session

Trigger examples:

- "I'll be studying X tonight"
- "Start a study session for chapter/topic X"
- "I'll be studying <study content>"

The user may provide either a simple objective list or a per-section study
packet. A study packet may include section titles, learning outcomes or guiding
questions, key terms and definitions, certification exam objectives, and lab,
simulator, activity, or practice-question expectations.

Treat a table of contents, module outline, lesson list, or copied course menu as
a rough outline even if the user calls it "objectives." It is not a complete
study packet unless it includes at least one of these per-section expectation
types: learning outcomes/guiding questions, key terms with definitions,
certification exam objective mappings, or lab/simulator expectations.

If the user gives only a topic, objective list, course menu, or rough outline,
ask once before creating any session file or updating `_study/state.json`:

```text
Please paste the per-section breakdown if you have it: learning outcomes, key terms, certification objectives, and lab/simulator expectations. If you do not have it, say "skip" and I will create the session from the outline you already gave me.
```

If the user already included the packet, or says to skip it:

1. Create `_study/sessions/<YYYY-MM-DD>-<slug>.md`.
2. Use this exact frontmatter shape:

```text
---
topic: <topic>
created: <ISO datetime>
status: studying
objectives:
  - <objective 1>
  - <objective 2>
---
```

3. Treat `objectives` as top-level lesson or section objectives. Preserve
   section numbers when provided.
4. If the user supplied a study packet, add it below frontmatter:

```markdown
## Study content

### Section <number> - <section title>

#### Learning outcomes

- <question or outcome>

#### Key terms

- **<term>**: <definition>

#### Certification exam objectives

- <exam>: <objective number and wording>
  - <subpoint>

#### Labs, activities, and practice

- <activity, simulator task, lab, or practice question set>
```

Use only the content the user supplies. Clean obvious paste artifacts, but do
not invent missing definitions, outcomes, or exam objectives during setup.

5. Add the audit log:

```markdown
## Session log

- <ISO datetime> - Session created. Status: studying.
```

6. Point `_study/state.json` at the session using a vault-relative path:

```text
{
  "active_session": "_study/sessions/<YYYY-MM-DD>-<slug>.md"
}
```

7. Confirm the objectives in one short list and stop. Do not quiz yet.

## Phase 2 - Study Break

Do nothing. The user studies offline and may return hours later or from another
machine. State lives on disk.

## Phase 3 - Quiz

Trigger examples: "I'm done", "quiz me", "ready for the quiz".

1. Read `_study/state.json`.
2. If `active_session` is `null`, ask the user to start a study session first.
3. Load the active session and read `topic`, `status`, `objectives`, and any
   `## Study content`.
4. Quiz thoroughly, covering every objective.
5. If `## Study content` exists, use learning outcomes, key terms, certification
   objectives, and lab expectations as the quiz blueprint.
6. Ask one section at a time, grouped by objective or by `### Section`.
7. Wait for the user's answer before moving on. Do not reveal answers early.
8. After each section, explain what was right, what was wrong, and the correct
   answer.
9. Mix direct recall, fill-in-the-blank, compare-contrast, and applied/scenario
   questions. Include term-definition recall and at least one distinguish-similar
   terms question when key terms are provided.

## Phase 4 - Assess

After the quiz, grade each objective:

- `solid` - The user demonstrated competence.
- `partial` - The user got the gist but missed key details.
- `gap` - The user could not recall it or got it materially wrong.

Record results under `## Assessment`:

```markdown
## Assessment

- <objective 1>: solid - <brief evidence from quiz>
- <objective 2>: partial - <brief evidence from quiz>
- <objective 3>: gap - <brief evidence from quiz>
```

Set frontmatter `status: quizzed` and append to `## Session log`:

```markdown
- <ISO datetime> - Quiz completed. Status: quizzed.
```

## Phase 5 - Write Notes

Write one note per session topic in `NOTES_DIR`, for example:

```text
Notes/Security+ - Ch3 - Access Control.md
```

Never overwrite an existing notes file silently. If the file exists, ask whether
to append a new dated section or update in place.

For each objective, write one `##` section:

- For `solid`, write complete, accurate notes.
- For `partial`, write complete, accurate notes and add a `> [!tip]` callout
  flagging the shaky detail.
- For `gap`, write only this placeholder:

```markdown
## <objective name>

> [!todo] RESEARCH NEEDED — you couldn't recall this in the quiz on <date>.
> Research and fill this in yourself, then run a review.

<!-- gap:<objective-slug> -->
```

For `solid` and `partial`, include relevant key terms and certification-objective
mappings from `## Study content` when supplied. Use `[[wikilinks]]` only for
concepts that reference existing notes in the vault.

Append a `## Notes written` entry:

```markdown
## Notes written

- <ISO datetime> - Wrote `Notes/<note-file>.md`.
- Full notes: <objective 1>, <objective 2>
- Gap stubs: <objective 3>
```

Set frontmatter `status: notes-written` and append:

```markdown
- <ISO datetime> - Notes written. Status: notes-written.
```

## Phase 6 - User Research

The user researches `gap` objectives offline and fills in content under the
placeholder. Do not do this work for the user unless explicitly asked.

## Phase 7 - Review Additions

Trigger examples: "review my additions", "check my gap notes".

1. Read `_study/state.json`; if it is `null`, use the most recent session in
   `_study/sessions/`.
2. Open the notes listed in that session's `## Notes written` entry.
3. Find sections that had `<!-- gap:<objective-slug> -->` markers. If the marker
   was deleted, use the session assessment and objective heading to locate the
   former gap.
4. Check the user's content for accuracy and completeness:
   - If correct, leave it and mark approved.
   - If wrong or incomplete, edit it to be correct and complete.
   - If unsure, add a `> [!warning]` callout rather than guessing.
5. Append and print this changelog:

```markdown
## Review — <date>

- <objective>: EDITED — <what changed>. Reason: <why>.
- <objective>: APPROVED — no changes.
```

6. Set frontmatter `status: reviewed` and append:

```markdown
- <ISO datetime> - Review completed. Status: reviewed.
```

## Safety Rules

- Treat the vault as precious. Never delete or overwrite notes without asking.
- Keep `_study/state.json` valid JSON with exactly one active session or `null`.
- Log every status change in the session file.
- Never invent citations or facts.
- If unsure about a technical detail, add a `> [!warning]` callout.
- Keep notes in clean Obsidian Markdown with `##` headings and callouts.
