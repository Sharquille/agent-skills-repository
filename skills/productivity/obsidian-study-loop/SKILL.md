---
name: obsidian-study-loop
description: "Run or install a disk-backed Obsidian study workflow where the agent acts as tutor without calling external LLM APIs except explicit read-only advisory consults. Use when the user wants to set up STUDY-PROTOCOL.md in an Obsidian vault, start a study session from objectives or per-section study content, quiz a full session or scoped unit, assess objective mastery, write tagged notes with gap placeholders and applied exercises, generate optional self-contained offline HTML review artifacts for assessed scopes, run relevance-checked mid-session deep dives that route teach-complex-concepts tutoring or evidence-research-loop research into the session under a strict mastery boundary, review learner additions, or grammar-clean learner answers while preserving the original evidence. Do not trigger for generic note capture, one-off quizzes the user does not want persisted, general Obsidian administration, flashcard export, or standalone app/API-based study tools."
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
add API keys. The exception is the optional `study-consult-panel`, an explicit,
opt-in, read-only **advisory** second opinion through the existing
`opencode-consult` wrapper — including a bounded MiMo prose lane for learner
answer grammar cleanup. It adds no keys, never becomes the tutor, and its output
is untrusted until the agent verifies it. Session-integrated research dives
(`evidence-research-loop`) likewise delegate only source reading through the
same wrapper family, never the tutoring.

Use Obsidian file conventions from `knowledge-capture-obsidian` when that skill
is available, but keep this workflow focused on tutoring: session setup, study
break, quiz, assessment, notes, user research, and review.

When installing the workflow into a vault, use `scripts/install_study_loop.py`.
It renders `references/study-protocol-template.md` into `STUDY-PROTOCOL.md`
without replacing existing study state or documents. Do not reconstruct the
protocol from memory when the bundled template is available.

This SKILL.md and `references/study-protocol-template.md` intentionally carry
the same workflow: the template is what gets installed into vaults. Any change
to shared workflow content must be made in both files, and installed vaults
then need `scripts/sync_study_protocol.py <VAULT_PATH>` (dry-run, then
`--apply`) to pick it up. Contract-sensitive blocks use matching
`shared-contract` markers and are tested byte-for-byte to prevent silent drift.

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
- `teach-complex-concepts`: run a **teaching dive** when covered material has
  not clicked and the learner needs adaptive tutoring rather than another notes
  pass. Session-integrated per Mid-Session Deep Dives below: relevance-check the
  topic, persist under the deep-dive rules, and keep the mastery boundary.
- `evidence-research-loop`: run a **research dive** when a question needs
  citation-audited, primary-source research. Session-integrated per Mid-Session
  Deep Dives below: the workspace roots at
  `_study/research/<YYYY-MM-DD>-<question-slug>/`, and the synthesis becomes
  citable provenance for gap fills — never mastery evidence.
- `literature-review`: use only for formal, citation-backed deep research. It is
  too heavy for routine certification notes.
- `study-consult-panel`: an optional advisory panel for high-stakes or uncertain
  notes. It routes prose to MiMo v2.5 Pro and technical accuracy to Kimi K2.7
  Code (read-only, via `opencode-consult`), then cross-checks them to manage
  single-model bias. It may also run a single MiMo prose lane to clean learner
  answer grammar after grading. Consult at the section level before finalizing;
  you remain the gatekeeper and re-apply `portable-markdown`. Skip silently if
  the opencode CLI or OpenRouter is unavailable.
- `study-map`: once the vault has more than one chapter, build the tiered map
  stack (Home index, chapter maps, section sub-maps, concept maps, tag-lens,
  prerequisite map). It is integrity-gated — every node, edge, and tag must
  resolve to a real note/tag/link, and missing linkage is reported, not invented.
  It writes only into `Maps/` and never touches `_study/` or note bodies. Refresh
  affected maps when a chapter reaches `reviewed`.

Helper skills never replace the safety rules in this workflow. Do not add API
keys and do not invent citations or facts. Do not outsource teaching, quizzing,
or grading to an external LLM API. External-model calls are permitted only for
the explicit, read-only, advisory `study-consult-panel` consult and for an
explicit session-integrated research dive, where `evidence-research-loop`
delegates source reading under `agent-orchestra` governance; both outputs are
untrusted until the agent verifies them, and neither ever becomes the tutor or
grader.

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
3. After the vault is resolved, use the idempotent installer for missing
   vault-local scaffolding. Use the sync helper—not setup—to refresh installed
   protocol or manual copies.
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
  STUDY-MANUAL.md                      # installed manual copy (refreshed on sync)
  CLAUDE.md / AGENTS.md / GEMINI.md    # pointer blocks only
  Notes/                               # study notes; this skill writes here
  Maps/                                # study-map output; never written here
  _study/
    state.json                         # active-session pointer
    sessions/                          # one file per study session
    visuals/                           # generated visual-review .html artifacts
    dives/                             # teaching-dive notes (created on first dive)
    research/                          # research-dive workspaces (created on first dive)
    workpages/                         # note-refresh history archives (created on first refresh)
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

The helper synchronizes both `STUDY-PROTOCOL.md` and the installed
`STUDY-MANUAL.md` copy from bundled sources. It must not touch `Notes/`, pointer
files, `_study/state.json`, or `_study/sessions/`.

The helper always uses its bundled canonical template and permits only a notes
directory inside the resolved vault. Relative `--notes-dir` values resolve from
the vault root. It refuses a symlinked `STUDY-PROTOCOL.md` target and replaces a
regular protocol file atomically so an interrupted write cannot leave a partial
protocol.

## Validate Existing Vault State

Use the bundled read-only validator after setup or sync, before repairing an
interrupted workflow, or whenever the note and session records may disagree:

```text
scripts/validate_study_vault.py <VAULT_PATH>
```

The validator never edits the vault. It checks state and session boundaries,
canonical H2 ordering, unique quiz attempts, planned/asked/scored/deferred
question records, attempt-to-assessment consumption, applicable score notation,
learner source markers, note/study-check integrity, and every visual artifact's
offline security contract. Asked-but-unscored questions and missing provenance
are warnings because they can represent valid interrupted or low-confidence
work; structural contradictions are errors. Resolve findings deliberately—do
not add an automatic fixer.

## Plain-Language Manual

`references/manpage.md` is a plain-language companion manual for learners:
quickstart, trigger phrases, the phase loop, disk layout, deep dives, scoring,
and a categorized helper-skill breakdown. The protocol stays authoritative —
if the manual and the protocol disagree, follow the protocol and fix the
manual in the same change.

Print it, whole or by topic, with the bundled read-only script:

```text
scripts/study_man.py            # full manual
scripts/study_man.py --list     # topics
scripts/study_man.py quiz       # one topic (id, alias, or keyword)
```

The first time this skill handles a study action in a conversation, mention
once that the manual exists ("ask for the study manual, or a topic like
'quiz' or 'deep dives'"). When the user asks how something works, run the
script and show the relevant section instead of paraphrasing from memory. Do
not paste the whole manual unprompted, and do not repeat the mention every
turn.

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

Session frontmatter `status` records the latest completed workflow stage, not
whole-session coverage. For a multi-scope session, `## Unit progress` is the
source of truth for which scopes were quizzed, written, and reviewed.

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

<!-- shared-contract:start id=mastery-scoring -->
## Mastery Evidence and Confidence

Use all learner-produced evidence, not only the final quiz score. Evidence
includes quiz answers, answered `study-check` blocks, learner-authored gap
research, lab decisions, and later review explanations.

For each evidence item, score only the dimensions that genuinely apply:

- Accuracy or correctness: `0-2`
- Context or application fit: `0-2`
- Reasoning or explanation: `0-2`
- Transfer, limitations, alternatives, or distractor rejection: `0-2`

Record both earned and applicable points as `<earned>/<possible applicable>`.
Applicable denominators are `2`, `4`, `6`, or `8`, matching the number of
rubric dimensions used; full applied evidence remains `/8`. Map the applicable
proportion to mastery: `solid` = at least 87.5%, `partial` = at least 50% but
below 87.5%, and `gap` = below 50%. A fully correct definition may therefore
be `2/2 applicable — solid (recall-only)`; never display it as `2/8`.

Each assessment objective selects one scored `evidence question: Q<n>` from
the linked attempt as its primary mastery evidence. Copy that question's raw
score, assistance, and learner confidence exactly; prefer the most diagnostic
unassisted item when one exists. The selected question controls the row's
numeric mastery and calibration. Other evidence may strengthen or weaken tutor
confidence and the evidence summary, but it does not replace that row's score.
Question kinds are a finite taxonomy: recall-only kinds are `recall`,
`definition`, `term-definition`, `free-recall`, `free-production`,
`fill-in-the-blank`, and `recognition`; applied-capable kinds are `application`,
`applied`, `scenario`, `compare-contrast`, `classification`, `discrimination`,
`transfer`, and `lab`. Reject any other kind. A numerically solid selected item
of a recall-only kind must be labeled `solid (recall-only)`, and an
applied-capable kind cannot use that label. With assistance `none`, mastery
follows the numeric band. Any `hint-*` or `revealed` evidence is capped at
`partial` even when its raw score is numerically solid. For `revealed`, score
only what the learner produced before the reveal—often a `gap`—never the shown
answer, and never record `solid`.

Keep two confidence signals separate:

- **Learner confidence**: Low, Medium, or High, selected before feedback; use
  `unknown` when the learner opts out or it was not collected.
- **Tutor confidence in mastery**:
  - `high`: at least two independent evidence items support mastery, including
    one applied or transfer item, with no unresolved critical misconception.
  - `medium`: evidence is limited, mixed, recall-only, or based on one strong item.
  - `low`: evidence is weak, contradictory, below the mastery threshold on its
    applicable denominator, or absent.

Calibration compares learner confidence with that evidence item's mastery band,
not with tutor confidence: `gap` maps to Low, `partial` to Medium, and `solid`
to High. Matching bands are `well-calibrated`; learner confidence above the
band is `overconfident`; below it is `underconfident`; missing confidence is
`unknown`. A `solid (recall-only)` answer may be well-calibrated while tutor
confidence remains capped at `medium`.

The `## Assessment — <scope> — attempt <attempt-id>` block is the canonical
record of the evidence question, raw score, assistance, mastery, tutor
confidence, learner confidence, calibration, retrieval stage, and next action.
A separate roll-up ledger is optional; it must summarize without contradicting
the assessment. Keep it lean:

```markdown
## Mastery evidence

| Date | Scope | Objective | Evidence | Score | Mastery | Confidence | Notes |
|---|---|---|---|---:|---|---|---|
| <date> | <scope> | <objective> | <quiz or study-check-id> | <earned>/<applicable> | <solid|partial|gap> | tutor <level>, learner <level|unknown>, <calibration> | <brief evidence> |
```

Historical evidence remains in the ledger. New evidence may update the current
tutor confidence, but must not rewrite what the learner originally answered.
<!-- shared-contract:end id=mastery-scoring -->

## Setup a Vault

When the user asks to install or set up the study loop, use the bundled
idempotent installer rather than hand-building the scaffold:

```text
scripts/install_study_loop.py <VAULT_PATH> [--notes-dir Notes]
```

It dry-runs by default and lists every proposed write. After the user has asked
to install and the plan is correct, apply it:

```text
scripts/install_study_loop.py <VAULT_PATH> [--notes-dir Notes] --apply
```

The installer enforces this setup contract:

- Resolve and display the exact vault and notes paths before applying.
- On a first install, create the protocol, manual, null state, pointer files,
  and missing `_study/` directories from bundled sources.
- On a repeat install, preserve every existing protocol, manual, state, note,
  session, dive, research workspace, visual, and pointer-file rule. Create only
  missing scaffold pieces.
- Create `{ "active_session": null }` only when `_study/state.json` is absent.
  If existing state is invalid or unsafe, stop; never reset it as repair.
- Append the study pointer block to `CLAUDE.md`, `AGENTS.md`, or `GEMINI.md`
  only when an equivalent block is absent.
- Refuse symlink escapes and notes directories outside the vault.

If an existing protocol may be stale, use the sync helper's dry run after
installation. Finish by running `scripts/validate_study_vault.py <VAULT_PATH>`.

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
     are on or before today. Offer to prepend at most 1-2 retrieval questions,
     prioritizing objectives that are confusable with each other or meaningfully
     related to the new scope. Record them under their original scopes, never in
     the new scope's grade. Persist the attempt in its originating session file
     without changing `active_session`. Do not randomly interleave unrelated
     material.
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

9. Offer one optional 1-2 minute prior-knowledge prompt tied to the scope,
   labeled **orientation — not a quiz**. Do not request confidence, score it,
   or use it as mastery evidence. Declining never blocks the study break. If
   completed, log only that activation occurred, not the learner's answer.
10. Confirm the objectives in one short list and close with the exact next
    action: study offline, then return with "quiz me". Do not quiz yet.

Maintain this section order in the session file for the whole session
lifecycle, inserting each new block within its group rather than appending at
the end of the file:

1. frontmatter
2. `## Study content`
3. `## Unit progress`
4. `## Quiz progress — <scope> — attempt <attempt-id>` blocks, in section order
5. `## Assessment — <scope> — attempt <attempt-id>` blocks, in section order
6. `## Notes written — <scope>` blocks, in section order
7. `## Deep dive — <scope>` blocks, in section order
8. `## Review — <date>` blocks, oldest first
9. `## Mastery evidence` (optional)
10. `## Session log` (always last)

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
<!-- shared-contract:start id=quiz-attempt -->
5. Build an adaptive question budget before asking anything. The minimum gives
   every eligible objective one scorable retrieval surface. The target adds an
   applied or discrimination prompt where it improves evidence. The maximum
   permits one clarification or fresh transfer prompt when evidence remains
   ambiguous. Tell the learner the estimated range; stop when evidence is
   sufficient and never ask filler questions.
6. Create a unique attempt ID from the local date plus a two-digit sequence,
   such as `2026-07-12-01`. Never reuse an ID. Persist one mutable record per
   question before the first prompt:

```markdown
## Quiz progress — <scope> — attempt <YYYY-MM-DD>-<NN>

- Budget: minimum <n>; target <n>; maximum <n>; mode adaptive
- Attempt status: active — updated: <ISO datetime>
- Q1 [recall] — <objective> — status: planned
- Q2 [application] — <objective> — status: planned
```

   Immediately before showing a question, replace its record with `status:
   asked` and its complete one-line prompt. After the learner responds, replace
   that same record with exactly one terminal `scored` or `deferred` state:

```markdown
- Q1 [recall] — <objective> — status: asked — prompt: <complete prompt>
- Q1 [recall] — <objective> — status: scored — prompt: <complete prompt> — score: 2/2 applicable — assistance: none — learner confidence: High — evidence: <brief evidence>
- Q2 [application] — <objective> — status: deferred — reason: <reason>
```

7. If `## Study content` exists, use the in-scope learning outcomes, key terms,
   labs, activities, and practice expectations as the blueprint. Certification
   mappings align wording but never introduce future-section material. Mix
   recall, compare-contrast, free production, and applied scenarios according
   to what each objective genuinely requires.
8. Ask exactly one question at a time. Do not display the full plan. The disk
   records—not chat memory—are the recovery point. On resume, first resolve an
   `asked` question, then continue with the earliest `planned` record.
9. Honor learner controls without corrupting evidence:
   - `pause`: set `Attempt status: paused` with the current timestamp; do not
     assess unfinished objectives.
   - `resume`: set the same attempt and ID back to `active`, update its
     timestamp, and continue.
   - `rephrase`: change wording only, update the stored prompt, and apply no
     hint penalty.
   - `shorter`: move toward the minimum by deferring optional prompts; retain at
     least one scorable item per objective unless the learner narrows scope.
   - `deeper`: add a planned discrimination or transfer prompt without
     expanding scope or exceeding the maximum without consent.
   - `hint`: step down one level per request—reframe, direct attention to a
     relevant feature, then recall the principle or a simpler analogue.
   - `show me` or `skip`: reveal the answer with reasoning and score only what
     the learner produced first.
10. Record assistance as `none`, `hint-1`, `hint-2`, `hint-3`, or `revealed`.
    Hint-assisted correct evidence is capped at `partial` and cannot satisfy the
    independent applied item required for high tutor confidence. A deep dive
    that reveals a planned answer changes the record to `deferred` with the
    reason `revealed by deep dive`.
11. Collect Low, Medium, or High learner confidence before feedback when
    practical. Ask once if omitted, honor opt-out, and store `unknown`.
12. After each answer, say what was right, what was missing, and the correct
    answer. A clarification probe may precede grading when the response is
    genuinely ambiguous; it must not teach the answer.
13. When the attempt is assessed, set its status to `completed`, then append the
    exact matching record:
    `- Consumed by Assessment — <scope> — attempt <attempt-id> on <ISO datetime>`.
    Never delete attempt history.
<!-- shared-contract:end id=quiz-attempt -->
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
18. Score each answer on its applicable denominator; the scores feed the
    attempt-scoped assessment in Phase 4. The separate mastery-evidence ledger
    remains optional.
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

Every visual artifact must be self-contained offline HTML. Inline CSS and JS
are allowed when they support the visual explanation. Do not add remote
scripts, stylesheets, fonts, images, telemetry, accounts, persistence, or
network calls.

### Approved tactile study surface (v2)

Use the tactile study surface as the default visual language, built from the
bundled template in `references/tactile-study-surface/` (read its `SPEC.md`
before generating). This is a structural and typographic system, not a skin:

- Build a deliberate study narrative: **orient -> map or classify -> contrast
  -> respond or apply -> retrieve**. Omit a stage only when the scope does not
  support it; never invent content to fill the sequence.
- Keep the stable page frame the template provides: sticky command bar,
  scrollspy index rail, one strong thesis, and numbered section panels. When
  honest retrieval cues exist, append the interactive deck last; otherwise
  omit it and produce a script-free static page.
- Assemble with `tactile-study-surface/assemble.py --vault <VAULT_PATH>
  <content.json> <VAULT_PATH>/_study/visuals/<slug>.html` and a declarative
  per-scope JSON manifest so every assembled artifact carries
  byte-identical chrome. The manifest is data, never executable code. Express
  content only through the assembler's validated primitives.
- The JSON assembler supports its documented semantic and CSS primitives and
  deliberately rejects SVG. If the source genuinely requires a concept-native
  SVG, author a separate offline artifact under the visual review standard;
  validate and browser-review it instead of placing SVG in `body_html`.
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
- Normal study-time generation uses the bundled reviewed `behaviors.js`; it
  must not invoke package managers or download build tools. `behaviors.ts` is
  maintainer source only and may be rebuilt during repository maintenance with
  an already-installed pinned compiler, followed by inspection and tests.
  TypeScript, JSX, runtimes, and build dependencies never ship in the HTML.
  The deck's self-marks stay ephemeral and never become mastery evidence.

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
3. Write generated files to `<VAULT>/_study/visuals/<YYYY-MM-DD>-<scope-slug>.html`.
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
- In a separately authored artifact, give informative inline SVGs an accessible
  name with `aria-label` or `aria-labelledby`; mark decorative SVGs
  `aria-hidden="true"`.
- Reflow without losing information at 320 CSS pixels. A complex table or code
  sample may use a deliberately scrollable wrapper.
- If motion is present, include a `prefers-reduced-motion: reduce` override.
  Prefer native `<details>`/`<summary>` over custom JavaScript disclosures.
- Include `study-source`, `study-scope`, `study-generated`, and
  `study-visual-version` metadata. `study-source` must be a vault-local POSIX
  path to an existing regular file inside the vault, never a remote URL. Use
  visual contract version `1`.
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
scripts/validate_study_vault.py <VAULT_PATH>
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
<!-- shared-contract:start id=teaching-evidence-boundary -->
- Use this teaching rhythm when it fits the concept: **orient → focused chunk →
  worked example → learner retrieval → corrective feedback → self-explanation
  or teach-back → later fresh transfer check**. Keep chunks small enough for the
  learner to manipulate, not merely reread.
- An immediate paraphrase, self-explanation, or teach-back after instruction or
  feedback is a learning activity, never mastery evidence. A later teach-back
  may count only when posed as a fresh, answer-withheld question through the
  normal quiz or study-check path. Score only that later response.
<!-- shared-contract:end id=teaching-evidence-boundary -->
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
  through the client's diagram renderer when one exists. Mermaid label syntax
  is strict and fails silently: a quoted label that **begins** with a list
  marker (`1.`, `1)`, `- `, `* `) is parsed as markdown and the whole label
  becomes `Unsupported markdown: list`, so prefix ordered steps with a word
  (`"Step 1 — Authorize"`, `"Panel 1 — ..."`); and use `<br/>` for line
  breaks. Layout direction is an authoring decision: when the surrounding
  prose names a reading direction, the diagram must match it — fix an
  overflowing `LR` chain by shortening labels, and change direction only when
  the prose is silent or is updated in the same edit. Keep diagrams teachable: past
  roughly 20 nodes, split into smaller diagrams or escalate to the artifact
  lane. A corrected diagram replaces the prior version in
  the note; the dive entry notes the correction. Outside an active dive,
  "draw it" renders in chat only and persists nothing unless the learner
  asks to save it.

### Evidence collision check

Before starting a dive, sweep the in-scope evidence surfaces it could
contaminate:

- An unconsumed `## Quiz progress — <scope> — attempt <attempt-id>` block
  covering the dive topic:
  finish or explicitly pause the quiz first. If the learner insists on diving,
  change each affected question record to `status: deferred — reason: revealed
  by deep dive` and score only what the learner produced before the dive.
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
  - Persisted: `_study/dives/<YYYY-MM-DD>-<topic-slug>.md` (teaching dive) or
    `_study/research/<YYYY-MM-DD>-<question-slug>/` (research dive)
  - Visuals: <n> Mermaid diagram(s) — "<title>" — embedded in the dive
    subsection (omit this line when no diagram was drawn)
  - Mastery: unchanged — re-quiz <offered|accepted|declined>, study-check
    <embedded|none>
```

  A second same-scope entry that revisits the same topic states whether it
  supersedes or complements the earlier entry.
- Teaching dives are decoupled from the canonical study notes. `Notes/`
  belongs to the mastery flow — only Phase 5 Write Notes, after a quiz and
  assessment, authors a study note there — and a dive never writes into
  `Notes/`. A teaching dive persists the distilled explanation and any Mermaid
  diagrams to `_study/dives/<YYYY-MM-DD>-<topic-slug>.md` (create the file and
  the `_study/dives/` directory if missing). Give it light frontmatter
  (`type: teaching-dive`, `scope`, `created`, `source: teaching-dive`), never
  the `type: learning` graded-note contract. The session `## Deep dive` entry
  points at this file. If the learner later wants dive content folded into a
  study note, that happens only through the mastery flow (Write Notes or
  Review), citing the dive note as a source — never by the dive writing
  `Notes/` directly.
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
  `## Mastery evidence`, session frontmatter status, or note status, and never
  writes a study note in `Notes/` — that directory is authored only by the
  mastery flow (Phase 5 Write Notes).
- The teaching skill's internal mastery labels (emerging, developing, secure,
  transfer-ready) are tutor observations for the dive entry only. They are not
  applicable-dimension evidence and are not inputs to tutor-confidence or
  calibration calculations.
- Mid-dive learner answers are hint-saturated and never enter the rubric.
- Close every dive by offering the canonical follow-ups and recording the
  disposition in the dive entry: a short scoped re-quiz (normal Phase 3/4 with
  a new attempt-scoped assessment block) or an embedded `study-check` for later review.
  A same-session post-dive re-quiz must use fresh question surfaces, and its
  evidence alone cannot raise tutor confidence to `high`; pair it with a later
  independent check, such as the objective's next-review date.

## Phase 4 - Assess

After the quiz, grade each in-scope objective:

- `solid` - The user demonstrated competence.
- `partial` - The user got the gist but missed key details.
- `gap` - The user could not recall it or got it materially wrong.

Record results under the exact attempt-scoped assessment heading:

```markdown
## Assessment — <scope> — attempt <attempt-id>

- <objective 1> — mastery: solid — evidence question: Q1 — score: 8/8 — assistance: none — evidence: <brief evidence> — tutor confidence: high — learner confidence: High — calibration: well-calibrated — review stage: 1 — next review: <YYYY-MM-DD>
- <objective 2> — mastery: solid (recall-only) — evidence question: Q2 — score: 2/2 applicable — assistance: none — evidence: <brief evidence> — tutor confidence: medium — learner confidence: High — calibration: well-calibrated — review stage: 1 — next review: <YYYY-MM-DD>
- <objective 3> — mastery: partial — evidence question: Q3 — score: 7/8 — assistance: hint-1 — evidence: <brief pre-hint production> — tutor confidence: medium — learner confidence: High — calibration: overconfident — next action: unassisted retrieval
```

For each objective, choose one scored question from the linked attempt as the
primary evidence. Prefer the most diagnostic unassisted question when one is
available, then copy its question ID, raw score, assistance, and learner
confidence exactly. Other answers inform tutor confidence and the evidence
summary without changing the selected row's score, calibration, or assistance
cap. Solid `recall`, `definition`, `term-definition`, `free-recall`,
`free-production`, `fill-in-the-blank`, and `recognition` questions use
`solid (recall-only)`; the applied-capable question kinds listed in the mastery
contract cannot use that label.

Assessment and re-assessment records:

<!-- shared-contract:start id=retrieval-schedule -->
- Label evidence supported only by recall or definitions `solid (recall-only)`;
  tutor confidence stays at most `medium` until an applied or transfer item is
  recorded.
- Use successive-relearning stages of approximately 1, 3, 7, 21, and 30 days
  after the latest successful unassisted retrieval. After stage 5, continue at
  least monthly and lengthen only after sustained success.
- A new or remediated `solid` starts at stage 1. Each successful unassisted
  retrieval advances one stage. Hint-assisted, revealed, `partial`, or `gap`
  evidence does not advance; after remediation, restart at stage 1.
- Write each re-review as a new attempt and assessment under the objective's
  original scope. Never rewrite historical assessments or fold a due warm-up
  into the new scope's grade. Reopen a gap stub only when new evidence is `gap`.
- Persist a due-item attempt and assessment in the originating session file,
  even when another session is active. Leave `_study/state.json` unchanged and
  add only a link-like session-log entry in the active session. If the origin is
  missing or ambiguous, defer the item and report the repair need.
- Example: while `Network Basics` is active, a due `Access Control` check from
  an older `Security Fundamentals` session is written to that older session;
  the active pointer stays on `Network Basics`, whose log names the warm-up and
  originating session.
- `partial` and `gap` receive a concrete `next action` rather than a review date
  until remediation produces a successful retrieval.
<!-- shared-contract:end id=retrieval-schedule -->

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

Record score, mastery, both confidence signals, calibration, and review stage or
next action in the attempt-scoped assessment. Calculate tutor confidence from
all available independent evidence, not the newest answer alone. Optionally
roll the result into `## Mastery evidence`. Finally, consume the exact attempt
with `- Consumed by Assessment — <scope> — attempt <attempt-id> on <ISO datetime>`.

When a re-quiz upgrades an objective on an already-reviewed note to `solid`, offer
the learner a note refresh (see Note Refresh on Re-quiz) so the study note reads as
clean current material with its prior scaffold archived, not as a record of past
gaps.

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
> **Prompt:** <one or two self-contained sentences posing the exact question to
> research — what to identify, compare, sequence, or explain. State the task in
> full so this stub stands alone without the quiz, and never supply the answer.>
>
> Research and fill this in yourself below, then run a review. Replace both
> `Write here.` fields, but keep the boundary comments.

<!-- gap:<objective-slug> -->
<!-- learner-edit:start id=gap-<objective-slug> -->
<!-- learner-answer:gap-response -->
Write here.

<!-- learner-source:gap-<objective-slug> -->
- **Source:** Write here.
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

<!-- shared-contract:start id=gap-evidence -->
The learner-edit boundaries are user-owned evidence. Score the original region
and never rewrite it. Approval leaves it unchanged. Corrections, a reviewed
synthesis, model answers, source verification, and tutor feedback belong in a
review callout immediately after the boundary. Grammar cleanup remains a
separately marked copy. A missing or unverified source stays visible and caps
tutor confidence; it does not authorize rewriting the learner's words.
<!-- shared-contract:end id=gap-evidence -->

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

## Note Refresh on Re-quiz

When a re-quiz proves an objective is now mastered, offer to rewrite that note
section into clean current study material and archive the superseded scaffold to
the note's workpage. The review canvas reads clean; nothing is lost. This runs on
an already-reviewed note, not during first authoring.

### Preconditions

All of the following must hold. If any fails, do not refresh that section.

- The note exists and its frontmatter `status` is `reviewed`. Never refresh a
  `draft` note — a draft still holds unreviewed or unfilled gaps, and those must
  stay visible.
- For the objective, the **latest** attempt scored `solid` or
  `solid (recall-only)` with `assistance: none`, and no more-recent attempt
  downgraded it. A downgrade routes to the normal gap-reopen path, never here.
- The target section carries stale scaffold anchored to a **filled and reviewed**
  learner region (a review callout dated at or after `<!-- learner-edit:end -->`),
  or tutor-only stale callouts / `[!TIP]` flags from a former `partial`.
- The section is not a Phase 7 consolidation cross-reference pointer (a body that
  is only `See [[note#section]]`). Refresh the anchor section, not the pointer.
- The learner approves the offer.

### Actions per upgraded section

- **Archive** to the workpage, verbatim with original markers live — never
  neutralize or rename a marker, never normalize whitespace: the
  `[!IMPORTANT] RESEARCH NEEDED` callout, the `<!-- learner-edit:start -->` …
  `<!-- learner-edit:end -->` region (learner answer and source), and prior
  review / `[!TIP]` / `[!WARNING]` callouts. If the region holds only markers with
  no learner-authored prose, do not archive and do not refresh — leave it.
- **Rewrite** the section as Phase 5 solid-quality notes: plain explanation,
  `### Key terms`, `### Exam focus`, and a `> [!NOTE]` worked example when the
  content supports one. For `solid (recall-only)`, keep the rewrite at least as
  complete as Phase 5 would author and do not overstate mastery. The rewrite cites
  its own verified source, independent of any unverified source on the archived
  original.
- **Determinism**: a second refresh with no new evidence yields byte-identical
  note prose and only one additional dated archive entry.
- **Atomicity**: each section's archive and rewrite is atomic. A failure mid-note
  leaves the note byte-identical to its pre-refresh state with no partial archive
  entry.
- **Untouched**: still-`gap`, `partial`, or unfilled objectives. Rewrite scope is
  per-section, never whole-note.

### The note keeps

- Frontmatter `updated` bumped to today's local date; `status` stays `reviewed`.
- Exactly one `> [!NOTE]` "Learning history" callout, placed once per note
  directly below the frontmatter, before the first `##` objective, linking the
  workpage. Update its date list on later refreshes. Do not add per-section
  pointers — that would reclutter the canvas.

### Workpage file

Write to `_study/workpages/<note-basename>.md`, one per note, append-only:

```text
---
type: study-workpage
note: <vault-relative path to the note>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
source: note-refresh
---

Archived history from note refreshes. This is not current study material. The
session file remains the canonical mastery ledger; on any conflict the session
file wins.

## Refresh — <YYYY-MM-DD> — <scope>

- Attempt: <attempt-id> — Upgraded: <objective slugs> — Assistance: none

### <objective> — was <prior mastery>, now solid

<verbatim archived scaffold: RESEARCH NEEDED callout, the learner-edit region with
the learner's answer and source, and any prior review/[!TIP]/[!WARNING] callouts>
```

Every `<!-- learner-edit:start -->` in a workpage must sit inside a `## Refresh —`
block, so an archived region can never be mistaken for live evidence.

### Bookkeeping

- Add one line per refresh to the session `## Review — <date>` changelog and
  `## Session log`, naming the archived objective(s), the workpage path, and the
  triggering attempt id.
- The session file is otherwise untouched and remains canonical.

### Approval and mastery boundary

Offer-then-approve the whole bundle (note rewrite plus workpage append); preview
which sections are rewritten and which bytes move to which workpage. A note
refresh changes no `## Assessment`, `## Unit progress`, `## Mastery evidence`, or
mastery grade — it is hygiene of already-earned mastery, never new, altered, or
deleted evidence.

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
   - If wrong or incomplete, preserve it and put the correction or reviewed
     synthesis in a feedback callout immediately after the learner boundary.
   - If unsure, add a `> [!WARNING]` callout rather than guessing.
   - Provenance gate: approved gap content must either name a source the user
     can point to (course material, vendor doc, RFC/NIST, reputable reference)
     or be flagged — tutor confidence at most `low` plus a `[!WARNING]` callout
     noting unverified provenance. Plausible-sounding prose with no source is a
     plausibility check, not a knowledge check; do not let it earn `solid`.
   - Replace the stale pending `[!IMPORTANT]` research callout after review. Keep
     the alert tag alone on its line and put the status on the next line:
     - `solid` or approved without edits → `[!TIP]`, body **Research reviewed — <date>**
     - corrected or still `partial` → `[!TIP]`, body **Research reviewed — corrections provided on <date>**
     - unresolved `gap` → `[!WARNING]`, body **More research needed — <date>**
   - Keep the `gap`, `learner-edit:start`, `learner-answer`, `learner-source`,
     and `learner-edit:end` markers so the original region remains traceable.
     Do not leave `RESEARCH NEEDED` above reviewed work.
   - Check frontmatter, tags, `[[wikilinks]]`, and related/mind-map metadata for
     consistency with the rest of the vault.
   - Apply a light humanizer pass so the final note reads like durable study
     material, not an AI transcript.
8. Score each answered mastery check before editing the user's selections:
   - Accuracy or correctness: `0-2`
   - Context or application fit: `0-2`
   - Reasoning or explanation: `0-2`
   - Transfer, limitations, alternatives, or distractor rejection: `0-2`
   - Record `<earned>/<applicable>` and apply the mastery proportions from the
     canonical scoring contract. Full applied checks remain `/8`.
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
> **Review — <date> · Score <earned>/<applicable> (<solid|partial|gap>)**
> **What worked:** <specific evidence>
> **Correction:** <what was wrong or incomplete>
> **Why:** <reasoning or transfer explanation>
```

   If the user asked for grammar cleanup, apply the **Learner Answer Grammar
   Cleanup** rules after scoring and before final bookkeeping. Add cleaned copies
   only; do not replace the original learner answer text and do not let the
   cleaned copy affect the score.

10. Append this changelog to the session file and print it in chat:

```markdown
## Review — <date>

- <objective>: EDITED — <what changed>. Reason: <why>.
- <objective>: APPROVED — no changes.
- <study-check-id>: <earned>/<applicable> — <solid|partial|gap>; tutor confidence <level>;
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
- Learner grammar cleanup never changes the original answer or learner-owned
  research text. MiMo output is advisory-only and must remain separate from
  graded evidence.
- A note refresh (see Note Refresh on Re-quiz) only relocates superseded scaffold
  verbatim to `_study/workpages/`; it never rewrites, deletes, or fabricates
  learner-owned evidence, runs only on a `status: reviewed` note, is
  offer-then-approve, and leaves the session file as the canonical ledger.
