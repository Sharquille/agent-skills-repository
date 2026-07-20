# Obsidian Study Loop — Manual

A plain-language guide to the study loop. `STUDY-PROTOCOL.md` (and the skill's
`SKILL.md`) stay authoritative — if this manual ever disagrees with the
protocol, the protocol wins. Print any topic with
`scripts/study_man.py <topic>` or list them all with `--list`.

<!-- man:section id=what aliases="about,overview,intro,what is this" -->
## What this is

A study system saved as ordinary files inside your Obsidian vault. The agent is
your tutor: it sets up study sessions, quizzes you one question at a time,
grades honestly, writes structured notes with deliberate gaps for you to
research, and reviews what you filled in. Everything is saved as plain
Markdown and JSON, so you can close the terminal, study for three days, come
back on another machine, and pick up exactly where you left off.

Your vault is the database. Routine tutoring, quizzing, grading, and note work
stay local. Only an explicit advisory consult or research dive may send bounded
context to an external configured model, and those results remain untrusted
until the tutor verifies them.
<!-- man:section-end id=what -->

<!-- man:section id=quickstart aliases="start,begin,first-night,how do i start,typical" -->
## Quickstart — a typical study night

1. **Tell the tutor what you're studying.** "I'll be studying 3.2 Cryptography
   Implementations tonight." Paste the section breakdown if you have it —
   learning outcomes, key terms, exam objectives, labs. More useful detail
   produces a better-aligned quiz.
2. **Optionally activate what you know.** The tutor may offer one short prior-
   knowledge prompt labeled as orientation, not a quiz. It is never graded.
3. **Go study.** Offline, at your pace. The session waits on disk.
4. **Come back and say "quiz me"** (or "quiz me on 3.2" for one section).
   One question at a time; answer in your own words.
5. **Get graded.** Each objective lands as `solid`, `partial`, or `gap`, with
   evidence.
6. **Notes get written** into your vault — full sections for what you know,
   research stubs for what you missed.
7. **Fill the gaps yourself** (that's where the learning is), then say
   **"review my additions"** to get them checked and scored.

Repeat per section. Say "study manual" or name a topic (like "deep dives")
any time you want this guide.
<!-- man:section-end id=quickstart -->

<!-- man:section id=say aliases="commands,triggers,phrases,cheat sheet,what do i say" -->
## What to say

| You want | Say |
|---|---|
| Start a session | "I'll be studying X tonight" (paste the study packet) |
| Get quizzed on everything | "quiz me" / "I'm done" / "ready for the quiz" |
| Get quizzed on one section | "quiz me on 3.1" / "quiz Security Controls" |
| A nudge mid-question | "hint" (steps down a ladder; never spoils outright) |
| Save the current quiz | "pause" (keeps the attempt unfinished and ungraded) |
| Continue it | "resume" |
| Change wording only | "rephrase" (no hint penalty) |
| Fewer or more questions | "shorter" / "deeper" (scope stays fixed) |
| Give up on a question | "show me" / "skip" |
| Explain it back | "let me teach it back" (learning practice; later fresh checks can count) |
| Deeper teaching mid-session | "teach me X" / "I don't get X" / "go deeper on X" |
| Sourced research mid-session | "research X with sources" / "research X properly" |
| A visual study aid | "make me a visual review for the current scope" |
| Gap-fill checked | "review my additions" / "check my gap notes" |
| Help researching a gap | "help me research X" (gets queries and a source plan) |
| This guide | "study manual" / "man page for the study loop" / a topic name |
<!-- man:section-end id=say -->

<!-- man:section id=phases aliases="loop,workflow,lifecycle,how it works" -->
## The loop

1. **Setup** — you name the topic and paste per-section study content. A
   dated session file is created and the system remembers it as the active
   one.
2. **Study break** — nothing happens. You study offline; disk remembers.
3. **Quiz** — conversational, one question at a time, scoped to what you name.
   You see an estimated range first. Each planned, asked, scored, or deferred
   question is saved under a unique attempt, so interruption and re-quizzing do
   not collide.
4. **Assess** — every in-scope objective graded `solid` / `partial` / `gap`
   using only the scoring dimensions that apply, with brief evidence and
   confidence calibration.
5. **Write notes** — real notes in your vault. `solid` and `partial` get full
   sections; `gap` gets a research stub that tells you exactly what to find
   out, without spoiling the answer.
6. **Your research** — you fill the stubs in your own words. The tutor doesn't
   do this for you unless you explicitly ask.
7. **Review** — "review my additions" checks accuracy, scores your practice
   checks, adds corrections beside your original work, and closes the loop in
   the session log.

Two optional layers sit alongside the phases: **deep dives** (mid-session
tutoring or sourced research) and **visual review artifacts** (offline HTML
study aids). Neither changes your grades.
<!-- man:section-end id=phases -->

<!-- man:section id=quiz aliases="quizzing,questions,hints,test me" -->
## How the quiz works

- One question at a time, in chat. No walls of lettered questions.
- Before starting, the tutor gives an estimated minimum/target/maximum range;
  the quiz stops once the evidence is sufficient.
- Expect a mix: recall, fill-in-the-blank, compare-contrast, and applied
  scenarios where you explain *why* the answer fits.
- At least one pure free-recall prompt per section — producing a term from a
  scenario is stronger evidence than recognizing it in a list.
- **"hint"** steps down a ladder one level per request: first a reframing,
  then attention to the relevant detail, then the underlying principle. Hints
  never reveal the answer, and a hint-assisted correct answer caps at
  `partial` — honest evidence beats flattering evidence.
- **"show me" / "skip"** reveals the answer with reasoning; only what you
  produced before the reveal is scored.
- You'll be asked for confidence (Low/Medium/High) before feedback when
  practical. You may opt out; the record then says `unknown`.
- `pause`, `resume`, `rephrase`, `shorter`, and `deeper` are first-class
  controls. Rephrasing changes wording without a hint penalty; shorter/deeper
  adjusts question density without silently expanding scope.
- Quiz progress records the complete current prompt before it is shown. If the
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
  that question's raw score, assistance, and your recorded confidence. The most
  diagnostic unassisted answer is preferred when available. That selected
  answer controls numeric mastery and calibration; all the other evidence can
  still affect the tutor's accumulated confidence and explanation.
- Question kinds are deliberately finite. Definition, recall, free-production,
  fill-in-the-blank, and recognition variants stay `solid (recall-only)` when
  solid; application, scenario, comparison, classification, discrimination,
  transfer, and lab variants are applied-capable. Unknown kinds fail validation
  instead of accidentally bypassing the recall-only confidence cap.
- A selected answer with any hint or reveal is capped at `partial`, even when
  its raw score reaches the `solid` band. After **show me** or **skip**, only
  what you produced before the answer was revealed is scored—often a `gap`.
  The shown answer never earns credit, and revealed evidence is never `solid`.
- Successful unassisted retrieval moves through review stages of roughly 1,
  3, 7, 21, and 30 days, then at least monthly. A miss or assisted response
  does not advance; after remediation the sequence restarts.
- At most one or two due questions may appear before a new quiz. They come
  from related or easily confused material and remain graded under their
  original scope—not the new one. Their attempt stays in the originating
  session file while your active-session pointer remains unchanged.
- Two confidence signals stay separate: **yours** (before feedback) and the
  **tutor's** (from accumulated evidence). Calibration compares your confidence
  with that answer's mastery band; tutor confidence remains a separate judgment.
- Evidence-quality rules are strict on purpose: recognizing an answer counts
  for less than producing it from memory, hint-assisted answers cap at
  `partial`, and a `solid` built only on recall stays flagged `recall-only`
  until you've shown you can apply it.
<!-- man:section-end id=scoring -->

<!-- man:section id=notes aliases="gaps,gap stubs,study-checks,review,research needed,fill in" -->
## Notes, gaps, and review

Notes land in your vault (one note per course section by default) with a
proper metadata header (frontmatter) and tags. Three kinds of content:

- **Full sections** for `solid`/`partial` objectives — explanation, key terms,
  exam focus, worked examples.
- **Gap stubs** for what you missed: a callout stating exactly what to
  research (never the answer), plus marked response and source fields. Replace
  both `Write here.` lines and keep the hidden markers—they preserve your
  original evidence and let review find it.
- **Study-checks**: practice exercises embedded in notes, answered offline
  between sessions. Check a box, fill the response lines, pick your
  confidence.

Then say **"review my additions"**. Your gap fills are checked for accuracy
and for a named source — say where you learned it (course material, vendor
doc, RFC/NIST) or it can't earn `solid` — and study-checks are scored on the same
applicable-dimension rubric, corrections are explained, and the session file
records it all. Your original words are never rewritten; corrections and a
reviewed synthesis live in feedback callouts next to them.

**Note refresh on re-quiz.** When you re-quiz a topic later and prove you have
mastered an objective that previously had gaps, the note section is rewritten as
clean study material and the old scaffold — your earlier answer, research
callouts, and review tips — moves into a workpage file under `_study/workpages/`.
Your note then reads like fresh material, while your old work stays linked and
fully preserved so you can always trace how you got there. This only happens on an
already-reviewed note and only with your approval.
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
  final write-up becomes a source you can cite when filling a gap stub.

A teaching dive is real tutoring, not more quizzing: expect a clear goal,
concrete scenarios, worked examples, and explanations that build on your
answers — the quiz's answer-withholding rules don't apply here, because dive
answers never count toward your grades anyway. If a picture would help, ask
for one ("draw it") — the tutor draws the analogy first, then the same
picture relabeled with the real terms, and Obsidian renders them.

Teaching dives stay out of your real study notes. Your `Notes/` folder is
built only by the study flow (quiz → grade → write notes) — a dive never
touches it. Instead each teaching dive is saved as its own file in
`_study/dives/`, and your session record links to it. So the tutoring is
kept, but it never overwrites or pre-empts the course notes your quizzes
produce. The topic is still checked against your active session first —
in-scope dives are labeled with the section they belong to; unrelated ones
run standalone.

**Deep dives never change your grades.** Teaching answers are hint-saturated,
so they aren't mastery evidence; instead every dive ends by offering a short
re-quiz or an embedded practice check — the honest paths to updating mastery.
The normal rhythm is orient → focused chunk → worked example → retrieval →
feedback → self-explanation or teach-back → a later fresh transfer check. An
immediate teach-back helps learning but is not itself mastery evidence.
<!-- man:section-end id=deep-dives -->

<!-- man:section id=visuals aliases="visual,html,artifact,concept map,diagram" -->
## Visual review artifacts

After a scope has been quizzed or written, ask for a visual review ("make me
a visual review for 3.1"). You get a single web page that works completely
offline — concept maps, comparison tables, flows, retrieval prompts — written to
`_study/visuals/`. It's a study aid, labeled as such: no scoring, no answer
collection, no network, and it never touches your assessments. When the source
does not support honest retrieval cues, the page simply omits that deck and its
script instead of inventing questions.
<!-- man:section-end id=visuals -->

<!-- man:section id=layout aliases="files,disk,structure,vault,where,folders" -->
## What's on disk

```text
<vault>/
  STUDY-PROTOCOL.md      # the installed workflow (authoritative)
  STUDY-MANUAL.md        # this manual — open it in Obsidian any time
  Notes/                 # your study notes — the durable output
  Maps/                  # study-map navigation pages (optional)
  _study/
    state.json           # which session is active
    sessions/            # one file per session: study content, quiz
                         #   progress, assessments, deep dives, review log
    visuals/             # offline HTML study aids
    dives/               # teaching-dive notes (decoupled from Notes/)
    research/            # research-dive workspaces (sources, evidence,
                         #   synthesis, audit)
    workpages/           # note-refresh history archives (one per note)
```

The session file is the audit trail: every quiz answer, grade, note write,
dive, and review lands there with a timestamp. If the chat loses its memory,
the saved files are enough to pick up where you left off.
<!-- man:section-end id=layout -->

<!-- man:section id=helpers aliases="tools,skills,toolbox,categories,helper skills" -->
## The toolbox (helper skills, by category)

**Mid-session deep dives**
- `teach-complex-concepts` — teaching dive: adaptive tutoring when material
  hasn't clicked.
- `evidence-research-loop` — research dive: citation-audited answers whose
  synthesis you can cite in gap fills.

**Research planning**
- `study-research-queries` — turns a gap into search queries, source types,
  and a capture checklist (you still do the research).
- `literature-review` — formal, citation-backed deep research; heavy, for
  when a topic truly needs it.

**Note quality**
- `portable-markdown` — keeps notes in standard Markdown that renders
  everywhere: callout boxes, clean tables, invisible markers.
- `humanizer` — prose pass so notes read like notes, not chatbot output.
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
- `scripts/validate_study_vault.py <vault>` — integrity check: session
  structure, recoverable quiz attempts, score notation, learner-source markers,
  statuses, and the visual-artifact contract. Run after anything odd; errors
  mean something needs deliberate repair.
- `scripts/sync_study_protocol.py <vault> [--apply]` — compares your
  installed protocol and manual to the skill's bundled sources. Preview-only
  by default; `--apply` refreshes both installed copies while preserving notes,
  pointer files, state, and sessions.
<!-- man:section-end id=scripts -->

<!-- man:section id=safety aliases="rules,protections,trust,evidence" -->
## Rules that protect you

- Your vault is treated as precious: nothing is deleted or overwritten
  without asking.
- Your answers are evidence. They're never rewritten — corrections and model
  answers live beside them, and grammar cleanup (if you ask for it) adds a
  copy, never replaces.
- Asking for hints is always welcome. Assisted evidence is labeled honestly and
  capped; a later fresh canonical check can demonstrate independent mastery.
- The agent is the tutor. No API keys, no external quiz services; the only
  external-model calls are the opt-in advisory consult and research-dive
  source reading, both verified before use.
- Every action is recorded in the session file with a real date and time.
<!-- man:section-end id=safety -->

<!-- man:section id=recovery aliases="stuck,resume,interrupted,undo,broken,help" -->
## Getting unstuck

- **Quiz died mid-way?** Say "resume" or "quiz me" — the disk-backed attempt
  restores an asked question first, then the earliest planned question.
- **Came back days later?** Just talk; the active session is read from
  `_study/state.json`. A session that says `reviewed` staying active is
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
