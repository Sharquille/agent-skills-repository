# Study Protocol

This vault contains a reusable study workflow for agentic CLIs. The agent
reading this file is the tutor. Do not call any LLM API, request API keys, or
run a standalone study app except for explicit read-only advisory consults
allowed by this protocol. Read and write plain files in this Obsidian vault.

## Paths and Conventions

- `VAULT_PATH`: `<VAULT_PATH>`
- `STUDY_DIR`: `_study`
- `NOTES_DIR`: `<NOTES_DIR>`
- Session logs live in `_study/sessions/`.
- Generated visual-review artifacts live in `_study/visuals/`.
- Session-integrated research-dive workspaces live in `_study/research/`
  (created on first dive).
- `STUDY-MANUAL.md` at the vault root is the installed plain-language manual
  (agent-refreshed on protocol sync; do not hand-edit).
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
- `teach-complex-concepts` for a **teaching dive** when covered material has
  not clicked and the learner needs adaptive tutoring rather than another
  notes pass. Session-integrated per Mid-Session Deep Dives below:
  relevance-check the topic, persist under the deep-dive rules, and keep the
  mastery boundary.
- `evidence-research-loop` for a **research dive** when a question needs
  citation-audited, primary-source research. Session-integrated per
  Mid-Session Deep Dives below: the workspace roots at
  `_study/research/<YYYY-MM-DD>-<question-slug>/`, and the synthesis becomes
  citable provenance for gap fills — never mastery evidence.
- `literature-review` only for formal, citation-backed research. Routine
  certification notes should stay lighter.
- `study-consult-panel` (optional) for a read-only, advisory second opinion on a
  drafted section — MiMo v2.5 Pro for writing, Kimi K2.7 Code for technical
  accuracy — cross-checked to manage single-model bias. It may also run a single
  MiMo prose lane to clean learner answer grammar after grading. The agent stays
  the tutor and gatekeeper, verifies every claim, and re-applies
  `portable-markdown`.
- `study-map` to build the tiered map stack (Home index, chapter maps, section
  sub-maps, concept maps, tag-lens, prerequisite map) once the vault has more than
  one chapter. It is integrity-gated: every node, edge, and tag must resolve to a
  real note/tag/link, missing linkage is reported (not invented), and it writes
  only into `Maps/` — never `_study/` or note bodies.

Helper skills do not change the safety rules: do not invent facts or citations,
and do not add API keys.

The agent is the tutor and never outsources the teaching, quizzing, or grading
to an external LLM API. Two explicit, opt-in exceptions exist, and neither ever
becomes the tutor or grader: `study-consult-panel`, a read-only **advisory**
consult through the already-configured `opencode-consult` wrapper, including
bounded MiMo learner-answer grammar cleanup; and a session-integrated
**research dive**, where `evidence-research-loop` delegates source reading
through the same wrapper family under `agent-orchestra` governance. Neither
adds API keys, and both outputs are untrusted until the agent verifies them
against the source. If a wrapper or its provider is unavailable, proceed from
the agent's own draft.

## Status Values

Session frontmatter `status` must be one of:

- `studying`
- `quizzed`
- `notes-written`
- `reviewed`

The session status records the latest completed workflow stage, not
whole-session coverage. For a multi-scope session, `## Unit progress` is the
source of truth for which scopes were quizzed, written, and reviewed.

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

## Syncing This Protocol

If this vault may be stale relative to the source `obsidian-study-loop` skill,
ask the agent to run the skill's bundled sync helper in dry-run mode first.
The script lives in the installed skill directory, not in this vault — for
example `~/.claude/skills/obsidian-study-loop/scripts/`, or
`skills/productivity/obsidian-study-loop/scripts/` in the skills repository:

```text
<skill-dir>/scripts/sync_study_protocol.py <VAULT_PATH>
```

The helper compares the source template to this `STUDY-PROTOCOL.md` and prints a
diff. It updates only this protocol file when run with `--apply`; it does not
touch `Notes/`, `_study/state.json`, or `_study/sessions/`.

The vault's `STUDY-MANUAL.md` is agent-managed, not script-managed: after an
`--apply`, the agent refreshes it by re-copying the skill's
`references/manpage.md` with the banner comment (creating the file if
missing).

The helper always uses its bundled canonical template and permits only a notes
directory inside the resolved vault. Relative `--notes-dir` values resolve from
the vault root. It refuses a symlinked `STUDY-PROTOCOL.md` target and replaces a
regular protocol file atomically.

## Validating This Vault

Use the skill's bundled read-only validator after setup or sync, before
repairing an interrupted workflow, or whenever the note and session records may
disagree:

```text
<skill-dir>/scripts/validate_study_vault.py <VAULT_PATH>
```

The validator never edits the vault. It checks the `state.json` schema and
active-session boundary, required session frontmatter, canonical H2 group
ordering, duplicate headings, final `## Session log`, logged note paths,
balanced learner/study-check markers, duplicate study-check IDs, pending gaps
inside reviewed notes, answered checks that lack review feedback, and every
HTML file under `_study/visuals/` against the offline visual-artifact contract.
An unconsumed quiz-progress block is a warning because it may represent a valid
interrupted quiz; integrity violations are errors. It exits `0` when no errors
exist and `1` when errors require attention. Resolve errors through the normal
recovery workflow rather than expecting an automatic fix.

## Plain-Language Manual

The `obsidian-study-loop` skill bundles a plain-language companion manual
(`references/manpage.md`) and a read-only `scripts/study_man.py` script that
prints it whole, by topic, or as a topic list (`--list`). Topics cover the
quickstart, trigger phrases, the phase loop, disk layout, deep dives, scoring,
and a categorized helper-skill breakdown. This protocol stays authoritative —
if the manual and the protocol disagree, follow the protocol.

The first time a study action is handled in a conversation, mention once that
the manual exists ("ask for the study manual, or a topic like 'quiz' or 'deep
dives'"). When the user asks how something works, run the script and show the
relevant section instead of paraphrasing from memory. Do not paste the whole
manual unprompted, and do not repeat the mention every turn.

Presentation: the script's stdout is source text for the agent, not the
deliverable. A raw tool-output dump renders as terminal text and is not
acceptable presentation for a manual request. After running the script,
re-render the requested section in the chat reply as normal formatted
markdown so headings, tables, and emphasis display properly. For a
full-manual request, do not replay every topic: show the topic list plus the
one or two most relevant sections, then offer the rest by name. Outside chat
there are two human-native views: `study_man.py --pretty` renders a styled
terminal view (automatic on an interactive terminal; `--raw` forces plain
markdown), and the vault-installed `STUDY-MANUAL.md` copy renders fully in
Obsidian — point non-technical readers there.

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

## Learner Answer Grammar Cleanup

Learner grammar cleanup is a readability aid, not tutoring, grading, or answer
generation. Use it only when the user asks for grammar cleanup or when a review
workflow explicitly needs a readable copy of learner-produced text. The original
learner wording remains the evidence of learning.

Run the cleanup through `study-consult-panel`'s Learner-Answer Grammar Cleanup
Mode (MiMo prose lane) when available; that skill owns the bounded prompt and
invocation. If it is unavailable, do only a conservative local cleanup or skip
and report that the prose lane was unavailable.

Rules:

- **Materiality gate.** Insert a cleaned copy only when it fixes real spelling,
  grammar, or sentence flow. If the cleaned text matches the original apart
  from trivia (capitalization, terminal punctuation, formatting), add nothing
  for that field and log it as already clean. Never duplicate an already-clean
  answer.
- One cleaned line per field; never merge fields. Mirror the original line's
  field-label formatting, including bold labels.
- Never replace text on `<!-- learner-answer:* -->` lines or inside
  `<!-- learner-edit:start -->` / `<!-- learner-edit:end -->` boundaries.
- Score and calibrate mastery from the original learner answer only. A cleaned
  copy is not new evidence and must not improve a score.
- Add the cleaned copy immediately below the original field, outside any
  learner-owned boundary when possible:

```markdown
<!-- learner-answer-cleaned:<check-id>.<field> source=mimo date=<YYYY-MM-DD> -->
- **Grammar-cleaned:** <minimal corrected wording>
```

- For gap research inside learner-edit boundaries, place the cleaned copy in a
  review callout after the boundary instead of editing the learner-owned region.
- Preserve the learner's voice and uncertainty markers such as "I think",
  "maybe", and "not sure"; these are calibration evidence.
- Do not correct cybersecurity substance in the cleaned copy. Put technical
  corrections in review feedback callouts.
- Record the cleanup in the session review changelog or session log, including
  the source (`mimo` or `local`) and which fields were skipped as already clean.

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
   - Research-dive workspaces under `_study/research/`: report each as
     resumable (no `audit.md` yet — offer to resume at the first incomplete
     stage, naming the originating session and question), needs repair
     (`audit.md` has unresolved failures), or deliverable (audit clean).
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

Maintain this section order in the session file for the whole session
lifecycle, inserting each new block within its group rather than appending at
the end of the file:

1. frontmatter
2. `## Study content`
3. `## Unit progress`
4. `## Quiz progress — <scope>` blocks, in section order
5. `## Assessment — <scope>` blocks, in section order
6. `## Notes written — <scope>` blocks, in section order
7. `## Deep dive — <scope>` blocks, in section order
8. `## Review — <date>` blocks, oldest first
9. `## Mastery evidence` (optional)
10. `## Session log` (always last)

When a heading already exists, append under it instead of creating a duplicate
heading. Do not reorder an existing session file without user approval.

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
   - If scope filtering leaves zero eligible objectives (for example, the named
     section has no in-scope learning outcomes, or everything in scope is
     already assessed and the user asked only for new material), stop: report
     why nothing is quizzable, do not run an empty quiz, do not write an
     assessment, and ask for a different scope or an updated study packet.
5. Quiz thoroughly, covering every objective in scope. If `## Study content`
   exists, use the in-scope learning outcomes, key terms, labs, activities, and
   practice expectations as the quiz blueprint. Use certification exam objective
   mappings only to align question wording to the exam, not to introduce
   future-section content. Before the first question, start a disk-backed
   progress block in the session file so an interrupted quiz can resume:

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
6. Mix question formats:
   - Direct recall: "What does X stand for and what does it do?"
   - Fill-in-the-blank: "In ___ access control, permissions attach to roles, not users."
   - Conceptual or compare-contrast: "When would you choose X over Y, and why?"
   - One applied/scenario question per major objective where it makes sense.
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
11. Honor mid-quiz learner controls without corrupting the evidence. If the
   user asks for a hint, step down a short ladder one level per request:
   restate what the question is really asking, then direct attention to the
   relevant feature of the scenario, then recall the needed principle or a
   simpler analogous case. Never reveal the answer as a hint. If the user says
   "show me" or "skip", give the correct answer with reasoning and score only
   what the user produced before the reveal. Record `hint` or `revealed` in
   that question's progress line; a hint-assisted correct answer caps at
   `partial` for that evidence item and does not count as the independent
   applied item that `high` tutor confidence requires. If a mid-quiz deep dive
   reveals planned material, record it per Mid-Session Deep Dives:
   `- <ISO datetime> - Q<n> <objective> - deferred: revealed by deep dive`.
12. After each answer, tell the user what was right, what was wrong or missing,
   and the correct answer before moving on.
13. Keep enough notes during the quiz to assess each objective later.
14. When key terms are provided, include term-definition recall and at least one
   question requiring the user to distinguish similar terms. Also include at
   least one pure free-recall prompt per section — describe a scenario and ask
   the user to produce the term or mechanism with no candidate list in sight.
   Recognition among presented options is weaker evidence than production.
15. When certification objectives are provided, include questions that map the
   user's understanding back to those exam objectives.
16. When lab or simulator expectations are provided, include practical or
   scenario questions about what the user would do in that environment.
17. For applied questions, state a concrete subject or asset, situation or
    failure path, and relevant facts. Ask the user to explain why the answer or
    decision fits that context, not merely name a term.
18. When practical, ask for learner confidence before giving feedback. Score
    each answer with the universal 8-point rubric; the scores feed the required
    `## Assessment — <scope>` block in Phase 4 (the separate `## Mastery
    evidence` ledger stays optional).
19. Record the resolved scope for assessment and notes. Examples: `full-session`,
   `1.1`, `1.2 Security Controls`, or `1.3 Use the Simulator`.

## Optional Visual Review Artifact

Chat remains the exam-standard quiz and mastery path. HTML artifacts are
optional post-assessment study aids: they can help the learner see relationships
between concepts, but they never quiz, grade, ingest results, or write mastery
evidence.

Trigger examples: "make me a visual review for the current scope", "make an
HTML concept map for 2.3", "diagram this scope", "visualize the malware
taxonomy", or "make a comparison page for these controls".

Generate a visual review artifact only for the current active study scope after
a chat quiz, assessment, notes write, or review has established that scope. If
the user names a different scope, verify that it has already been assessed or
written before treating it as the artifact scope. If the requested scope has not
been assessed or written yet, explain that mastery remains chat-based and offer
to quiz first.

### Purpose and content

Use the artifact to visually reinforce concepts already covered in the current
scope. Useful formats include:

- Concept maps and relationship diagrams.
- Comparison tables for similar terms or controls.
- Process flows, timelines, and remediation ladders.
- Attack paths, supply-chain dependency maps, and taxonomy diagrams.
- Visual retrieval prompts such as unlabeled diagrams or "explain this flow"
  cues, without scoring or answer collection.

Every visual artifact must be self-contained offline HTML. Inline CSS, JS, and
SVG are allowed when they support the visual explanation. Do not add remote
scripts, stylesheets, fonts, images, telemetry, accounts, persistence, or
network calls.

### Approved tactile study surface (v2)

Use the tactile study surface as the default visual language, built from the
skill's bundled template (`references/tactile-study-surface/`; read its
`SPEC.md` before generating). This is a structural and typographic system,
not a skin:

- Build a deliberate study narrative: **orient -> map or classify -> contrast
  -> respond or apply -> retrieve**. Omit a stage only when the scope does not
  support it; never invent content to fill the sequence.
- Keep the stable page frame the template provides: sticky command bar with
  scope code and keyboard hints, scrollspy index rail, one strong thesis,
  numbered section panels, and the retrieval deck last. oklch tokens, system
  font stacks only, hard asymmetric shadows, one per-scope accent hue, light
  default with dark via `prefers-color-scheme` plus an in-memory toggle.
- Assemble with the template's `assemble.py` and a per-scope content module
  so every artifact carries byte-identical chrome; express content through
  the template's primitives (cards, flows, duos, vs pairs, tables, contrast
  callouts) rather than inventing new chrome.
- Use rich UI elements only when they carry study meaning. Do not add
  dashboard metrics, ornamental cards, generic hero chrome, or controls that
  do not change an explanatory view.
- Add a mind map only when the source contains real hierarchy, branching,
  ownership, taxonomy, or one-to-many relationships. Keep pairwise contrasts
  as comparison layouts and ordered material as a flow or timeline. Never
  force every scope into a mind map.
- Treat the source note and assessment as immutable content authority during a
  visual migration. Preserve every factual claim, distinction, example,
  limitation, scope boundary, and retrieval reference. Presentation may move;
  subject matter may not drift, disappear, or expand.
- Author non-trivial interaction logic in TypeScript (the template's
  `behaviors.ts` is the source of truth) and compile it with the TypeScript 7
  native compiler (`npx -y -p typescript@7 tsc --strict`) to a small classic
  inline JavaScript block before release; TypeScript, JSX, Tailwind, package
  runtimes, and build dependencies must not ship in the offline HTML. The
  deck's self-marks stay ephemeral: in-memory only, reset on reload, never
  stored, exported, scored, or written to mastery evidence.

Before migrating an existing artifact, inventory its headings, factual blocks,
comparisons, examples, and retrieval cues. After migration, compare the same
inventory and fail the migration if any source content is missing or altered.

This is a local-first, agent-agnostic vault artifact. Do not route it through a
Claude Artifact, cloud-hosted page, or Claude-specific workflow; write the
current-scope HTML directly into this vault.

### Generation rules

1. Keep the artifact scope locked to the assessed or written scope. Do not use a
   visual artifact to introduce future-section content.
2. Put the current scope in the page title and filename.
3. Write generated files to `_study/visuals/<YYYY-MM-DD>-<scope-slug>.html`.
4. Label the page visibly as "Visual review artifact - not an assessment".
5. Do not include quiz scoring, submit buttons, answer collection, automatic
   grading code, mastery ledger writes, or pass/fail language.
6. Visual retrieval prompts may ask the learner to recall or explain, but the
   artifact must not collect, score, store, or export answers.
7. Log generation under `## Session log`, for example:
   "Generated visual review artifact for 2.3 -> `_study/visuals/...html`."
8. For a redesign or in-place migration, log the visual-system change without
   implying new mastery evidence or a new assessment.

### Artifact contract and quality gate

When available, read `references/visual-review-standard.md` before generating
or overhauling visual artifacts. The following core contract is authoritative
even when that reference is unavailable:

- Use one logical `<h1>`, a `<main>` landmark, `<html lang>`, UTF-8 charset,
  viewport metadata, and a visible focus treatment for interactive elements.
- Give informative inline SVGs an accessible name with `aria-label` or
  `aria-labelledby`; mark decorative SVGs `aria-hidden="true"`.
- Reflow without losing information at 320 CSS pixels. A complex table or code
  sample may use a deliberately scrollable wrapper.
- If motion is present, include a `prefers-reduced-motion: reduce` override.
  Prefer native `<details>`/`<summary>` over custom JavaScript disclosures.
- Include `study-source`, `study-scope`, `study-generated`, and
  `study-visual-version` metadata. Source values are vault-local identifiers,
  never remote URLs. Use visual contract version `1`.
- Add `referrer=no-referrer` and a Content Security Policy that denies all
  default and network access. At minimum it must contain
  `default-src 'none'`, `connect-src 'none'`, `form-action 'none'`, and
  `base-uri 'none'`. Permit inline styles or classic inline scripts only when
  the page actually needs them; never permit a host or wildcard source.
- Do not use forms, inputs, textareas, selects, iframes, objects, embeds,
  external or relative resource links, inline event-handler attributes,
  module scripts, network APIs, browser storage, cookies, device APIs, dynamic
  imports, `eval`, or function constructors. Fragment links and inline
  `data:image/` resources are the only URL-bearing exceptions.
- Treat print styling as recommended, not a release gate. Treat browser console
  output as diagnostic because extensions can add unrelated messages.

Before logging or presenting a new or changed artifact, run:

```text
<skill-dir>/scripts/validate_study_vault.py <VAULT_PATH>
```

Any visual-artifact error blocks release. Fix the file and rerun the validator;
do not add an automatic fixer or weaken the contract to pass an artifact. Then
open the local file in a browser and visually inspect it at a wide and narrow
viewport. Confirm readable hierarchy, no clipped content, visible keyboard
focus, and no attempted network access. This browser pass is human-facing QA,
not mastery evidence.

### Mastery boundary

HTML visual artifacts are not evidence. Opening, completing, annotating, or
discussing a visual artifact does not change `## Assessment`, `## Unit progress`,
`## Mastery evidence`, note status, or session status.

If the learner wants to use a visual prompt as mastery evidence, run a normal
chat quiz or review exchange and score that learner-produced answer in the
session file. The canonical mastery path remains:

```text
chat quiz -> assessment -> notes/gaps -> review -> mastery evidence
```

Legacy files from the old HTML quiz flow may still exist in `_study/quizzes/`,
but new study-loop work should treat them as archival and should not generate,
read, score, or rely on HTML quiz results.

## Mid-Session Deep Dives

Chat quiz, assessment, notes, and review remain the canonical mastery path. A
**deep dive** is a mid-session learning activity run by a helper skill under
this protocol's persistence and mastery rules:

- **Teaching dive** — `teach-complex-concepts` runs its adaptive tutoring loop
  when covered material has not clicked and the learner needs more than
  another notes pass.
- **Research dive** — `evidence-research-loop` runs its citation-audited
  pipeline when a question needs primary sources rather than tutoring.

Trigger examples: "teach me X", "I don't get X", "go deeper on X", "walk me
through X properly", "research X with sources". The helper skills also detect
the reverse direction themselves: invoked directly while a study session is
active, they resolve the vault, check relevance, and run session-integrated
under these rules.

### Relevance resolution

Resolve the dive topic against the active session before writing anything:

1. Read `_study/state.json` and the active session's topic, objectives,
   `## Study content`, and unit progress. If no session is active, apply the
   Session Lifecycle and Recovery rules (inspect the latest session file and
   ask) before treating the dive as standalone.
2. Classify the topic:
   - `in-scope`: maps to an in-scope objective or section. Proceed, announcing
     the mapping in one line ("Deep dive on key stretching → 3.1
     Cryptography").
   - `adjacent`: same course or certification, but a different or future
     section. Confirm with one line before integrating. Scope Boundary Rules
     apply unchanged: a dive never unlocks quizzing or full notes for a future
     section.
   - `unrelated`: say so, then run the helper standalone with no vault writes,
     or offer a new session.
3. If the topic is ambiguous between two scopes, ask one clarifying question.

Relevance is agent judgment over the session file — topic, objectives, study
content, and existing note headings — not string matching. Do not add a
matching script.

### Running the dive

- Run the helper skill for real: invoke `teach-complex-concepts` or
  `evidence-research-loop` and follow its loaded workflow. Never imitate the
  helper from memory — a dive that paraphrases the pedagogy degrades into
  bare Q&A with feedback, which is quizzing, not teaching.
- Register separation: inside a teaching dive, the Phase 3 quiz rules
  (one-question-at-a-time scoring, answer withholding, hint caps) do not
  govern the conversation — the teaching skill's workflow does, end to end.
  The mastery boundary below already excludes mid-dive answers from
  evidence, so there is no evidence-protection reason to withhold teaching:
  set the learning target, anchor it in a concrete scenario, build the
  smallest useful model, give worked examples, and name precisely what the
  learner's answers got right or wrong. Diagnostic questions serve the
  teaching; they are not the teaching.
- Use the session as the learner profile: the session file already states
  the course, certification goal, in-scope objectives, and prior assessment
  evidence. Do not re-ask what it answers; calibrate the lesson from it and
  ask at most one genuinely missing diagnostic question.
- Teaching visuals: when a picture materially reduces abstraction — or the
  learner asks ("draw it", "visualize that") — draw it as a Mermaid fenced
  code block, the **only** embedded diagram format for teaching content;
  every other visual format (HTML, Excalidraw, images) routes to the
  post-assessment visual review artifact lane. For analogy-driven teaching
  prefer the **decouple/recouple pair**: the structure in the analogy's own
  labels, then the identical layout relabeled with the domain's real terms
  (one block with two subgraphs, or two adjacent blocks) — the unchanged
  shape carries the mapping, and both halves persist. Place a one-line
  plain-text description immediately before each block so the explanation
  survives even where Mermaid is not rendered. Before emitting, self-check
  the block (fence opens and closes, valid diagram type) and render it
  through the client's diagram renderer when one exists. Keep diagrams
  teachable: past roughly 20 nodes, split into smaller diagrams or escalate
  to the artifact lane. A corrected diagram replaces the prior version in
  the note; the dive entry notes the correction. Outside an active dive,
  "draw it" renders in chat only and persists nothing unless the learner
  asks to save it.

### Evidence collision check

Before starting a dive, sweep the in-scope evidence surfaces it could
contaminate:

- An unconsumed `## Quiz progress — <scope>` block covering the dive topic:
  finish or explicitly pause the quiz first. If the learner insists on diving,
  append a progress line for each affected planned objective —
  `- <ISO datetime> - Q<n> <objective> - deferred: revealed by deep dive` —
  and score only what the learner produced before the dive.
- Unanswered in-scope `study-check` blocks the dive would teach: offer the
  learner a quick pre-dive attempt (clean evidence). If declined, the check
  stays pending and its later answer is graded like a hint-assisted item
  (capped at `partial`).
- Pending in-scope gap stubs need no restriction — a dive is legitimate gap
  research. Note the stub in the dive entry; the learner still writes the fill
  in their own words and review scores it normally.

### Persistence

- Session file: record every dive under a `## Deep dive — <scope>` block (one
  block per scope, dated entries appended, placed per the canonical section
  order):

```markdown
## Deep dive — <scope>

- <ISO datetime> — <helper skill> — <topic>
  - Trigger: <why the learner needed it>
  - Outcome: <what now clicks / what stays fragile — tutor observation only>
  - Persisted: `<notes-dir>/<note>.md` `### Deep dive — <topic> (<date>)` or
    `_study/research/<YYYY-MM-DD>-<question-slug>/`
  - Visuals: <n> Mermaid diagram(s) — "<title>" — embedded in the dive
    subsection (omit this line when no diagram was drawn)
  - Mastery: unchanged — re-quiz <offered|accepted|declined>, study-check
    <embedded|none>
```

  A second same-scope entry that revisits the same topic states whether it
  supersedes or complements the earlier entry.
- Notes: durable teaching content lands in the same section note under the
  relevant objective as `### Deep dive — <topic> (<date>)`, including any
  Mermaid diagrams drawn during the dive, so the note remains the illustrated
  explanation. When the note does
  not exist yet, follow the Phase 5 pre-draft rules first (vault search,
  peer-note `course`/`domain` formats, append-vs-new question when a note
  already covers the scope). When the objective's section is a gap
  placeholder, put the dive subsection after the `<!-- learner-edit:end -->`
  marker — never inside the learner-edit region, and never replacing the
  stub. Dive subsections are preserved verbatim by later consolidation unless
  the learner explicitly approves a merge.
- Research dives root their workspace at
  `_study/research/<YYYY-MM-DD>-<question-slug>/` (create the directory if
  missing). Every `evidence-research-loop` stage file and gate applies
  unchanged, including capture status and the citation audit. The synthesis
  is citable provenance for the learner's own gap fill — cite
  `_study/research/<slug>/synthesis.md` plus the named primary sources, which
  satisfies the Phase 7 provenance gate. If the user explicitly asks the
  agent to fill a gap from the research, label the fill
  `agent-filled on user request` in the dive entry and session log; the
  objective's mastery stays unchanged until the learner demonstrates it.
- Append a session-log line for every dive.

### Mastery boundary

- A dive never changes `## Assessment`, `## Unit progress`,
  `## Mastery evidence`, session frontmatter status, or note status.
- The teaching skill's internal mastery labels (emerging, developing, secure,
  transfer-ready) are tutor observations for the dive entry only. They are not
  8-point-rubric evidence and are not inputs to tutor-confidence or
  calibration calculations.
- Mid-dive learner answers are hint-saturated and never enter the rubric.
- Close every dive by offering the canonical follow-ups and recording the
  disposition in the dive entry: a short scoped re-quiz (normal Phase 3/4 with
  a new dated assessment block) or an embedded `study-check` for later review.
  A same-session post-dive re-quiz must use fresh question surfaces, and its
  evidence alone cannot raise tutor confidence to `high`; pair it with a later
  independent check, such as the objective's next-review date.

## Phase 4 - Assess

After the quiz is complete:

1. Grade each in-scope objective into exactly one bucket:
   - `solid` - The user demonstrated competence.
   - `partial` - The user got the gist but missed key details.
   - `gap` - The user could not recall it or got it materially wrong.
2. Append a scoped assessment heading in the active session file using
   this format:

```markdown
## Assessment — <scope>

- <objective 1>: solid (<score>) - <brief evidence from quiz> - next review <YYYY-MM-DD>
- <objective 2>: partial (<score>) - <brief evidence from quiz>
- <objective 3>: gap (<score>) - <brief evidence from quiz>
```

   Assessment and re-assessment records:

   - An objective whose supporting evidence is entirely recall or definition
     items is labeled `solid (recall-only)`, and its tutor confidence stays at
     most `medium` until at least one applied or transfer evidence item is
     recorded.
   - Give every `solid` objective a `next review` date: today + 7 days, or
     today + 21 days when tutor confidence is `high`. `partial` and `gap`
     objectives are re-tested through the normal loop and need no date.
   - If an `## Assessment — <scope>` block already exists for this scope, do
     not edit it. Create a new dated heading
     `## Assessment — <scope> — <YYYY-MM-DD>` so attempts stay distinguishable;
     the newest dated block is the current one.

3. If the scope is not the full session, do not imply that the entire session
   has been quizzed. Update or append a unit progress table. Keep exactly one
   row per scope — update the existing row in place on re-quiz or later phases;
   never add a duplicate row for the same scope:

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
`## Mastery evidence`. Finally, mark the scope's `## Quiz progress` block
consumed (`- Consumed by Assessment — <scope> on <ISO datetime>`).

## Phase 5 - Write Notes

After assessment, write markdown notes into `NOTES_DIR` for the assessed scope,
not necessarily the whole session. If the latest quiz covered only `1.1`, write
only the `1.1` note sections and gap stubs. If the latest quiz covered the full
session, write all assessed objectives.

Choose note granularity and names by these rules:

- When the course has numbered sections and quizzes run per section, default to
  **one note per section**, named `<Course short name> Ch<N> - <Section
  title>.md`, with frontmatter `section` set to that section's number.
  Example:

```text
Notes/Security+ Ch3 - Access Control.md
```

- Use a single chapter- or topic-wide note only when the session is one
  unsectioned topic.
- If an existing note already covers the chapter and a new section is about to
  be written, ask whether to append the new section to that note or start a
  per-section note. Never fork a second note for the same scope.
- Do not add an H1 title line to note bodies. The filename and frontmatter
  `title` carry the display name; body headings start at `##`.

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
> **Prompt:** <one or two self-contained sentences posing the exact question to
> research — what to identify, compare, sequence, or explain. State the task in
> full so this stub stands alone without the quiz, and never supply the answer.>
>
> Research and fill this in yourself below, then run a review. Replace the
> `Write here.` sentence, but keep the boundary comments.

<!-- gap:<objective-slug> -->
<!-- learner-edit:start id=gap-<objective-slug> -->
Write here.
<!-- learner-edit:end id=gap-<objective-slug> -->
```

The `**Prompt:**` line is mandatory and makes the stub self-contained: a learner
reading only this section must know exactly what to research without seeing the
quiz. Derive it from the specific quiz question that was missed, or the
section's learning outcome, and restate it as one or two declarative or
question-shaped sentences ("Which…?", "What…?") that preserve the original
cognitive demand — if the quiz asked the learner to identify vectors, the prompt
asks them to identify vectors, not merely define a term. Never embed the answer
or the exact term being tested (do not write "explain how macro-enabled Office
documents spread malware" when that document type is the answer). An
objective-name heading alone is not a prompt.

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
- Use industry-standard cybersecurity terminology in headings, preferring the
  exact terms used in the relevant certification objectives, course materials,
  NIST CSF, or MITRE ATT&CK (e.g. "threat actors" over "threat agents"). Avoid
  vague or generic headings that do not signal the specific concept.
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
   objectives received full notes and which received gap stubs. `<notes-dir>`
   is the vault-relative configured notes directory (`NOTES_DIR` above,
   `Notes` by default) — log the path actually written, not a hardcoded
   `Notes/`:

```markdown
## Notes written — <scope>

- <ISO datetime> - Wrote `<notes-dir>/<note-file>.md`.
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
- Teaching dive: `teach-complex-concepts` can tutor a shaky concept adaptively;
  persisted as a deep dive without changing mastery.
- Research dive: `evidence-research-loop` can produce a citation-audited answer
  whose synthesis becomes citable provenance for a gap fill.
- Deep source review: `literature-review` can support formal, citation-backed
  research when a gap needs stronger sources.
- Advisory check: `study-consult-panel` can provide an optional read-only second
  opinion on uncertain sections before finalizing.
- Grammar cleanup: `study-consult-panel` can use MiMo to add minimal
  grammar-cleaned copies of learner answers after grading — only where the
  text materially differs — without changing the original evidence.
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
placeholder in the notes file. Keep the `<!-- gap:... -->` marker and matching
learner-edit boundaries so later review and recovery can locate the evidence.

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
   marker no longer equals `Write here.`. Leave untouched checks pending. A
   changed field with no substance — a bare acknowledgement ("ok", "done",
   "idk"), or a fragment carrying no term, mechanism, or reasoning — is
   non-substantive: report it as such, leave the check pending, and do not
   score it. A string change is a presence signal, not evidence.
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
   - Apply a light humanizing edit so the note reads like durable study
     material, not a transcript.
9. Score each answered mastery check before editing the user's selections:
   - Accuracy or correctness: `0-2`
   - Context or application fit: `0-2`
   - Reasoning or explanation: `0-2`
   - Transfer, limitations, alternatives, or distractor rejection: `0-2`
   - `solid`: 7-8, `partial`: 4-6, `gap`: 0-3
10. After scoring, explain every false positive, false negative, and weak
    rationale. Preserve the user's original choices and answer text. Never
    replace the learner's text on `learner-answer` lines: corrections and model
    answers belong in the feedback callout, quoting the learner's original
    words when discussing them. Leave unanswered fields as `Write here.` and
    report them as pending instead of filling them in. Convert the
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

If the user asked for grammar cleanup, apply the **Learner Answer Grammar
Cleanup** rules after scoring and before final bookkeeping. Add cleaned copies
only; do not replace the original learner answer text and do not let the cleaned
copy affect the score.

11. Append a changelog to the session file under this exact heading format:

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

12. Record every answered check's score and mastery in the review changelog, and
    optionally roll it into `## Mastery evidence`. Recalculate tutor confidence
    for the objective from all available independent evidence. Do not rewrite the
    historical quiz assessment.
13. If no gap content changed and no applied check was answered, report that
    there is nothing new to review. Do not change frontmatter, unit progress, or
    the session log.
14. Print the same changelog to the user.
15. Status gates — set statuses only inside the step-18 ordered pass, never
    before it:
    - Note `status: reviewed` requires zero unreviewed gap placeholders and
      zero answered-but-unreviewed study-checks in that note (a reviewed gap
      may stay open under a `[!WARNING]` without blocking). Untouched
      optional checks stay pending and do not block the note, but note their
      count in the review changelog.
    - Session frontmatter `status: reviewed` and the closing session log entry
      come at the end of the ordered pass, not here.
16. The closing session log entry uses this format:

```markdown
- <ISO datetime> - Review completed. Status: reviewed.
```

17. Keep `_study/state.json` pointing at the reviewed session. Do not clear the
    active pointer after review. The next agent should be able to see what was
    just reviewed and whether the user wants to continue, start the next unit,
    or start the next chapter.
18. Finish the bookkeeping in the same pass as the note edits — review feedback
    in a note with no matching session-side record means an interrupted review.
    Complete, in order: note feedback and callout swaps → note frontmatter
    (`status`, `updated`) → session `## Review — <date>` changelog → `## Unit
    progress` Review column set to `reviewed` for the scope → calibration
    rollup: count the scope's evidence rows by calibration and append one line
    to the session log (`- <ISO datetime> - Calibration: <n> well-calibrated,
    <n> overconfident, <n> underconfident, <n> unknown.`) → session frontmatter
    status → closing session log entry. Then cross-check: the note and the
    session file must tell the same story.
19. If, when a review starts, a note already contains review feedback newer
    than the session's last review entry, a previous review was interrupted.
    Reconstruct the missing session-side records from the evidence in the note
    (scores, dates, callouts) before doing new review work, and log the repair
    in the session log.

## Markdown Rules (portable)

- Use portable GFM markdown per the `portable-markdown` skill, not Obsidian-only
  syntax. Run its `scripts/lint.sh` on a note before considering it done.
- No H1 title line in note bodies; the filename and frontmatter `title` carry
  the display name.
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
- Verify heading anchors (`[[Note#Heading]]`, `[[#Heading]]`) against the
  target note's actual headings, and update anchor references whenever a
  heading is renamed or consolidated away.
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
  Gemini, or other LLM APIs directly; the only permitted external-model paths
  are the advisory `study-consult-panel` consult and an explicit
  session-integrated research dive through `evidence-research-loop`, and
  neither ever becomes the tutor or grader.
- Learner grammar cleanup never changes the original answer or learner-owned
  research text. MiMo output is advisory-only and must remain separate from
  graded evidence.

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
5. Write Notes creates the scope-appropriate per-section or topic note(s),
   writes complete sections for `solid` and `partial`, writes exact gap stubs
   for `gap`, sets `status: notes-written`, and shows the available
   `support-helper` menu when follow-up work exists.
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
13. Note frontmatter follows the field contract: one spelling of `course` and
    `domain` per course, `type` is `learning` or `reference`, the note status
    lifecycle is respected, and `updated` is bumped on every substantive edit.
14. After review, the note and session file agree: feedback in a note has a
    matching `## Review` changelog, an updated `## Unit progress` Review
    column, and a session log entry.
15. Learner text on `learner-answer` lines was never replaced; corrections
    live in feedback callouts.
16. Grammar-cleaned learner copies, when present, were added separately with a
    `learner-answer-cleaned` marker, only where the text materially differs
    from the original, and did not affect mastery scoring.
17. A visual review artifact, when generated, is post-assessment, scope-locked,
    self-contained offline HTML, visibly labeled as not an assessment, written
    to `_study/visuals/`, and logged in the session file. It contains no quiz
    scoring, answer collection, automatic grading code, mastery ledger writes,
    pass/fail state, telemetry, or network calls. Chat remains the only
    exam-standard mastery path.
18. A deep dive, when run, was relevance-checked against the active session,
    passed the evidence collision check, was recorded under
    `## Deep dive — <scope>` with a session log entry, persisted its durable
    content per the deep-dive rules, and changed no assessment, unit progress,
    mastery evidence, or status fields. Any post-dive mastery update came from
    a fresh scoped re-quiz or a reviewed study-check.
19. The read-only validator reports no integrity errors after setup, sync, or a
    completed recovery pass; any warning is understood and intentionally left
    open.
