---
name: obsidian-study-loop
description: "Run or install a disk-backed Obsidian study workflow where the agent acts as tutor without calling external LLM APIs. Use when the user wants to set up STUDY-PROTOCOL.md in an Obsidian vault, start a study session from objectives or per-section study content, quiz the full session or a scoped unit like 1.1 / Security Controls, assess objective mastery, write professional tagged Obsidian notes with gap placeholders and applied checkbox exercises, or review user-filled gaps and applied reasoning. Do not trigger for generic note capture without tutoring or for standalone app/API-based study tools."
# --- provenance ---
category: productivity
source: self-authored from the ComptiaSec+ Obsidian study-loop protocol
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-15
---

# Obsidian Study Loop

Create and run a reusable study system inside an Obsidian vault. The system is
plain Markdown and JSON. The agent reading the protocol is the tutor and does not
outsource the teaching, quizzing, or grading to an external LLM API, and does not
add API keys. The one exception is the optional `study-consult-panel`, an
explicit, opt-in, read-only **advisory** second opinion through the existing
`opencode-consult` wrapper — it adds no keys, never becomes the tutor, and its
output is untrusted until the agent verifies it.

Use Obsidian file conventions from `knowledge-capture-obsidian` when that skill
is available, but keep this workflow focused on tutoring: session setup, study
break, quiz, assessment, notes, user research, and review.

When installing the workflow into a vault, read
`references/study-protocol-template.md` and copy that canonical template into
`STUDY-PROTOCOL.md`, replacing only the documented placeholders. Do not
reconstruct the protocol from memory when the reference is available.

This SKILL.md and `references/study-protocol-template.md` intentionally carry
the same workflow: the template is what gets installed into vaults. Any change
to shared workflow content must be made in both files, and installed vaults
then need `scripts/sync_study_protocol.py <VAULT_PATH>` (dry-run, then
`--apply`) to pick it up.

If the user needs to roll back a mistaken install, wrong-workspace scaffold, or
false-start session, use the companion `undo-obsidian-study-loop` skill instead
of improvising deletion steps.

## Helper Skill Routing

This skill is the study orchestrator. Use these helper skills when available:

- `knowledge-capture-obsidian`: apply its vault hygiene conventions before
  writing notes. Search the vault first, use consistent frontmatter, tags,
  `[[wikilinks]]`, and MOC/index links when they fit the vault.
- `humanizer`: run a prose pass on completed `solid` and `partial` note
  sections so they read like concise study notes, not chatbot output. Preserve
  technical accuracy and do not add personality to reference material.
- `portable-markdown`: the formatting authority for every note this skill writes.
  Use only the five GFM-standard alerts (`[!NOTE] [!TIP] [!IMPORTANT] [!WARNING]
  [!CAUTION]`), HTML `<!-- ... -->` machine markers, and clean typography
  (comparison tables for "X vs Y", bold key terms, section rules). Never emit
  Obsidian-only syntax (`%% ... %%` comments or custom callout types). Run its
  `scripts/lint.sh` on a note before considering it done.
- `study-research-queries`: when the user asks for help researching a `gap`, or
  when a gap note needs better search strings, generate a source-aware research
  plan and query set. Do not do the user's offline research unless asked.
- `literature-review`: use only for formal, citation-backed deep research. It is
  too heavy for routine certification notes.
- `study-consult-panel`: an optional two-model advisory panel for high-stakes or
  uncertain notes. It routes prose to MiMo v2.5 Pro and technical accuracy to
  Kimi K2.7 Code (read-only, via `opencode-consult`), then cross-checks them to
  manage single-model bias. Consult at the section level before finalizing; you
  remain the gatekeeper and re-apply `portable-markdown`. Skip silently if the
  opencode CLI or OpenRouter is unavailable.
- `study-map`: once the vault has more than one chapter, build the tiered map
  stack (Home index, chapter maps, section sub-maps, concept maps, tag-lens,
  prerequisite map). It is integrity-gated — every node, edge, and tag must
  resolve to a real note/tag/link, and missing linkage is reported, not invented.
  It writes only into `Maps/` and never touches `_study/` or note bodies. Refresh
  affected maps when a chapter reaches `reviewed`.

Helper skills never replace the safety rules in this workflow. Do not add API
keys and do not invent citations or facts. Do not outsource teaching, quizzing,
or grading to an external LLM API; the only external-model call permitted is the
explicit, read-only, advisory `study-consult-panel` consult, whose output the
agent must verify before use.

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

## Timestamp and Link Discipline

Before writing any timestamped frontmatter or session-log entry, get the real
current time from the system. Always use **local time**, never UTC: a UTC stamp
(`date -u`) can land on the next calendar day and make notes look dated a day
ahead. Do not invent, round, reuse, or default timestamps to midnight.

- For ISO datetime fields and session log bullets, use local time with offset:

```text
date +%Y-%m-%dT%H:%M:%S%z
```

- For human-facing date-only fields such as note `created`, `updated`, review
  headings, and mastery-evidence dates, use the local calendar date:

```text
date +%F
```

Inspect the active offset or abbreviation with `date +%z` or `date +%Z` to
confirm the zone before writing. If the user or vault specifies an IANA timezone,
use it explicitly, for example `TZ=America/Dominica date +%F`. Never use `date -u`
or a trailing `Z` for note/log timestamps, and do not infer a named timezone from
a bare offset. If the timezone source is ambiguous or conflicts with the current
system, ask before writing a date-only field. Paste the exact command output
into the file.

Before adding any `[[wikilink]]`, verify that the target note already exists in
the vault. Use `rg --files` or another file listing and match the note basename
without `.md`. If the target note does not exist, write the concept as plain text
instead of a wikilink. Only create a wikilink to a not-yet-existing concept when
the user explicitly asks to create future concept pages.

The same verification applies to heading anchors. Before writing
`[[Note#Heading]]` or a same-note `[[#Heading]]` link, confirm the exact heading
text exists in the target note. When a heading is renamed, merged, or
consolidated away, search the vault for `#<old heading>` references in the same
edit and update them so no anchor dangles.

## Vault Structure and Note Granularity

A scaffolded study vault has this shape. Keep writes inside these locations:

```text
<VAULT_PATH>/
  STUDY-PROTOCOL.md                    # installed protocol (sync-managed)
  CLAUDE.md / AGENTS.md / GEMINI.md    # pointer blocks only
  Notes/                               # study notes; this skill writes here
  Maps/                                # study-map output; never written here
  _study/
    state.json                         # active-session pointer
    sessions/                          # one file per study session
    README.md                          # one-paragraph explainer (see Setup)
```

Note granularity and naming:

- When the course has numbered sections and quizzes run per section, default to
  **one note per section**, named `<Course short name> Ch<N> - <Section
  title>.md` (for example `Security+ Ch1 - Security Controls.md`), with
  frontmatter `section` set to that section's number.
- Use a single chapter- or topic-wide note only when the session is one
  unsectioned topic.
- If an existing note already covers the chapter and a new section is about to
  be written, ask whether to append the new section to that note or start a
  per-section note. Never fork a second note for the same scope.
- Do not add an H1 title line to note bodies. The filename and frontmatter
  `title` carry the display name; body headings start at `##`.

## Sync Existing Vault Protocol

When the user asks to sync, refresh, update, or check whether a working vault is
stale relative to this skill, run the bundled helper script instead of manually
rewriting `STUDY-PROTOCOL.md`:

```text
scripts/sync_study_protocol.py <VAULT_PATH>
```

The helper compares the bundled `references/study-protocol-template.md` to the
vault-local `STUDY-PROTOCOL.md` after rendering `<VAULT_PATH>` and `<NOTES_DIR>`.
It dry-runs by default and prints a unified diff. Apply only when the user asks
to update/sync or after they approve the dry run:

```text
scripts/sync_study_protocol.py <VAULT_PATH> --apply
```

The helper updates only `STUDY-PROTOCOL.md`. It must not touch `Notes/`,
`_study/state.json`, or `_study/sessions/`.

## Session Lifecycle and Recovery

`_study/state.json` is the handoff point between agent sessions. A reviewed
session is still the active session until the user explicitly starts a new
session, clears state, or runs an undo flow. Do not set `active_session` to
`null` just because a scope or session reached `status: reviewed`.

At the start of every study-loop action:

1. Read `_study/state.json` if it exists.
2. If `active_session` points at an existing session, treat that as the current
   study context even when its frontmatter status is `reviewed`.
3. If `active_session` is `null` but `_study/sessions/*.md` exists, inspect the
   most recent session file before asking the user to start over. Tell the user
   what was found and ask whether to resume it, make it active again, or start a
   new session.
4. If the user is starting a new topic while another session is active, preserve
   the existing session file. Ask whether to replace the active pointer with the
   new session. Never delete or clear the previous session as part of normal
   setup.
5. Only write `{ "active_session": null }` when the user explicitly asks to
   clear, close, undo, or remove active state.

## Scope Boundary Rules

For a scoped quiz or note, the section's learning outcomes, key terms, labs,
activities, and practice expectations define the teaching scope. Certification
exam objective mappings are exam-alignment metadata, not permission to pull in
full content from a later section.

When the packet maps a broad exam objective to more than one lesson:

1. Quiz only the parts of that exam objective that are directly supported by the
   in-scope section's learning outcomes or key terms.
2. If a mapped exam objective contains topics taught in a later section, mention
   them only as a brief forward reference, for example: "Covered in 1.2 Security
   Controls." Do not quiz, grade, or write full notes for that later material.
3. Before writing notes, classify each candidate note section as `in-scope`,
   `brief cross-reference`, or `out-of-scope`. Write full sections only for
   `in-scope` material.
4. If out-of-scope material was accidentally quizzed, record it as a scope issue
   in the session log and do not use it to mark the current scope as `gap` or
   `partial`.
5. If an existing note already contains out-of-scope material, do not silently
   move or delete it. Flag the overlap and ask before restructuring the note.

## Context-Anchored Examples and Mastery Checks

Applied examples must identify the protected context instead of using vague
phrases such as "the same asset." Use this reasoning chain:

```text
Subject or asset -> situation or threat -> relevant facts -> decision or answer -> why it fits -> limitation or alternative
```

Adapt the chain to the topic. A subject may be an asset set, command, protocol,
role, process, architecture, incident, risk, control, or troubleshooting
symptom. Every claimed answer must have a defensible relationship to the stated
context.

Distinguish two example types:

- A **worked example** includes the answer and teaches the reasoning. It is not
  mastery evidence because the learner did not produce the answer.
- A **mastery check** withholds the answer and requires the learner to select,
  classify, compare, sequence, diagnose, calculate, configure, or explain. Every
  answered mastery check is evidence for grading and confidence.

Two assessment channels coexist. The Phase 3 quiz is asked and answered live in
chat; in-note `study-check` blocks are answered offline by the learner and scored
during Phase 7 review. Use the chat quiz to assess within a session; embed a
`study-check` when you want the learner to practice application between sessions.

Where meaningful, include at least one mastery check per objective. Use
checkboxes when multiple selections or distractors help; use short-answer fields
when reasoning matters more than selection.

Keep worked examples visually subordinate to the objective they support. Do not
use `### Example` for a short scenario because it clutters the note outline and
renders more prominently than the content warrants. Use a compact callout:

```markdown
> [!NOTE]
> **Worked example** — <concrete subject or asset and situation>
> **Reasoning:** <answer or decision and why it fits>
> **Limit:** <what it does not cover, or a relevant alternative>
```

Omit a label only when it would be artificial, but keep the context chain
complete. Reserve `###` headings for durable subsections such as `Key terms` or
`Exam focus`, not one-paragraph labels.

Use this general machine-readable structure:

```markdown
<!-- study-check:start id=<stable-id> type=<check-type> scope=<scope> objective=<objective-slug> -->
### Mastery check: <short title>

> [!NOTE]
> **Scenario** — <context and task without the answer>

#### Your answer

- [ ] <candidate option when useful>
- [ ] <candidate option or distractor>

Replace `Write here.` on each relevant line. Keep the field label and the
HTML hidden marker on the line above it so a later review can locate
your exact response.

<!-- learner-answer:response -->
- **Response:** Write here.
<!-- learner-answer:reasoning -->
- **Reasoning:** Write here.
<!-- learner-answer:transfer -->
- **Limitation, alternative, or rejected options:** Write here.

#### Your confidence before review

- [ ] Low
- [ ] Medium
- [ ] High

<!-- study-check:end id=<stable-id> -->
```

Do not reveal the answer key in the exercise. Use a stable ID that includes the
section and concept, such as `1.2-control-category-fit`. Check types may include
`selection`, `classification`, `compare-contrast`, `sequence`, `diagnosis`,
`calculation`, `configuration`, `scenario-response`, or a narrower subtype such
as `asset-control-fit`. A generated check may use more specific answer-field
labels, but each editable line must retain a preceding
`<!-- learner-answer:<field> -->` marker and the `Write here.` sentinel.

Use HTML `<!-- ... -->` comments for all machine markers — never Obsidian
`%% ... %%`. HTML comments stay hidden in every Markdown renderer (GitHub,
VS Code, pandoc, and Obsidian's reading view), keeping the note portable, while
`%%` leaks as literal text outside Obsidian. The `portable-markdown` skill owns
this rule.

While a check is pending, task boxes provide clickable choices. After review,
replace each task line with a non-task answer-state line so checked choices do
not appear struck through:

```markdown
- **Selected:** <original option text>
- **Not selected:** <original option text>
```

Do the same for learner confidence. This is a presentation-only normalization:
preserve every original choice exactly and record it in mastery evidence before
changing the rendering.

## Mastery Evidence and Confidence

Use all learner-produced evidence, not only the final quiz score. Evidence
includes quiz answers, answered `study-check` blocks, corrected gap research,
lab decisions, and later review explanations.

Score each evidence item out of 8 with this topic-neutral rubric:

- Accuracy or correctness: `0-2`
- Context or application fit: `0-2`
- Reasoning or explanation: `0-2`
- Transfer, limitations, alternatives, or distractor rejection: `0-2`

Map scores to mastery: `solid` = 7-8, `partial` = 4-6, `gap` = 0-3.

For recall or definition items where context, reasoning, and transfer do not
genuinely apply, score only the dimensions that fit and judge mastery on those. A
fully correct term-definition answer is `solid` even though it earns no
application or transfer points. Never let inapplicable dimensions drag a correct
recall answer down to `partial` or `gap`. Reserve the full four-dimension score
for application, scenario, and explanation items.

Keep two confidence signals separate:

- **Learner confidence**: Low, Medium, or High, selected before feedback.
- **Tutor confidence in mastery**:
  - `high`: at least two independent evidence items support mastery, including
    one applied or transfer item, with no unresolved critical misconception.
  - `medium`: evidence is limited, mixed, or based on one strong item.
  - `low`: evidence is weak, contradictory, below 4/8, or absent.

Judge calibration after scoring:

- `well-calibrated`: learner confidence matches demonstrated mastery.
- `overconfident`: learner confidence materially exceeds demonstrated mastery.
- `underconfident`: demonstrated mastery materially exceeds learner confidence.
- `unknown`: learner confidence was not supplied.

The `## Assessment — <scope>` block is the canonical record of scores and
mastery. Maintaining a separate roll-up ledger is optional; use it only when a
cross-session view helps, and keep it consistent with the assessment — it must
summarize, never contradict it. Keep the ledger lean:

```markdown
## Mastery evidence

| Date | Scope | Objective | Evidence | Score | Mastery | Confidence | Notes |
|---|---|---|---|---:|---|---|---|
| <date> | <scope> | <objective> | <quiz or study-check-id> | <0-8> | <solid|partial|gap> | tutor <level>, learner <level|unknown>, <calibration> | <brief evidence> |
```

Historical evidence remains in the ledger. New evidence may update the current
tutor confidence, but must not rewrite what the learner originally answered.

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

6. Write `_study/README.md` with this one-paragraph explainer:

```markdown
# _study

State and session logs for the Obsidian study loop. Managed by the study
workflow in `STUDY-PROTOCOL.md`. Do not hand-edit `state.json` unless
recovering.
```

7. Copy `references/study-protocol-template.md` to `STUDY-PROTOCOL.md`, replacing
   `<VAULT_PATH>` and `<NOTES_DIR>` with the confirmed paths.
8. If the reference file is unavailable, write a `STUDY-PROTOCOL.md` that
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

1. Read `_study/state.json` first. If it points at an existing session, report
   the active topic and status. If the user is clearly starting a new study
   session, preserve the existing session file and ask for confirmation before
   replacing the active pointer. While state is open, run the session-start
   sweep and surface anything found before proceeding:
   - Pending gap stubs: notes whose `<!-- gap:` markers still contain the
     unchanged `Write here.` sentinel. Report file and count; offer resume
     (fill and review), keep waiting, or archive the stub.
   - Unconsumed `## Quiz progress` blocks in session files: an interrupted
     quiz. Offer to resume it before starting anything new.
   - Due re-reviews: `next review` dates in the latest assessment blocks that
     are on or before today. Offer to prepend 1-2 retrieval questions for
     those objectives to the next quiz; if the re-check score drops, demote
     the objective's mastery and reopen a gap stub.
2. Create a slug from the topic:
   - Lowercase the topic.
   - Replace spaces and punctuation with hyphens.
   - Collapse repeated hyphens.
   - Trim leading and trailing hyphens.
3. Create `_study/sessions/<YYYY-MM-DD>-<slug>.md`.
4. Use this exact frontmatter shape:

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

5. Treat `objectives` as top-level lesson or section objectives. Preserve
   section numbers when provided.
6. If the user supplied a study packet, add it below frontmatter:

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

7. Add the audit log:

```markdown
## Session log

- <ISO datetime> - Session created. Status: studying.
```

8. Point `_study/state.json` at the session using a vault-relative path:

```text
{
  "active_session": "_study/sessions/<YYYY-MM-DD>-<slug>.md"
}
```

9. Confirm the objectives in one short list and stop. Do not quiz yet.

Maintain this section order in the session file for the whole session
lifecycle, inserting each new block within its group rather than appending at
the end of the file:

1. frontmatter
2. `## Study content`
3. `## Unit progress`
4. `## Assessment — <scope>` blocks, in section order
5. `## Notes written — <scope>` blocks, in section order
6. `## Review — <date>` blocks, oldest first
7. `## Mastery evidence` (optional)
8. `## Session log` (always last)

When a heading already exists, append under it instead of creating a duplicate
heading. Do not reorder an existing session file without user approval.

## Phase 2 - Study Break

Do nothing. The user studies offline and may return hours later or from another
machine. State lives on disk.

## Phase 3 - Quiz

Trigger examples:

- "I'm done"
- "quiz me"
- "ready for the quiz"
- "quiz me on 1.1"
- "quiz section 1.2"
- "quiz Security Controls"
- "quiz everything"

1. Read `_study/state.json`.
2. If `active_session` is `null`, inspect `_study/sessions/*.md` for the most
   recent session. If one exists, report its topic, status, and latest unit
   progress, then ask whether to resume that session and restore the pointer.
   If no session exists, ask the user to start a study session first.
3. Load the active session and read `topic`, `status`, `objectives`, and any
   `## Study content`.
4. Resolve the quiz scope:
   - If the user says only "quiz me", "I'm done", or "ready for the quiz", quiz
     the full active session.
   - If the user names a section, chapter, objective number, or title, quiz only
     that matching scope.
   - If the user says "quiz everything", quiz the full active session.
   - If the requested scope is ambiguous, ask one clarifying question and do not
     start the quiz yet.
   - If scope filtering leaves zero eligible objectives (for example, the named
     section has no in-scope learning outcomes, or everything in scope is
     already assessed and the user asked only for new material), stop: report
     why nothing is quizzable, do not run an empty quiz, do not write an
     assessment, and ask for a different scope or an updated study packet.
5. Quiz thoroughly, covering every objective in scope. Before the first
   question, start a disk-backed progress block in the session file so an
   interrupted quiz can resume:

```markdown
## Quiz progress — <scope>

- Planned: <objective 1>; <objective 2>; <objective 3>
- <ISO datetime> - Q1 <objective 1> - score <0-8> - <one-line answer summary>
```

   Append one line per scored answer as it is scored. When Phase 4 writes the
   assessment, mark the block consumed by appending
   `- Consumed by Assessment — <scope> on <ISO datetime>` rather than deleting
   it. If a quiz starts and an unconsumed `## Quiz progress` block already
   exists for the same scope, offer to resume from the first unanswered planned
   objective instead of restarting.
6. If `## Study content` exists, use the in-scope learning outcomes, key terms,
   labs, activities, and practice expectations as the quiz blueprint. Use
   certification exam objective mappings only to align question wording to the
   exam, not to introduce future-section content.
7. Ask exactly one quiz question at a time. Do not list the full quiz or multiple
   lettered questions in one message. Keep the remaining questions as an
   internal queue, mirrored by the `## Quiz progress` block on disk — context
   can evaporate between turns; the block is the recovery point.
8. If a section has several planned prompts, ask only the next prompt, wait for
   the user's answer, give brief feedback, record assessment notes, and then ask
   the next prompt.
9. Group the hidden question queue by objective or by `### Section` from
   `## Study content`, but keep the chat experience conversational and
   one-question-at-a-time.
10. Do not reveal an answer until the user has responded to that question.
11. After each answer, tell the user what was right, what was wrong or missing,
   and the correct answer before moving on.
12. Keep enough notes during the quiz to assess each objective later.
13. When key terms are provided, include term-definition recall and at least one
   question requiring the user to distinguish similar terms. Also include at
   least one pure free-recall prompt per section — describe a scenario and ask
   the user to produce the term or mechanism with no candidate list in sight.
   Recognition among presented options is weaker evidence than production.
14. When certification objectives are provided, include questions that map the
   user's understanding back to those exam objectives.
15. When lab or simulator expectations are provided, include practical or
   scenario questions about what the user would do in that environment.
16. For applied questions, state a concrete subject or asset, situation or
    failure path, and relevant facts. Ask the user to explain why the answer or
    decision fits that context, not merely name a term.
17. When practical, ask for learner confidence before giving feedback. Score
    each answer with the universal 8-point rubric; the scores feed the required
    `## Assessment — <scope>` block in Phase 4 (the separate `## Mastery
    evidence` ledger stays optional).
18. Record the resolved scope for assessment and notes. Examples: `full-session`,
   `1.1`, `1.2 Security Controls`, or `1.3 Use the Simulator`.

## Phase 4 - Assess

After the quiz, grade each in-scope objective:

- `solid` - The user demonstrated competence.
- `partial` - The user got the gist but missed key details.
- `gap` - The user could not recall it or got it materially wrong.

Record results under a scoped assessment heading:

```markdown
## Assessment — <scope>

- <objective 1>: solid (<score>) - <brief evidence from quiz> - next review <YYYY-MM-DD>
- <objective 2>: partial (<score>) - <brief evidence from quiz>
- <objective 3>: gap (<score>) - <brief evidence from quiz>
```

Assessment and re-assessment records:

- An objective whose supporting evidence is entirely recall or definition items
  is labeled `solid (recall-only)`, and its tutor confidence stays at most
  `medium` until at least one applied or transfer evidence item is recorded.
- Give every `solid` objective a `next review` date: today + 7 days, or
  today + 21 days when tutor confidence is `high`. `partial` and `gap`
  objectives are re-tested through the normal loop and need no date.
- If an `## Assessment — <scope>` block already exists for this scope, do not
  edit it. Create a new dated heading `## Assessment — <scope> — <YYYY-MM-DD>`
  so attempts stay distinguishable; the newest dated block is the current one.

If the scope is not the full session, do not imply that the entire session has
been quizzed. Update or append a unit progress table. Keep exactly one row per
scope — update the existing row in place on re-quiz or later phases; never add
a duplicate row for the same scope:

```markdown
## Unit progress

| Scope | Quiz | Notes | Review |
|---|---|---|---|
| <scope> | quizzed | pending | pending |
```

Set frontmatter `status: quizzed` when the full session has been quizzed or when
at least one scoped quiz has completed and the latest action is quiz assessment.
The scoped assessment heading and unit progress table are the source of truth
for which units were actually covered.

Append to `## Session log`:

```markdown
- <ISO datetime> - Quiz completed for <scope>. Status: quizzed.
```

Record each objective's score and mastery in the `## Assessment — <scope>` block
using the universal 8-point rubric (apply the recall exception for definition
items). Use `unknown` learner confidence when confidence was not collected.
Calculate tutor confidence from all evidence currently available for that
objective, not from the newest answer alone. Optionally roll the result into
`## Mastery evidence`. Finally, mark the scope's `## Quiz progress` block
consumed (`- Consumed by Assessment — <scope> on <ISO datetime>`).

## Phase 5 - Write Notes

Write notes for the assessed scope, not necessarily the whole session. If the
latest quiz covered only `1.1`, write only the `1.1` note sections and gap stubs.
If the latest quiz covered the full session, write all assessed objectives.

Choose the note file per the Vault Structure and Note Granularity rules:
one note per section when quizzes run per section, for example:

```text
Notes/Security+ Ch3 - Access Control.md
```

Never overwrite an existing notes file silently. If the file exists, ask whether
to append a new dated section or update in place.

Before drafting, search the vault for related notes and existing concept pages.
Build a short list of verified existing note basenames that may be linked. Use
`[[wikilinks]]` only for verified existing notes unless the user explicitly asked
for future concept pages. Keep the vault clean: no duplicate topic notes, no
orphaned notes when an obvious MOC or course index exists, and no unstructured
dumps.

New notes must start with Obsidian frontmatter:

```text
---
title: <note title>
type: learning
course: <course or certification name>
domain: <domain or chapter>
section: <scope>
status: draft
tags:
  - study
  - security-plus
  - <normalized-topic-tag>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
source: study-session
related: []
---
```

Use lower-case kebab-case tags. Add or adjust tags to match the vault's existing
tag style when one is visible.

Frontmatter field contract:

- `type`: `learning` for graded study notes; `reference` for non-graded
  reference notes (for example, tool mechanics captured without a quiz).
- Note `status` lifecycle: `draft` when written; `reviewed` once every gap and
  answered study-check in the note has been reviewed. Reference notes use
  `status: reference`. Note status is independent of session status.
- Before creating a note, read the frontmatter of an existing note from the
  same course and copy the exact `course` and `domain` value formats. Do not
  introduce a second spelling of the same course or domain.
- `domain` precedence: when the course has certification exam domains (for
  example "1.0 General Security Concepts"), use the exam domain; otherwise use
  the course chapter. Pick one meaning per course and never mix the two within
  the same vault.
- Bump `updated:` to the local date on every substantive edit, including
  review corrections and consolidations.
- Keep frontmatter `related:` and the `## Related` section listing the same
  verified notes.

For each assessed in-scope objective, write one `##` section:

- For `solid`, write complete, accurate notes.
- For `partial`, write complete, accurate notes and add a `> [!TIP]` callout
  flagging the shaky detail.
- For `gap`, write only this placeholder:

```markdown
## <objective name>

> [!IMPORTANT]
> **RESEARCH NEEDED** — you couldn't recall this in the quiz on <date>.
> Research and fill this in yourself, then run a review. Replace the `Write
> here.` sentence below, but keep the boundary comments.

<!-- gap:<objective-slug> -->
<!-- learner-edit:start id=gap-<objective-slug> -->
Write here.
<!-- learner-edit:end id=gap-<objective-slug> -->
```

The learner-edit boundaries are user-owned space. During review, preserve the
user's original wording long enough to score it, then make required corrections
inside the same boundaries and record them in the changelog. Never place tutor
feedback inside the learner-edit region.

For `solid` and `partial`, include in-scope key terms and certification-objective
mappings from `## Study content` when they are anchored to the current section's
learning outcomes. Use `[[wikilinks]]` only for verified existing notes. If a certification mapping points to a later section, add at
most a short forward reference instead of full notes.

For `solid` and `partial`, use this section shape when the content supports it:

```markdown
## <objective name>

<One or two plain paragraphs explaining the concept accurately.>

### Key terms

- **<term>**: <definition>

### Exam focus

- <exam objective mapping or likely test angle>

> [!NOTE]
> **Worked example** — <concrete subject or asset and situation>
> **Reasoning:** <answer or decision and why it fits>
> **Limit:** <what it does not cover, or a relevant alternative>
```

For applied examples, replace vague claims with the full context chain: asset,
situation, relevant facts, answer or decision, fit, and limitation. Add a
`study-check` mastery exercise when application would reveal more understanding
than another definition question.

Do not use a heading for a short worked example. Keep it in an `[!NOTE]`
callout so it remains visible without competing with objective and subsection
headings in the outline.

After drafting, do a note quality pass:

- Remove chatbot phrasing such as "here is," "let's dive in," generic
  conclusions, inflated importance, and vague attributions.
- Prefer simple, direct sentences and concrete examples.
- Keep heading weight proportional to structure: `##` for objectives, `###` for
  durable subsections, and callouts for short examples or feedback.
- Use industry-standard cybersecurity terminology in headings, preferring the
  exact terms used in the relevant certification objectives, course materials,
  NIST CSF, or MITRE ATT&CK (e.g. "threat actors" over "threat agents"). Avoid
  vague or generic headings that do not signal the specific concept.
- Make every learner-editable location explicit. Use hidden HTML
  `<!-- ... -->` learner boundaries for research gaps and put each
  `learner-answer` marker on its own line above the mastery-check field.
- Preserve course wording for definitions and exam objectives when the user
  supplied it.
- Do not cite sources unless a real source was consulted and can be named.
- If a technical detail is uncertain, add a `> [!WARNING]` callout instead of
  guessing.

Add a short discovery block near the end of the note when useful:

```markdown
## Related

- [[<verified existing related note>]]

## Mind map seeds

- Parent: [[<verified existing course or domain note>]]
- Related: [[<verified existing note>]], <plain-text concept without a note yet>
- Children:
```

Append a scoped `## Notes written` entry. `<notes-dir>` is the vault-relative
configured notes directory (`NOTES_DIR` in `STUDY-PROTOCOL.md`, `Notes` by
default) — log the path actually written, not a hardcoded `Notes/`:

```markdown
## Notes written — <scope>

- <ISO datetime> - Wrote `<notes-dir>/<note-file>.md`.
- Full notes: <objective 1>, <objective 2>
- Gap stubs: <objective 3>
```

Update `## Unit progress` for the scope:

```markdown
| <scope> | quizzed | notes-written | pending |
```

Set frontmatter `status: notes-written` and append:

```markdown
- <ISO datetime> - Notes written for <scope>. Status: notes-written.
```

After the notes are written, show a concise `support-helper` menu in chat
whenever the assessed scope has `gap` stubs, unanswered `study-check` blocks, or
obvious follow-up work. This is a handoff inside `obsidian-study-loop`, not a new
study phase. Include only helper skills that are available in the current agent
environment; if skill discovery is unavailable, list these as protocol-supported
options and say "if available." Do not write this menu inside the study note or
any learner-edit region.

Use this shape, omitting unavailable bullets when availability is known:

```text
Available support-helpers:
- Research plan: `study-research-queries` can turn each gap into source types,
  search queries, and a capture checklist.
- Deep source review: `literature-review` can support formal, citation-backed
  research when a gap needs stronger sources.
- Advisory check: `study-consult-panel` can provide an optional read-only second
  opinion on uncertain sections before finalizing.
- Map refresh: `study-map` can refresh course maps after reviewed notes are
  ready to link.
- Note polish: `humanizer` and `portable-markdown` can clean reviewed prose and
  formatting after the learner's own gap work is checked.
```

Ask which support path the user wants next, or tell them they can fill the gaps
offline and return with "review my additions." Do not start a helper workflow
unless the user chooses it or has already asked for that help.

## Phase 6 - User Research

The user researches `gap` objectives offline and fills in content under the
placeholder. Do not do this work for the user unless explicitly asked.

At the start of a gap-filling exchange, repeat the available `support-helper`
menu when it would help the user choose the next action. Keep the default path as
offline learner research. If the user asks for help planning that research, use
`study-research-queries` to produce targeted search queries, preferred source
types, and a capture checklist. The output should help the user research the gap
without filling the note for them.

## Phase 7 - Review Additions

Trigger examples: "review my additions", "check my gap notes".

1. Read `_study/state.json`; if it is `null`, inspect `_study/sessions/` and
   use the most recent session only after telling the user what was recovered.
   Restore `_study/state.json` to that vault-relative session path before
   editing review output, unless the user says not to.
2. Open the notes listed in that session's `## Notes written` entry.
3. Find sections that had `<!-- gap:<objective-slug> -->` markers. If the marker
   was deleted, use the session assessment and objective heading to locate the
   former gap.
4. Prefer content between matching `<!-- learner-edit:start ... -->` and
   `<!-- learner-edit:end ... -->` boundaries when they exist. Treat an
   unchanged `Write here.` sentinel as unanswered. If boundaries are absent,
   fall back to the gap marker and objective heading.
5. Find `<!-- study-check:start ... -->` blocks. Review a block when at least one
   checkbox is selected or the field after a `<!-- learner-answer:<field> -->`
   marker no longer equals `Write here.`. Leave untouched checks pending. A
   changed field with no substance — a bare acknowledgement ("ok", "done",
   "idk"), or a fragment carrying no term, mechanism, or reasoning — is
   non-substantive: report it as such, leave the check pending, and do not
   score it. A string change is a presence signal, not evidence.
6. **Duplicate content resolution.** Before editing individual sections, scan the
   opened notes for content that repeats across sections. Not all repetition is
   duplication — purposeful cross-references and worked examples that serve
   different objectives are legitimate. Apply this procedure:
   - **Detect.** Identify sections where the same concept, term, or explanation
     appears in more than one place with different headings. Common patterns:
     an actor type covered in both a general-actor section and a dedicated
     deep-dive section; the same attack term defined in two separate sections
     under different headings; a scenario or mitigation explained in a concept
     section and repeated in a gap section.
   - **Classify.** Tag each overlap as `true duplicate`, `cross-reference`, or
     `partial overlap`:
     - `true duplicate`: identical or near-identical content in two sections
       (e.g., nation-state actor definition in both "High-resource actors" and
       "Nation-state actors").
     - `cross-reference`: one section briefly mentions a concept that belongs
       to another section (e.g., "least privilege" in "Threat actors" is a
       forward reference to the insider section). Leave it if it serves
       context; tighten to one sentence if verbose.
     - `partial overlap`: sections share related but distinct content (e.g.,
       "Coercion and attacker goals" lists motivations, and "Threat actors and
       motivations" also lists them). Consolidate only when the same facts or
       mechanisms are restated for the same purpose.
   - **Consolidate.** For each `true duplicate` or `partial overlap` that
     justifies merging:
     1. Identify the **anchor section** — the section whose learning outcome,
        key terms, or objective mapping is the best fit for the content.
     2. Move the full text (including key terms, exam focus, worked examples,
        `> [!TIP]` callouts, `study-check` blocks, and `gap` markers) from
        the duplicate section into the anchor section. Order merged content
        logically: anchor's original content first, then absorbed content.
     3. Preserve every `<!-- learner-edit: ... -->`, `<!-- gap: ... -->`,
        `<!-- study-check: ... -->`, and `<!-- learner-answer: ... -->`
        marker. Adjust the `scope` attribute in moved `study-check` markers
        if the anchor section's scope is different. If the anchor already has
        a key terms or exam focus subsection, append new entries rather than
        creating a duplicate sub-heading.
     4. Replace the vacated section heading with a single-line cross-reference
        pointing to the anchor section:
        ```markdown
        ## <old heading>
        See [[<anchor note>#<anchor section heading>]].
        ```
        Keep the cross-reference only when the original heading is likely to
        be looked up by the learner (e.g., a term or objective name). If the
        original heading was a gap section whose content has been absorbed,
        leave a `> [!TIP]` cross-reference instead of an `[!IMPORTANT]` gap
        stub so the learner knows the content was merged, not lost.
     5. If a `study-check` block was moved during consolidation, verify it
        still makes sense in the anchor context. Change the scenario or
        framing if the original section-specific framing no longer fits.
   - **Log every consolidation** in the review changelog. Use this format:
     ```markdown
     - <source-section>: CONSOLIDATED into <anchor-section>. Reason: <why>.
       Moved: <key terms, example, study-check, etc.>.
     ```
   - **Do not consolidate** when:
     - The overlap is intentionally pedagogical (the same concept presented
       differently for two learning outcomes — e.g., recall in one section,
       application in another).
     - A section is a legitimate sub-topic that deserves its own heading (e.g.,
       "APT" as a sub-type of nation-state actors with unique characteristics).
     - The user explicitly asked for both sections to remain separate.
     - The content is a `gap` stub with no user-submitted answer. These may
       be consolidated at the agent's discretion, but never at the cost of
       removing the learner-edit boundary.
7. Check the user's gap content for accuracy and completeness:
   - If correct, leave it and mark approved.
   - If wrong or incomplete, edit it to be correct and complete.
   - If unsure, add a `> [!WARNING]` callout rather than guessing.
   - Provenance gate: approved gap content must either name a source the user
     can point to (course material, vendor doc, RFC/NIST, reputable reference)
     or be flagged — tutor confidence at most `low` plus a `[!WARNING]` callout
     noting unverified provenance. Plausible-sounding prose with no source is a
     plausibility check, not a knowledge check; do not let it earn `solid`.
   - Replace the stale pending `[!IMPORTANT]` research callout after review. Keep
     the alert tag alone on its line and put the status on the next line:
     - `solid` or approved without edits → `[!TIP]`, body **Research reviewed — <date>**
     - corrected or still `partial` → `[!TIP]`, body **Research reviewed — corrections applied on <date>**
     - unresolved `gap` → `[!WARNING]`, body **More research needed — <date>**
   - Keep the `gap`, `learner-edit:start`, and `learner-edit:end` markers so the
     reviewed region remains traceable. Do not leave `RESEARCH NEEDED` above a
     section that has already been approved or corrected.
   - Check frontmatter, tags, `[[wikilinks]]`, and related/mind-map metadata for
     consistency with the rest of the vault.
   - Apply a light humanizer pass so the final note reads like durable study
     material, not an AI transcript.
8. Score each answered mastery check before editing the user's selections:
   - Accuracy or correctness: `0-2`
   - Context or application fit: `0-2`
   - Reasoning or explanation: `0-2`
   - Transfer, limitations, alternatives, or distractor rejection: `0-2`
   - `solid`: 7-8, `partial`: 4-6, `gap`: 0-3
9. After scoring, explain every false positive, false negative, and weak
   rationale. Preserve the user's original choices and answer text. Never
   replace the learner's text on `learner-answer` lines: corrections and model
   answers belong in the feedback callout, quoting the learner's original words
   when discussing them. Leave unanswered fields as `Write here.` and report
   them as pending instead of filling them in. Convert the
   reviewed task boxes to explicit **Selected** / **Not selected** lines only
   after recording the original choices and score.
   Place feedback after `#### Your confidence before review` and before the
   closing `study-check` marker, outside any learner-edit region. Use
   `[!TIP]` for `solid`, `[!TIP]` for `partial`, and `[!WARNING]` for `gap`:

```markdown
> [!TIP]
> **Review — <date> · Score <score>/8 (<solid|partial|gap>)**
> **What worked:** <specific evidence>
> **Correction:** <what was wrong or incomplete>
> **Why:** <reasoning or transfer explanation>
```

10. Append this changelog to the session file and print it in chat:

```markdown
## Review — <date>

- <objective>: EDITED — <what changed>. Reason: <why>.
- <objective>: APPROVED — no changes.
- <study-check-id>: <score>/8 — <solid|partial|gap>; tutor confidence <level>;
  learner confidence <level>; calibration <result>. <reasoning feedback>
```

    The session file holds the canonical changelog. When edits to the note were
    substantive, a brief dated `## Review — <date>` provenance section may also
    be appended at the end of the note, after a `---` rule; keep it shorter
    than the session entry and never contradicting it.

11. Record every answered check's score and mastery in the review changelog, and
   optionally roll it into `## Mastery evidence`. Recalculate tutor confidence for
   the objective from all available independent evidence. Do not rewrite the
   historical quiz assessment.
12. If no gap content changed and no applied check was answered, report that
    there is nothing new to review. Do not change frontmatter, unit progress, or
    the session log.
13. Status gates — set statuses only inside the step-15 ordered pass, never
    before it:
    - Note `status: reviewed` requires zero unreviewed gap placeholders and
      zero answered-but-unreviewed study-checks in that note (a reviewed gap
      may stay open under a `[!WARNING]` without blocking). Untouched
      optional checks stay pending and do not block the note, but note their
      count in the review changelog.
    - Session frontmatter `status: reviewed` and the closing session log entry
      (`- <ISO datetime> - Review completed. Status: reviewed.`) come at the
      end of the ordered pass, not here.
14. Keep `_study/state.json` pointing at the reviewed session. Do not clear the
   active pointer after review. The next agent should be able to see what was
   just reviewed and whether the user wants to continue, start the next unit, or
   start the next chapter.
15. Finish the bookkeeping in the same pass as the note edits — review feedback
    in a note with no matching session-side record means an interrupted review.
    Complete, in order: note feedback and callout swaps → note frontmatter
    (`status`, `updated`) → session `## Review — <date>` changelog → `## Unit
    progress` Review column set to `reviewed` for the scope → calibration
    rollup: count the scope's evidence rows by calibration and append one line
    to the session log (`- <ISO datetime> - Calibration: <n> well-calibrated,
    <n> overconfident, <n> underconfident, <n> unknown.`) → session frontmatter
    status → closing session log entry. Then cross-check: the note and the
    session file must tell the same story.
16. If, when a review starts, a note already contains review feedback newer
    than the session's last review entry, a previous review was interrupted.
    Reconstruct the missing session-side records from the evidence in the note
    (scores, dates, callouts) before doing new review work, and log the repair
    in the session log.

## Safety Rules

- Treat the vault as precious. Never delete or overwrite notes without asking.
- Keep `_study/state.json` valid JSON with exactly one active session or `null`.
- A reviewed session may remain active. This is expected and helps the next
  agent recover context.
- Never clear `active_session` after review unless the user explicitly asks to
  clear or close state.
- Log every status change in the session file.
- Never invent citations or facts.
- If unsure about a technical detail, add a `> [!WARNING]` callout.
- Keep notes in portable GFM Markdown per the `portable-markdown` skill: the five
  standard alerts only, HTML `<!-- ... -->` markers, and clean typography. Never
  emit Obsidian-only `%% ... %%` comments or custom callout types.
