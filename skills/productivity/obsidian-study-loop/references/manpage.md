# Obsidian Study Loop — Manual

A plain-language guide to the study loop. `STUDY-PROTOCOL.md` (and the skill's
`SKILL.md`) stay authoritative — if this manual ever disagrees with the
protocol, the protocol wins. Print any topic with
`scripts/study_man.py <topic>` or list them all with `--list`.

<!-- man:section id=what aliases="about,overview,intro,what is this" -->
## What this is

A study system saved as ordinary files inside your Obsidian vault. The agent
first runs a short diagnostic against the chapter breakdown. It then publishes
complete notes shaped by what the check exposed, shows the exact sections to
read, and prepares Anki recall cards from those finished notes. You do not have
to fill note placeholders or pass every question before the notes are written.

Your vault is the database. Routine tutoring, quizzing, grading, and note work
stay local. Only an explicit advisory consult or research dive may send bounded
context to an external configured model, and those results remain untrusted
until the tutor verifies them.
<!-- man:section-end id=what -->

<!-- man:section id=quickstart aliases="start,begin,first-night,how do i start,typical" -->
## Quickstart — diagnose, publish, learn, complete

1. **Name the chapter.** Paste its outline, objectives, key terms, labs, or
   course pages when you have them.
2. **Take the diagnostic.** The tutor asks a few applied questions before it
   rewrites the notes or generates Anki cards. No prior reading is required.
3. **Receive the publication.** The agent writes complete notes for every
   assessed objective, including the areas you missed, then prepares Anki from
   the final note headings.
4. **Follow the board.** Read the exact note headings it names and import or
   review the Anki cards. This is where you decide when the material feels clear
   enough for another check.
5. **Recheck only unresolved objectives.** Passed objectives stay passed. A
   fresh question covers only a remaining applied gap unless you request a full
   chapter test.
6. **Complete the chapter.** Completion requires ready notes, ready or declined
   Anki practice, and passed applied competency for every relevant objective.

Anki reviews continue after chapter completion without reopening it.
<!-- man:section-end id=quickstart -->

<!-- man:section id=say aliases="commands,triggers,phrases,cheat sheet,what do i say" -->
## What to say

| You want | Say |
|---|---|
| Prepare a chapter | "Prepare chapter X" (paste the study packet) |
| See the live board | "Show my study board" / "what should I do next?" |
| Prepare Anki cards | "Prepare the Anki import" |
| Run competency checks | "Test my competency" / "assess objective 3.1" |
| A nudge mid-question | "hint" (steps down a ladder; never spoils outright) |
| Save the current check | "pause" (keeps the attempt unfinished and ungraded) |
| Continue it | "resume" |
| Change wording only | "rephrase" (no hint penalty) |
| Give up on a question | "show me" / "skip" |
| Explain it back | "let me teach it back" (learning practice; later fresh checks can count) |
| Repair confusion | "teach me X" / "I don't get X" / "go deeper on X" |
| Repair thin notes | "research X with sources" / "enrich this section" |
| A visual study aid | "make me a visual review for the current scope" |
| Reflect on the study process | "reflect on my study process" / "what keeps helping or hurting my learning?" |
| This guide | "study manual" / "man page for the study loop" / a topic name |
<!-- man:section-end id=say -->

<!-- man:section id=phases aliases="loop,workflow,lifecycle,how it works" -->
## The loop

1. **Prepare the scope** — the agent turns the supplied chapter breakdown into
   stable objectives. It does not publish notes or Anki yet.
2. **Diagnose** — you answer a small number of applied questions in chat. The
   session ledger preserves the evidence, hints, and score.
3. **Publish** — the agent writes complete notes for every assessed objective,
   whether it passed or exposed a gap. It then generates Anki from those final
   note sections.
4. **Learn** — you read the board's note locations and use Anki for recall. A
   reported confusion can trigger one focused teaching intervention and a note
   update.
5. **Recheck and complete** — only unresolved applied objectives receive fresh
   questions. The chapter completes after every relevant competency gate passes.

The board is generated from the session file, so there is no second checklist
to drift. Anki ratings never count as mastery. A failed initial check never
withholds the notes; it tells the publication what to explain more clearly.
<!-- man:section-end id=phases -->

<!-- man:section id=quiz aliases="quizzing,questions,hints,test me" -->
## How the competency check works

- One question at a time, in chat. No walls of lettered questions.
- The first check happens before note publication and Anki. It is diagnostic,
  so you do not need to study the agent's material first.
- Normally one diagnostic scenario per objective and no more than three prompts
  in one action. Anki handles the repeated definitions and recognition work.
- Expect application, comparison, classification, or transfer prompts where you
  explain *why* an answer fits and when it would not.
- **"hint"** steps down a ladder one level per request: first a reframing,
  then attention to the relevant detail, then the underlying principle. Hints
  never reveal the answer, and a hint-assisted correct answer caps at
  `partial` — honest evidence beats flattering evidence.
- **"show me" / "skip"** reveals the answer with reasoning; only what you
  produced before the reveal is scored.
- Version 2 does not ask for a Low/Medium/High confidence label. The ledger uses
  `unknown` unless you volunteer a label before feedback. Your readiness is a
  decision you make while reviewing the finished notes and Anki cards.
- `pause`, `resume`, `rephrase`, `shorter`, and `deeper` are first-class
  controls. Rephrasing changes wording without a hint penalty; shorter/deeper
  adjusts question density without silently expanding scope.
- Attempt progress records the complete current prompt before it is shown. If the
  session dies mid-question, the next tutor can resume that exact attempt.
<!-- man:section-end id=quiz -->

<!-- man:section id=scoring aliases="mastery,grades,rubric,confidence,calibration,solid,partial,gap" -->
## Scoring and mastery

Applied answers use four dimensions worth two points each: accuracy, context
fit, reasoning, and transfer. Questions are scored only on dimensions that
actually apply, with earned and applicable points both shown. A perfect
definition can therefore be `2/2 applicable — solid (recall-only)`, never
`2/8`. Applicable denominators are `2`, `4`, `6`, or `8`, matching the rubric
dimensions the question genuinely exercises.

- `solid` = at least 87.5% of applicable points · `partial` = 50% to below
  87.5% · `gap` = below 50%.
- Each objective's assessment names one scored **evidence question** and copies
  that question's raw score, assistance, and recorded confidence or `unknown`.
  The most diagnostic unassisted answer is preferred when available. That
  selected answer controls numeric mastery and calibration; all the other
  evidence can still affect the tutor's accumulated confidence and explanation.
- Question kinds are deliberately finite. Definition, recall, free-production,
  fill-in-the-blank, and recognition variants stay `solid (recall-only)` when
  solid; application, scenario, comparison, classification, discrimination,
  transfer, and lab variants are applied-capable. Unknown kinds fail validation
  instead of accidentally bypassing the recall-only confidence cap.
- A selected answer with any hint or reveal is capped at `partial`, even when
  its raw score reaches the `solid` band. After **show me** or **skip**, only
  what you produced before the answer was revealed is scored—often a `gap`.
  The shown answer never earns credit, and revealed evidence is never `solid`.
- Anki owns recurring recall dates and due-card selection. Its ratings do not
  alter competency, confidence, or the session ledger.
- The tutor schedules a fresh applied check only after remediation or a
  substantive chapter revisit. Version 2 does not run a second spaced schedule
  alongside Anki.
- The tutor's confidence comes from the accumulated evidence. Version 2 does
  not turn a required self-confidence label into learner-facing praise or
  criticism. A volunteered label can remain in the ledger for history.
- Evidence-quality rules are strict on purpose: recognizing an answer counts
  for less than producing it from memory, hint-assisted answers cap at
  `partial`, and a `solid` built only on recall stays flagged `recall-only`
  until you've shown you can apply it.
<!-- man:section-end id=scoring -->

<!-- man:section id=notes aliases="notes,enrichment,publication,content ready" -->
## Complete notes and enrichment

Notes are clean, agent-maintained study material, not worksheets. They are
published immediately after the first competency attempt. Every assessed
objective gets a complete section even when the result was `partial` or `gap`.
A weak result changes the explanation and examples; it never creates homework
fields for you to fill.

The chapter breakdown controls scope. The agent uses its enriched content first,
then verified material already in the vault, and cited research only when a
factual defect needs repair. Your answer tells the agent what needs emphasis; it
does not become a source and it does not add unrelated material.

Each note passes the same writing pipeline: `technical-writing` sets the mode
and structure, `unslop` removes filler without changing technical meaning,
`humanizer` runs a neutral draft-audit-final rewrite, and
`portable-markdown` checks the finished Markdown. Only the final checked note is
saved. Anki cards are generated from that note, not from raw answers or mistakes.

If the canonical material is thin, contradictory, or weakly sourced, the tutor
runs bounded cited research and enriches the same note. If the material is
correct but has not clicked, the tutor teaches it and may add a verified clearer
explanation. Neither action proves mastery; only a fresh applied response can do
that.

Old study-loop notes may still contain gap fields or embedded checks. They are
preserved as legacy evidence. A requested migration archives those original
regions under `_study/workpages/` and publishes a clean version 2 note without
silently rewriting your historical answer.
<!-- man:section-end id=notes -->

<!-- man:section id=deep-dives aliases="deep dive,dive,teach me,research dive,teaching dive,go deeper" -->
## Deep dives (mid-session teaching and research)

When the material just isn't landing, you don't have to leave the session:

- **"teach me X" / "I don't get X"** → a **teaching dive**: adaptive tutoring
  (`teach-complex-concepts`) — small steps, you do the thinking, hints on a
  ladder, misconceptions repaired.
- **"research X with sources"** → a **research dive**: a research process
  (`evidence-research-loop`) that checks every quote against its source,
  working in a dated folder under `_study/research/` in your vault. Its
  verified final write-up may enrich the canonical note.

A teaching dive is real tutoring, not more quizzing: expect a clear goal,
concrete scenarios, worked examples, and explanations that build on your
answers — the quiz's answer-withholding rules don't apply here, because dive
answers never count toward your grades anyway. If a picture would help, ask
for one ("draw it") — the tutor draws the analogy first, then the same
picture relabeled with the real terms, and Obsidian renders them.

Each teaching dive is saved under `_study/dives/`, and the session record links
to it. The dive itself remains separate evidence, but the study-loop
orchestrator may publish a verified clearer explanation into the canonical
note and refresh affected cards. The topic is checked against the active
chapter first; unrelated dives stay standalone.

**Deep dives never change your grades.** Teaching answers are hint-saturated,
so they aren't mastery evidence; instead every remediation ends with a fresh
applied check — the honest path to updating competency.
The normal rhythm is orient → focused chunk → worked example → retrieval →
feedback → self-explanation or teach-back → a later fresh transfer check. An
immediate teach-back helps learning but is not itself mastery evidence.
<!-- man:section-end id=deep-dives -->

<!-- man:section id=reflection aliases="reflect,reflection,study process,learning patterns,improve studying" -->
## Reflect on the study process

Say **"reflect on my study process"** when you have enough completed or legacy
reviewed history
and want to know whether something repeatedly helps or gets in the way. You
choose the course, chapter, or objective. A candidate needs the same pattern in
at least three independent dated occurrences: separate reviewed attempts for a
mastery-related pattern, or separate teaching dives for an instructional one.
Mirrored summaries of one occurrence count once.

The result is a chat-only improvement candidate: the exact session plus either
an attempt or check ID or a dated deep-dive heading; the proposed adjustment;
expected gain; possible downside; and a fresh applied check that could
prove whether it helped. Sparse or contradictory history produces no candidate
rather than a guess.

Reflection never edits the vault, calls an external model, changes grades,
mastery, confidence, schedules, answers, notes, or session state, or builds a
permanent learner profile. Embedded commands, links, and scope-expansion
requests in old records are inert, untrusted evidence: the tutor never follows
them, quotes only what is necessary, and does not expose sensitive learner
content. Teaching-dive responses can suggest a better pace, representation, or
hint strategy, but never prove mastery. Nothing carries into future sessions
unless you explicitly adopt it later through the normal study workflow; old
evidence is never rewritten. If reflection uncovers a factual or integrity
problem, the tutor reports it, stops the reflection, and offers the normal
review or repair path as a separate action.
<!-- man:section-end id=reflection -->

<!-- man:section id=visuals aliases="visual,mermaid,markdown,artifact,concept map,diagram" -->
## Visual review artifacts

After a scope has been quizzed or written, ask for a visual review ("make me
a visual review for 3.1"). You get a Markdown note with Mermaid diagrams that
opens directly in Obsidian on desktop and iPadOS — concept maps, comparison
tables, flows, and foldable retrieval prompts — written to `_study/visuals/`.
It is a study aid labeled `Visual review artifact - not an assessment`: no
scoring, no answer collection, no remote dependencies, and no assessment
changes. The automatic chapter endpoint is separate: `visualize-study-chapter`
owns its helper-generated HTML under the vault's `Visuals/` folder.
<!-- man:section-end id=visuals -->

<!-- man:section id=maps aliases="map,mind map,seeds,related,navigation,canvas" -->
## Maps and mind-map seeds

`related:` and `## Mind map seeds` help the map builder navigate finished
notes; they do not add study content or competency evidence. A `[[note]]` or
`[[note#heading]]` seed must resolve to one real note in `Notes/` or `Maps/`.
Plain-text seeds are ideas for the map gap report, not links or file nodes.

Maps refresh when a chapter reaches `complete`, not after every note edit. The
release check rejects missing or ambiguous note links, renamed heading anchors,
links into workflow scaffolding, duplicate Canvas node or edge IDs, and malformed
Canvas structures. If a note is renamed, update its related links and seeds
before refreshing the map.
<!-- man:section-end id=maps -->

<!-- man:section id=layout aliases="files,disk,structure,vault,where,folders" -->
## What's on disk

```text
<vault>/
  STUDY-PROTOCOL.md      # the installed workflow (authoritative)
  STUDY-MANUAL.md        # this manual — open it in Obsidian any time
  Notes/                 # complete agent-maintained study material
  Maps/                  # study-map navigation pages (optional)
  _study/
    state.json           # which session is active
    sessions/            # source ledger: objectives, state, applied evidence
    anki/                # source manifests and generated TSV imports
    visuals/             # Markdown and Mermaid study aids
    dives/               # teaching-dive notes (decoupled from Notes/)
    research/            # research-dive workspaces (sources, evidence,
                         #   synthesis, audit)
    workpages/           # note-refresh history archives (one per note)
```

The review board is generated from the active session when requested; there is
no second board file to become stale. The session file is the audit trail: every
question asked, its grade, note write, dive, and remediation lands there with a
timestamp. It keeps the question
and a short summary of what your answer showed — not your answer word for
word. If the chat loses its memory, the saved files are enough to pick up
where you left off.
<!-- man:section-end id=layout -->

<!-- man:section id=helpers aliases="tools,skills,toolbox,categories,helper skills" -->
## The toolbox (helper skills, by category)

**Mid-session deep dives**
- `teach-complex-concepts` — teaching dive: adaptive tutoring when material
  hasn't clicked.
- `evidence-research-loop` — research dive: citation-audited answers used to
  repair a bounded defect in the canonical notes.

**Research planning**
- `study-research-queries` — creates a focused source plan before a difficult
  research repair.
- `literature-review` — formal, citation-backed deep research; heavy, for
  when a topic truly needs it.

**Note quality**
- `technical-writing` — chooses one document mode per note and keeps the
  structure, instructions, and sentences unambiguous.
- `unslop` — preservation-first prose authoring; keeps technical terms and
  learner-owned wording intact while removing unnecessary filler.
- `portable-markdown` — keeps notes in standard Markdown that renders
  everywhere: callout boxes, clean tables, invisible markers.
- `humanizer` — runs the final draft-audit-rewrite pass for version 2 notes in a
  neutral technical voice. Drafts stay transient; only the checked final prose
  is saved.
- `knowledge-capture-obsidian` — vault hygiene: frontmatter, tags, wikilinks,
  index links.

**Second opinions (opt-in, advisory only)**
- `study-consult-panel` — reads drafted notes and checks wording and
  technical accuracy without changing anything; can also add grammar-cleaned
  copies of your answers without touching the originals. Never becomes the
  tutor.

**Navigation**
- `study-map` — tiered map pages (course → chapter → concept) in `Maps/`,
  built only from links that actually resolve.

**Recall practice**
- `anki-study-sync` — creates stable, source-anchored Anki text imports from
  content-ready notes. The builder rejects fronts that depend on "this
  chapter" or a numbered lab, and rejects duplicate active answers. It never
  grades competency or changes Anki directly.

**Repair**
- `undo-obsidian-study-loop` — roll back a mistaken install or false-start
  session safely (inventory and dry-run first).
<!-- man:section-end id=helpers -->

<!-- man:section id=scripts aliases="sync,validate,man,utilities,scripts" -->
## Bundled scripts

All read-only except where noted; all local, no network.

- `scripts/install_study_loop.py <vault> [--apply]` — idempotent installer.
  Dry-runs by default, creates only missing scaffold pieces, and never resets
  existing state or overwrites protocol, manual, notes, or sessions.
- `scripts/study_man.py [topic|--list] [--pretty]` — this manual, whole or by
  topic; `--pretty` gives a styled view in a terminal (on automatically when
  you run it by hand).
- `scripts/study_board.py <vault>` — renders the current chapter board from the
  session ledger without writing a second state file.
- `scripts/validate_study_vault.py <vault>` — integrity check: session
  structure, version 2 completion gates, clean publications, recoverable legacy
  attempts, statuses, and the visual-artifact contract. Add `--active-only`
  with `--summary` for a concise current-chapter release gate; it preserves the
  validator's failure exit code without piping through another command.
- `scripts/sync_study_protocol.py <vault> [--apply]` — compares your
  installed protocol and manual to the skill's bundled sources. Preview-only
  by default; `--apply` refreshes both installed copies while preserving notes,
  pointer files, state, and sessions.
<!-- man:section-end id=scripts -->

<!-- man:section id=safety aliases="rules,protections,trust,evidence" -->
## Rules that protect you

- Your vault is treated as precious: nothing is deleted or overwritten
  without asking.
- Your answers live in the session evidence ledger, not inside published notes.
  Legacy learner answers are preserved byte-for-byte during migration.
- Asking for hints is always welcome. Assisted evidence is labeled honestly and
  capped; a later fresh canonical check can demonstrate independent mastery.
- The agent is the tutor. No API keys or external grading services; the only
  external-model calls are the opt-in advisory consult and research-dive
  source reading, both verified before use.
- The Anki handoff is a local text file. Anki reviews are practice and never
  silently alter competency or chapter state.
- Every state-, evidence-, or mastery-changing action is recorded in the
  session file with a real date and time. Read-only reflection changes none of
  them and is not logged.
<!-- man:section-end id=safety -->

<!-- man:section id=recovery aliases="stuck,resume,interrupted,undo,broken,help" -->
## Getting unstuck

- **Check died mid-way?** Say "resume" — the disk-backed attempt
  restores an asked question first, then the earliest planned question.
- **A command or edit was aborted?** The next action is read-only recovery:
  inspect the active pointer, complete objective list, current question states,
  and changed note/card files before writing again. Nothing is marked complete
  or committed until the active-only validator passes.
- **The validator prints too much?** Use `--active-only --summary`. Do not pipe
  it through `tail`; a pipeline can hide the validator's nonzero exit code.
- **Old chapters already have known errors?** The active-only gate isolates the
  current chapter. The full validator still reports historical findings, which
  remain open until repaired; a nonzero full result is never called clean.
- **One question was skipped?** Only that asked question is skipped. Later
  objectives remain planned unless you explicitly shorten, pause, or change the
  scope.
- **Came back days later?** Just talk; the active session is read from
  `_study/state.json`. A session that says `complete` staying active is
  normal — it's context for whatever you do next.
- **No active session but you had one?** The agent inspects the most recent
  session file and asks whether to resume it — nothing is silently discarded.
- **Left gaps unfilled or checks unanswered?** They're surfaced at the start
  of the next session — resume, keep waiting, or archive.
- **Half-finished research dive?** Reported at session start with where it
  stopped; resumable at the first incomplete stage.
- **Something looks structurally wrong?** Run the validator; it names the
  problem without touching anything.
- **Ran setup twice?** The installer is idempotent: it fills missing scaffold
  pieces but preserves active state and existing study files.
- **Installed into the wrong folder / false-start session?** Use
  `undo-obsidian-study-loop` — it lists what it would remove and previews
  the change before touching anything.
<!-- man:section-end id=recovery -->
