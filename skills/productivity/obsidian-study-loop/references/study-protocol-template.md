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

## Helper Skills

When available, use these helper skills while following this protocol:

- `knowledge-capture-obsidian` for frontmatter, tags, `[[wikilinks]]`, MOC/index
  hygiene, and clean Obsidian note structure.
- `humanizer` for a final prose pass on completed `solid` and `partial` note
  sections. Keep technical reference notes neutral, direct, and accurate.
- `study-research-queries` when the user asks for help researching a gap. It
  should produce search queries and a source plan, not fill the gap note unless
  the user explicitly asks for that.
- `literature-review` only for formal, citation-backed research. Routine
  certification notes should stay lighter.
- `study-consult-panel` (optional) for a read-only, advisory two-model second
  opinion on a drafted section — MiMo v2.5 Pro for writing, Kimi K2.7 Code for
  technical accuracy — cross-checked to manage single-model bias. The agent
  stays the tutor and gatekeeper, verifies every claim, and re-applies
  `portable-markdown`.
- `study-map` to build the tiered map stack (Home index, chapter maps, section
  sub-maps, concept maps, tag-lens, prerequisite map) once the vault has more than
  one chapter. It is integrity-gated: every node, edge, and tag must resolve to a
  real note/tag/link, missing linkage is reported (not invented), and it writes
  only into `Maps/` — never `_study/` or note bodies.

Helper skills do not change the safety rules: do not invent facts or citations,
and do not add API keys.

The agent is the tutor and never outsources the teaching, quizzing, or grading
to an external LLM API. The single exception is `study-consult-panel`: an
explicit, opt-in, read-only **advisory** consult through the already-configured
`opencode-consult` wrapper. It adds no API keys, never becomes the tutor, and its
output is untrusted until the agent verifies it against the source. If that
wrapper or its provider is unavailable, proceed from the agent's own draft.

## Status Values

Session frontmatter `status` must be one of:

- `studying`
- `quizzed`
- `notes-written`
- `reviewed`

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


## Syncing This Protocol

If this vault may be stale relative to the source `obsidian-study-loop` skill,
ask the agent to run the skill's bundled sync helper in dry-run mode first:

```text
scripts/sync_study_protocol.py <VAULT_PATH>
```

The helper compares the source template to this `STUDY-PROTOCOL.md` and prints a
diff. It updates only this protocol file when run with `--apply`; it does not
touch `Notes/`, `_study/state.json`, or `_study/sessions/`.

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

Treat a table of contents, module outline, lesson list, or copied course menu as
a rough outline even if the user calls it "objectives." It is not a complete
study packet unless it includes at least one of these per-section expectation
types: learning outcomes/guiding questions, key terms with definitions,
certification exam objective mappings, or lab/simulator expectations.

When the user gives only a chapter/topic, objective list, course menu, or rough
outline, ask once for the per-section study content packet before creating any
session file or updating `_study/state.json`:

```text
Please paste the per-section breakdown if you have it: learning outcomes, key terms, certification objectives, and lab/simulator expectations. If you do not have it, say "skip" and I will create the session from the outline you already gave me.
```

If the user already included the study packet, or if the user says to skip it,
continue setup.

When creating the session:

1. Read `_study/state.json` first. If it points at an existing session, report
   the active topic and status. If the user is clearly starting a new study
   session, preserve the existing session file and ask for confirmation before
   replacing the active pointer.
2. Create a slug from the topic:
   - Lowercase the topic.
   - Replace spaces and punctuation with hyphens.
   - Collapse repeated hyphens.
   - Trim leading and trailing hyphens.
3. Create `_study/sessions/<YYYY-MM-DD>-<slug>.md`.
4. Write this exact frontmatter shape at the top:

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

5. Treat `objectives` as the top-level lesson or section objectives. If the user
   provided section numbers, preserve them in the objective names.
6. Add a structured study packet below the frontmatter when the user supplied
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

7. Add an audit entry below the frontmatter or below `## Study content`:

```markdown
## Session log

- <ISO datetime> - Session created. Status: studying.
```

8. Write `_study/state.json` so it points at the session file:

```text
{
  "active_session": "_study/sessions/<YYYY-MM-DD>-<slug>.md"
}
```

9. Confirm the objectives back to the user in one short list. If a study packet
   was captured, also confirm the section titles captured, but keep it brief.
10. Stop. Do not quiz the user yet.

## Phase 2 - Study Break

Nothing happens during the study break. The user closes the agent and studies
offline. The session survives because `_study/state.json` points to the active
session file on disk.

## Phase 3 - Quiz

Trigger examples:

- "I'm done"
- "Quiz me"
- "Ready for the quiz"
- "Quiz me on 1.1"
- "Quiz section 1.2"
- "Quiz Security Controls"
- "Quiz everything"

When the user asks to be quizzed:

1. Read `_study/state.json`.
2. If `active_session` is `null`, inspect `_study/sessions/*.md` for the most
   recent session. If one exists, report its topic, status, and latest unit
   progress, then ask whether to resume that session and restore the pointer.
   If no session exists, ask the user to start a study session first.
3. Load the active session file and read its `topic`, `status`, `objectives`,
   and any `## Study content`.
4. Resolve the quiz scope:
   - If the user says only "quiz me", "I'm done", or "ready for the quiz", quiz
     the full active session.
   - If the user names a section, chapter, objective number, or title, quiz only
     that matching scope.
   - If the user says "quiz everything", quiz the full active session.
   - If the requested scope is ambiguous, ask one clarifying question and do not
     start the quiz yet.
5. Quiz thoroughly, covering every objective in scope. If `## Study content`
   exists, use the in-scope learning outcomes, key terms, labs, activities, and
   practice expectations as the quiz blueprint. Use certification exam objective
   mappings only to align question wording to the exam, not to introduce
   future-section content.
6. Mix question formats:
   - Direct recall: "What does X stand for and what does it do?"
   - Fill-in-the-blank: "In ___ access control, permissions attach to roles, not users."
   - Conceptual or compare-contrast: "When would you choose X over Y, and why?"
   - One applied/scenario question per major objective where it makes sense.
7. Ask exactly one quiz question at a time. Do not list the full quiz or multiple
   lettered questions in one message. Keep the remaining questions as an
   internal queue.
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
   question requiring the user to distinguish similar terms.
14. When certification objectives are provided, include questions that map the
   user's understanding back to those exam objectives.
15. When lab or simulator expectations are provided, include practical or
   scenario questions about what the user would do in that environment.
16. For applied questions, state a concrete subject or asset, situation or
    failure path, and relevant facts. Ask the user to explain why the answer or
    decision fits that context, not merely name a term.
17. When practical, ask for learner confidence before giving feedback. Record
    each answer as mastery evidence using the universal 8-point rubric.
18. Record the resolved scope for assessment and notes. Examples: `full-session`,
   `1.1`, `1.2 Security Controls`, or `1.3 Use the Simulator`.

## Phase 4 - Assess

After the quiz is complete:

1. Grade each in-scope objective into exactly one bucket:
   - `solid` - The user demonstrated competence.
   - `partial` - The user got the gist but missed key details.
   - `gap` - The user could not recall it or got it materially wrong.
2. Append or update a scoped assessment heading in the active session file using
   this format:

```markdown
## Assessment — <scope>

- <objective 1>: solid (<score>) - <brief evidence from quiz>
- <objective 2>: partial (<score>) - <brief evidence from quiz>
- <objective 3>: gap (<score>) - <brief evidence from quiz>
```

3. If the scope is not the full session, do not imply that the entire session
   has been quizzed. Update or append a unit progress table:

```markdown
## Unit progress

| Scope | Quiz | Notes | Review |
|---|---|---|---|
| <scope> | quizzed | pending | pending |
```

4. Set frontmatter `status: quizzed` when the full session has been quizzed or
   when at least one scoped quiz has completed and the latest action is quiz
   assessment. The scoped assessment heading and unit progress table are the
   source of truth for which units were actually covered.
5. Append an audit entry:

```markdown
## Session log

- <ISO datetime> - Quiz completed for <scope>. Status: quizzed.
```

If `## Session log` already exists, append the new bullet under the existing
heading instead of creating a duplicate heading.

Record each objective's score and mastery in the `## Assessment — <scope>` block
using the universal 8-point rubric (apply the recall exception for definition
items). Use `unknown` learner confidence when confidence was not collected.
Calculate tutor confidence from all evidence currently available for that
objective, not from the newest answer alone. Optionally roll the result into
`## Mastery evidence`.

## Phase 5 - Write Notes

After assessment, write markdown notes into `NOTES_DIR` for the assessed scope,
not necessarily the whole session. If the latest quiz covered only `1.1`, write
only the `1.1` note sections and gap stubs. If the latest quiz covered the full
session, write all assessed objectives.

Use one note file per session topic. Example:

```text
Notes/Security+ - Ch3 - Access Control.md
```

Before writing:

1. Determine the intended note path from the topic.
2. Search the vault for existing notes about the topic, key terms, and related
   concepts. Avoid duplicate notes.
3. Build a short list of verified existing note basenames that may be linked.
   Do not add `[[wikilinks]]` for concepts that are not on this verified list
   unless the user explicitly asked for future concept pages.
4. If `NOTES_DIR` does not exist, create it.
5. If the notes file already exists, do not overwrite it silently. Ask the user
   whether to append a new dated section or update in place.

New notes must begin with frontmatter in this shape:

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

Use lower-case kebab-case tags. If the vault already has a visible tag style,
match it.

For each assessed in-scope objective, write one `##` section.

For `solid` objectives:

- Write complete, accurate notes.
- Use portable GFM markdown (see the `portable-markdown` skill): the five standard
  alerts only, HTML `<!-- ... -->` markers, and clean typography.
- Include in-scope key terms and certification objective mappings from
  `## Study content` when they are anchored to the current section's learning
  outcomes.

For `partial` objectives:

- Write complete, accurate notes.
- Add a `> [!TIP]` callout flagging the specific detail the user was shaky on.
- Include in-scope key terms and certification objective mappings from
  `## Study content` when they are anchored to the current section's learning
  outcomes.

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

If a certification mapping points to a later section, add at most a short
forward reference instead of full notes.

For applied examples, replace vague claims with the full context chain: asset,
situation, relevant facts, answer or decision, fit, and limitation. Add a
`study-check` mastery exercise when application would reveal more understanding
than another definition question.

Do not use a heading for a short worked example. Keep it in an `[!NOTE]`
callout so it remains visible without competing with objective and subsection
headings in the outline.

For `gap` objectives, write only this placeholder:

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

The `<!-- gap:<objective-slug> -->` HTML comment is a machine marker. Do not
remove it during note writing. The learner-edit boundaries are user-owned space.
During review, preserve the user's original wording long enough to score it,
then make required corrections inside the same boundaries and record them in
the changelog. Never place tutor feedback inside the learner-edit region.

After drafting full sections, run a note quality pass:

- Remove chatbot phrasing such as "here is," "let's dive in," generic
  conclusions, inflated importance, and vague attributions.
- Prefer concise paragraphs, direct wording, and concrete examples.
- Keep heading weight proportional to structure: `##` for objectives, `###` for
  durable subsections, and callouts for short examples or feedback.
- Make every learner-editable location explicit. Use hidden HTML
  `<!-- ... -->` learner boundaries for research gaps and put each
  `learner-answer` marker on its own line above the mastery-check field.
- Preserve course wording for definitions and exam objectives when supplied.
- Do not cite sources unless a real source was consulted and can be named.
- If a technical detail is uncertain, add a `> [!WARNING]` callout instead of
  guessing.

Add discovery metadata near the end when useful:

```markdown
## Related

- [[<verified existing related note>]]

## Mind map seeds

- Parent: [[<verified existing course or domain note>]]
- Related: [[<verified existing note>]], <plain-text concept without a note yet>
- Children:
```

After writing notes:

1. Append a scoped `## Notes written` entry to the session log listing which
   objectives received full notes and which received gap stubs:

```markdown
## Notes written — <scope>

- <ISO datetime> - Wrote `Notes/<note-file>.md`.
- Full notes: <objective 1>, <objective 2>
- Gap stubs: <objective 3>
```

2. Update `## Unit progress` for the scope:

```markdown
| <scope> | quizzed | notes-written | pending |
```

3. Set frontmatter `status: notes-written`.
4. Append an audit entry under `## Session log`:

```markdown
- <ISO datetime> - Notes written for <scope>. Status: notes-written.
```

5. Show a concise `support-helper` menu in chat whenever the assessed scope has
   `gap` stubs, unanswered `study-check` blocks, or obvious follow-up work. This
   is a handoff inside `obsidian-study-loop`, not a new study phase. Include only
   helper skills that are available in the current agent environment; if skill
   discovery is unavailable, list these as protocol-supported options and say "if
   available." Do not write this menu inside the study note or any learner-edit
   region.

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

The user researches `gap` objectives offline and fills in the content under the
placeholder in the notes file. The user may leave or delete the
`<!-- gap:... -->` marker.

Do not do this research for the user unless explicitly asked. The learning value
comes from the user filling the gap.

At the start of a gap-filling exchange, repeat the available `support-helper`
menu when it would help the user choose the next action. Keep the default path as
offline learner research. If the user asks for research help, use
`study-research-queries` when available to generate a focused plan with search
queries, preferred source types, and a capture checklist. Prefer official course
materials, exam objectives, standards bodies, vendor documentation, and reputable
technical references over generic SEO articles.

## Phase 7 - Review

Trigger examples:

- "Review my additions"
- "Check my gap notes"
- "Review the notes I filled in"

When the user asks for review:

1. Read `_study/state.json`.
2. If there is an active session, use it. If `active_session` is `null`, inspect
   `_study/sessions/` and use the most recent session only after telling the
   user what was recovered. Restore `_study/state.json` to that vault-relative
   session path before editing review output, unless the user says not to.
3. Open the notes file or files listed in that session's `## Notes written`
   entry.
4. Find every section that previously had a `<!-- gap:<objective-slug> -->`
   marker.
5. Prefer content between matching `<!-- learner-edit:start ... -->` and
   `<!-- learner-edit:end ... -->` boundaries when they exist. Treat an
   unchanged `Write here.` sentinel as unanswered.
6. If the marker or boundaries were deleted, use the session assessment and
   objective heading to find the section that was formerly a gap.
7. Find `<!-- study-check:start ... -->` blocks. Review a block when at least one
   checkbox is selected or the field after a `<!-- learner-answer:<field> -->`
   marker no longer equals `Write here.`. Leave untouched checks pending.
7.5. **Duplicate content resolution.** Before editing individual sections, scan the
   opened notes for content that repeats across sections. Not all repetition
   is duplication — purposeful cross-references and worked examples that
   serve different objectives are legitimate. Apply this procedure:
   - **Detect.** Identify sections where the same concept, term, or
     explanation appears in more than one place with different headings.
     Common patterns: an actor type covered in both a general-actor section
     and a dedicated deep-dive section; the same attack term defined in two
     separate sections under different headings; a scenario or mitigation
     explained in a concept section and repeated in a gap section.
   - **Classify.** Tag each overlap as `true duplicate`, `cross-reference`,
     or `partial overlap`:
     - `true duplicate`: identical or near-identical content in two
       sections (e.g., nation-state actor definition in both
       "High-resource actors" and "Nation-state actors").
     - `cross-reference`: one section briefly mentions a concept that
       belongs to another section (e.g., "least privilege" in
       "Threat actors" is a forward reference to the insider section).
       Leave it if it serves context; tighten to one sentence if verbose.
     - `partial overlap`: sections share related but distinct content
       (e.g., "Coercion and attacker goals" lists motivations, and
       "Threat actors and motivations" also lists them). Consolidate
       only when the same facts or mechanisms are restated for the same
       purpose.
   - **Consolidate.** For each `true duplicate` or `partial overlap` that
     justifies merging:
     1. Identify the **anchor section** — the section whose learning
        outcome, key terms, or objective mapping is the best fit for the
        content.
     2. Move the full text (including key terms, exam focus, worked
        examples, `> [!TIP]` callouts, `study-check` blocks, and `gap`
        markers) from the duplicate section into the anchor section.
        Order merged content logically: anchor's original content first,
        then absorbed content.
     3. Preserve every `<!-- learner-edit: ... -->`, `<!-- gap: ... -->`,
        `<!-- study-check: ... -->`, and `<!-- learner-answer: ... -->`
        marker. Adjust the `scope` attribute in moved `study-check`
        markers if the anchor section's scope is different. If the anchor
        already has a key terms or exam focus subsection, append new
        entries rather than creating a duplicate sub-heading.
     4. Replace the vacated section heading with a single-line
        cross-reference pointing to the anchor section:
        ```markdown
        ## <old heading>
        See [[<anchor note>#<anchor section heading>]].
        ```
        Keep the cross-reference only when the original heading is likely
        to be looked up by the learner (e.g., a term or objective name).
        If the original heading was a gap section whose content has been
        absorbed, leave a `> [!TIP]` cross-reference instead of an
        `[!IMPORTANT]` gap stub so the learner knows the content was
        merged, not lost.
     5. If a `study-check` block was moved during consolidation, verify
        it still makes sense in the anchor context. Change the scenario
        or framing if the original section-specific framing no longer
        fits.
   - **Log every consolidation** in the review changelog. Use this format:
     ```markdown
     - <source-section>: CONSOLIDATED into <anchor-section>. Reason: <why>.
       Moved: <key terms, example, study-check, etc.>.
     ```
   - **Do not consolidate** when:
     - The overlap is intentionally pedagogical (the same concept
       presented differently for two learning outcomes — e.g., recall in
       one section, application in another).
     - A section is a legitimate sub-topic that deserves its own heading
       (e.g., "APT" as a sub-type of nation-state actors with unique
       characteristics).
     - The user explicitly asked for both sections to remain separate.
     - The content is a `gap` stub with no user-submitted answer. These
       may be consolidated at the agent's discretion, but never at the
       cost of removing the learner-edit boundary.
8. For each researched gap section, check the user's content for accuracy and
   completeness against the objective:
   - If correct and complete, leave it unchanged and mark it approved.
   - If wrong or incomplete, edit it to be correct and complete.
   - If uncertain about a technical detail, do not guess. Add a
     `> [!WARNING]` callout explaining what needs verification.
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
   - Apply a light humanizing edit so the note reads like durable study
     material, not a transcript.
9. Score each answered mastery check before editing the user's selections:
   - Accuracy or correctness: `0-2`
   - Context or application fit: `0-2`
   - Reasoning or explanation: `0-2`
   - Transfer, limitations, alternatives, or distractor rejection: `0-2`
   - `solid`: 7-8, `partial`: 4-6, `gap`: 0-3
10. After scoring, explain every false positive, false negative, and weak
    rationale. Preserve the user's original choices and answer text. Convert the
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
11. Append a changelog to the session file under this exact heading format:

```markdown
## Review — <date>

- <objective>: EDITED — <what changed>. Reason: <why>.
- <objective>: APPROVED — no changes.
- <study-check-id>: <score>/8 — <solid|partial|gap>; tutor confidence <level>;
  learner confidence <level>; calibration <result>. <reasoning feedback>
```

12. Record every answered check's score and mastery in the review changelog, and
    optionally roll it into `## Mastery evidence`. Recalculate tutor confidence
    for the objective from all available independent evidence. Do not rewrite the
    historical quiz assessment.
13. If no gap content changed and no applied check was answered, report that
    there is nothing new to review. Do not change frontmatter, unit progress, or
    the session log.
14. Print the same changelog to the user.
15. Set frontmatter `status: reviewed`.
16. Append an audit entry under `## Session log`:

```markdown
- <ISO datetime> - Review completed. Status: reviewed.
```

17. Keep `_study/state.json` pointing at the reviewed session. Do not clear the
    active pointer after review. The next agent should be able to see what was
    just reviewed and whether the user wants to continue, start the next unit,
    or start the next chapter.

## Markdown Rules (portable)

- Use portable GFM markdown per the `portable-markdown` skill, not Obsidian-only
  syntax. Run its `scripts/lint.sh` on a note before considering it done.
- Use `##` headings for objective sections.
- Use `###` only for durable subsections. Format short worked examples as
  `[!NOTE]` callouts and review feedback as mastery-appropriate callouts.
- Use only the five GFM-standard alerts — `> [!NOTE]`, `> [!TIP]`,
  `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]` — with the tag alone on its
  line. Never use custom callout types (`[!example]`, `[!question]`, …).
- Keep hidden HTML `<!-- ... -->` `learner-edit` boundaries and `learner-answer`
  markers intact so the user and future review agents can identify exactly where
  answers belong. Never use Obsidian `%% ... %%` comments.
- Use `[[wikilinks]]` only after verifying that the target note already exists
  in the vault. If the target note does not exist, use plain text instead.
- Use lower-case kebab-case tags and keep them consistent across the course.
- Add `## Related` and `## Mind map seeds` when they help future graph or mind
  map views.
- Never invent citations or facts.
- If unsure about a technical detail, flag it in a `> [!WARNING]` callout
  instead of guessing.

## Safety Rules

- Never delete notes unless the user explicitly asks.
- Never overwrite an existing notes file silently.
- Append to existing `CLAUDE.md`, `AGENTS.md`, and `GEMINI.md`; do not clobber
  them.
- Keep `_study/state.json` valid JSON at all times.
- Keep one active session pointer or `null`.
- A reviewed session may remain active. This is expected and helps the next
  agent recover context.
- Never clear `active_session` after review unless the user explicitly asks to
  clear or close state.
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
   `partial`, writes exact gap stubs for `gap`, sets `status: notes-written`,
   and shows the available `support-helper` menu when follow-up work exists.
6. User Research happens offline unless the user chooses a helper path from the
   `support-helper` menu.
7. Review reopens the written notes, checks the former gap sections, appends the
   required changelog, sets `status: reviewed`, and keeps `_study/state.json`
   pointed at the reviewed session.
8. Any timestamp written to frontmatter or the session log came from the system
   date command, not from a guessed or placeholder value.
9. Every `[[wikilink]]` in newly written notes resolves to an existing note, or
   the user explicitly asked for future concept-page links.
10. Every applied example uses the topic-appropriate context chain and explains
    why the answer fits.
11. Every answered learner-produced example is scored in the `## Assessment`
    block or review changelog (optionally rolled into `## Mastery evidence`) and
    contributes to mastery and confidence.
12. Answered `study-check` blocks are scored during review without changing the
    user's checkbox selections before grading.
