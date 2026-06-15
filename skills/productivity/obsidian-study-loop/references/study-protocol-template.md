# Study Protocol

This vault contains a reusable study workflow for agentic CLIs. The agent
reading this file is the tutor. Do not call any LLM API, request API keys, or
run a standalone study app. Read and write plain files in this Obsidian vault.

## Paths and Conventions

- `VAULT_PATH`: `<VAULT_PATH>`
- `STUDY_DIR`: `_study`
- `NOTES_DIR`: `<NOTES_DIR>`
- Session logs live in `_study/sessions/`.
- Active session state lives in `_study/state.json`.
- `state.json` must always be valid JSON and must contain exactly one active
  session pointer or `null`:

```text
{
  "active_session": null
}
```

When a session is active, use a vault-relative path:

```text
{
  "active_session": "_study/sessions/2026-06-15-access-control.md"
}
```

Treat the vault as precious. Never delete or overwrite notes without asking
first. Every state change must be recorded in the session file, which is the
audit trail.

## Status Values

Session frontmatter `status` must be one of:

- `studying`
- `quizzed`
- `notes-written`
- `reviewed`

## Phase 1 - Setup

Trigger examples:

- "I'll be studying X tonight"
- "Start a study session for chapter/topic X"
- "Study X with these objectives..."
- "I'll be studying <study content>"

The setup message may include a simple objective list or a richer per-section
study packet. A study packet can include:

- Section number and title.
- Lesson-level learning outcomes or guiding questions.
- Key terms and definitions.
- Certification exam objectives mapped to that section.
- Lab, simulator, activity, or practice-question expectations.

When the user gives only a chapter/topic or a rough outline, ask once for the
per-section study content packet before creating the session:

```text
Please paste the per-section breakdown if you have it: learning outcomes, key terms, certification objectives, and lab/simulator expectations. If you do not have it, say "skip" and I will create the session from the outline you already gave me.
```

If the user already included the study packet, or if the user says to skip it,
continue setup.

When creating the session:

1. Create a slug from the topic:
   - Lowercase the topic.
   - Replace spaces and punctuation with hyphens.
   - Collapse repeated hyphens.
   - Trim leading and trailing hyphens.
2. Create `_study/sessions/<YYYY-MM-DD>-<slug>.md`.
3. Write this exact frontmatter shape at the top:

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

4. Treat `objectives` as the top-level lesson or section objectives. If the user
   provided section numbers, preserve them in the objective names.
5. Add a structured study packet below the frontmatter when the user supplied
   one:

```markdown
## Study content

### Section <number> - <section title>

#### Learning outcomes

- <question or outcome>
- <question or outcome>

#### Key terms

- **<term>**: <definition>
- **<term>**: <definition>

#### Certification exam objectives

- <exam>: <objective number and wording>
  - <subpoint>
  - <subpoint>

#### Labs, activities, and practice

- <activity, simulator task, lab, or practice question set>
```

Use only the study content the user provides. Clean up obvious paste artifacts,
but do not invent missing definitions, outcomes, or exam objectives during
setup.

6. Add an audit entry below the frontmatter or below `## Study content`:

```markdown
## Session log

- <ISO datetime> - Session created. Status: studying.
```

7. Write `_study/state.json` so it points at the session file:

```text
{
  "active_session": "_study/sessions/<YYYY-MM-DD>-<slug>.md"
}
```

8. Confirm the objectives back to the user in one short list. If a study packet
   was captured, also confirm the section titles captured, but keep it brief.
9. Stop. Do not quiz the user yet.

## Phase 2 - Study Break

Nothing happens during the study break. The user closes the agent and studies
offline. The session survives because `_study/state.json` points to the active
session file on disk.

## Phase 3 - Quiz

Trigger examples:

- "I'm done"
- "Quiz me"
- "Ready for the quiz"

When the user asks to be quizzed:

1. Read `_study/state.json`.
2. If `active_session` is `null`, ask the user to start a study session first.
3. Load the active session file and read its `topic`, `status`, `objectives`,
   and any `## Study content`.
4. Quiz thoroughly, covering every objective. If `## Study content` exists, use
   the learning outcomes, key terms, certification objectives, and lab
   expectations as the quiz blueprint.
5. Mix question formats:
   - Direct recall: "What does X stand for and what does it do?"
   - Fill-in-the-blank: "In ___ access control, permissions attach to roles, not users."
   - Conceptual or compare-contrast: "When would you choose X over Y, and why?"
   - One applied/scenario question per major objective where it makes sense.
6. Ask one section at a time, grouped by objective or by `### Section` from
   `## Study content`.
7. Wait for the user's answers before moving to the next section.
8. Do not reveal answers until the user has responded to that section.
9. After each section, tell the user what they got right, what they got wrong,
   and the correct answer.
10. Keep enough notes during the quiz to assess each objective later.
11. When key terms are provided, include term-definition recall and at least one
   question requiring the user to distinguish similar terms.
12. When certification objectives are provided, include questions that map the
   user's understanding back to those exam objectives.
13. When lab or simulator expectations are provided, include practical or
   scenario questions about what the user would do in that environment.

## Phase 4 - Assess

After the quiz is complete:

1. Grade each objective into exactly one bucket:
   - `solid` - The user demonstrated competence.
   - `partial` - The user got the gist but missed key details.
   - `gap` - The user could not recall it or got it materially wrong.
2. Append or update a `## Assessment` heading in the active session file using
   this format:

```markdown
## Assessment

- <objective 1>: solid - <brief evidence from quiz>
- <objective 2>: partial - <brief evidence from quiz>
- <objective 3>: gap - <brief evidence from quiz>
```

3. Set frontmatter `status: quizzed`.
4. Append an audit entry:

```markdown
## Session log

- <ISO datetime> - Quiz completed. Status: quizzed.
```

If `## Session log` already exists, append the new bullet under the existing
heading instead of creating a duplicate heading.

## Phase 5 - Write Notes

After assessment, write markdown notes into `NOTES_DIR`, one file per session
topic. Example:

```text
Notes/Security+ - Ch3 - Access Control.md
```

Before writing:

1. Determine the intended note path from the topic.
2. If `NOTES_DIR` does not exist, create it.
3. If the notes file already exists, do not overwrite it silently. Ask the user
   whether to append a new dated section or update in place.

For each objective, write one `##` section.

For `solid` objectives:

- Write complete, accurate notes.
- Use clean Obsidian-flavored markdown.
- Include relevant key terms and certification objective mappings from
  `## Study content` when they were supplied.

For `partial` objectives:

- Write complete, accurate notes.
- Add a `> [!tip]` callout flagging the specific detail the user was shaky on.
- Include relevant key terms and certification objective mappings from
  `## Study content` when they were supplied.

For `gap` objectives, write only this placeholder:

```markdown
## <objective name>

> [!todo] RESEARCH NEEDED — you couldn't recall this in the quiz on <date>.
> Research and fill this in yourself, then run a review.

<!-- gap:<objective-slug> -->
```

The `<!-- gap:<objective-slug> -->` HTML comment is a machine marker. Do not
remove it during note writing.

After writing notes:

1. Append a `## Notes written` entry to the session log listing which objectives
   received full notes and which received gap stubs:

```markdown
## Notes written

- <ISO datetime> - Wrote `Notes/<note-file>.md`.
- Full notes: <objective 1>, <objective 2>
- Gap stubs: <objective 3>
```

2. Set frontmatter `status: notes-written`.
3. Append an audit entry under `## Session log`:

```markdown
- <ISO datetime> - Notes written. Status: notes-written.
```

## Phase 6 - User Research

The user researches `gap` objectives offline and fills in the content under the
placeholder in the notes file. The user may leave or delete the `<!-- gap:... -->`
marker.

Do not do this research for the user unless explicitly asked. The learning value
comes from the user filling the gap.

## Phase 7 - Review

Trigger examples:

- "Review my additions"
- "Check my gap notes"
- "Review the notes I filled in"

When the user asks for review:

1. Read `_study/state.json`.
2. If there is an active session, use it. If `active_session` is `null`, find
   the most recent session in `_study/sessions/`.
3. Open the notes file or files listed in that session's `## Notes written`
   entry.
4. Find every section that previously had a `<!-- gap:<objective-slug> -->`
   marker.
5. If the marker still exists, inspect the content around that objective section.
6. If the marker was deleted, use the session assessment and objective heading to
   find the section that was formerly a gap.
7. For each researched gap section, check the user's content for accuracy and
   completeness against the objective:
   - If correct and complete, leave it unchanged and mark it approved.
   - If wrong or incomplete, edit it to be correct and complete.
   - If uncertain about a technical detail, do not guess. Add a
     `> [!warning]` callout explaining what needs verification.
8. Append a changelog to the session file under this exact heading format:

```markdown
## Review — <date>

- <objective>: EDITED — <what changed>. Reason: <why>.
- <objective>: APPROVED — no changes.
```

9. Print the same changelog to the user.
10. Set frontmatter `status: reviewed`.
11. Append an audit entry under `## Session log`:

```markdown
- <ISO datetime> - Review completed. Status: reviewed.
```

## Obsidian Markdown Rules

- Use clean Obsidian-flavored markdown.
- Use `##` headings for objective sections.
- Use callouts such as `> [!note]`, `> [!tip]`, `> [!todo]`, and
  `> [!warning]`.
- Use `[[wikilinks]]` when a concept references another note that already exists
  in the vault.
- Never invent citations or facts.
- If unsure about a technical detail, flag it in a `> [!warning]` callout
  instead of guessing.

## Safety Rules

- Never delete notes unless the user explicitly asks.
- Never overwrite an existing notes file silently.
- Append to existing `CLAUDE.md`, `AGENTS.md`, and `GEMINI.md`; do not clobber
  them.
- Keep `_study/state.json` valid JSON at all times.
- Keep one active session pointer or `null`.
- Record every state change in the session file.
- The agent reading this protocol is the tutor. Do not call Anthropic, OpenAI,
  Gemini, or other LLM APIs directly.

## Dry Run Checklist for Agents

Before completing any setup or protocol change, verify this workflow remains
unambiguous:

1. Setup creates a dated session log, frontmatter, audit entry, and `state.json`
   pointer.
2. Study break requires no action.
3. Quiz loads `state.json`, asks one objective section at a time, waits, then
   gives feedback.
4. Assess writes per-objective `solid`, `partial`, or `gap` results and sets
   `status: quizzed`.
5. Write Notes creates one topic note, writes complete sections for `solid` and
   `partial`, writes exact gap stubs for `gap`, and sets `status: notes-written`.
6. User Research happens offline.
7. Review reopens the written notes, checks the former gap sections, appends the
   required changelog, and sets `status: reviewed`.
