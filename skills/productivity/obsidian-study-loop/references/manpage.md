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

Nothing here calls a study app or uploads your progress anywhere. Your vault
is the database.
<!-- man:section-end id=what -->

<!-- man:section id=quickstart aliases="start,begin,first-night,how do i start,typical" -->
## Quickstart — a typical study night

1. **Tell the tutor what you're studying.** "I'll be studying 3.2 Cryptography
   Implementations tonight." Paste the section breakdown if you have it —
   learning outcomes, key terms, exam objectives, labs. More detail in equals
   better quiz out.
2. **Go study.** Offline, at your pace. The session waits on disk.
3. **Come back and say "quiz me"** (or "quiz me on 3.2" for one section).
   One question at a time; answer in your own words.
4. **Get graded.** Each objective lands as `solid`, `partial`, or `gap`, with
   evidence.
5. **Notes get written** into your vault — full sections for what you know,
   research stubs for what you missed.
6. **Fill the gaps yourself** (that's where the learning is), then say
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
| Give up on a question | "show me" / "skip" |
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
   Progress is saved to disk after every scored answer, so an interrupted quiz
   resumes instead of restarting.
4. **Assess** — every in-scope objective graded `solid` / `partial` / `gap`
   with a score out of 8 and brief evidence.
5. **Write notes** — real notes in your vault. `solid` and `partial` get full
   sections; `gap` gets a research stub that tells you exactly what to find
   out, without spoiling the answer.
6. **Your research** — you fill the stubs in your own words. The tutor doesn't
   do this for you unless you explicitly ask.
7. **Review** — "review my additions" checks accuracy, scores your practice
   checks, fixes what needs fixing, and closes the loop in the session log.

Two optional layers sit alongside the phases: **deep dives** (mid-session
tutoring or sourced research) and **visual review artifacts** (offline HTML
study aids). Neither changes your grades.
<!-- man:section-end id=phases -->

<!-- man:section id=quiz aliases="quizzing,questions,hints,test me" -->
## How the quiz works

- One question at a time, in chat. No walls of lettered questions.
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
- You'll often be asked for your confidence (Low/Medium/High) before
  feedback. That's calibration data — say what you actually feel.
- Quiz progress is written to the session file as you go. If the session dies
  mid-quiz, the next agent offers to resume from the first unanswered
  question.
<!-- man:section-end id=quiz -->

<!-- man:section id=scoring aliases="mastery,grades,rubric,confidence,calibration,solid,partial,gap" -->
## Scoring and mastery

Each answer is scored out of 8 across four dimensions (2 points each):
accuracy, context fit, reasoning, and transfer (limits, alternatives,
rejecting distractors). Pure recall questions are scored only on the
dimensions that apply — a perfect definition isn't punished for having no
"transfer" angle.

- `solid` = 7–8 · `partial` = 4–6 · `gap` = 0–3
- `solid` objectives get a **next review** date (7 days out, 21 if tutor
  confidence is high) and may reappear as warm-up questions later. If the
  re-check scores lower, the rating is downgraded — past wins don't carry
  forward automatically.
- Two confidence signals stay separate: **yours** (before feedback) and the
  **tutor's** (from accumulated evidence). Comparing them yields calibration:
  well-calibrated, overconfident, or underconfident.
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
  research (never the answer), plus a marked region where you write. Replace
  the `Write here.` line; keep the hidden markers (invisible labels in the
  file) — they're how review finds your work.
- **Study-checks**: practice exercises embedded in notes, answered offline
  between sessions. Check a box, fill the response lines, pick your
  confidence.

Then say **"review my additions"**. Your gap fills are checked for accuracy
and for a named source — say where you learned it (course material, vendor
doc, RFC/NIST) or it can't earn `solid` — and study-checks are scored on the same
8-point rubric, corrections are explained, and the session file records it
all. Your original words are never rewritten; corrections live in feedback
callouts next to them.
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

The topic is checked against your active session first — in-scope dives are
announced and integrated; unrelated ones run standalone so your session stays
clean. What the dive produces is saved: an entry in your session file, and
durable content as a `### Deep dive` subsection in the relevant note. No
separate folders to dig through.

**Deep dives never change your grades.** Teaching answers are hint-saturated,
so they aren't mastery evidence; instead every dive ends by offering a short
re-quiz or an embedded practice check — the honest paths to updating mastery.
<!-- man:section-end id=deep-dives -->

<!-- man:section id=visuals aliases="visual,html,artifact,concept map,diagram" -->
## Visual review artifacts

After a scope has been quizzed or written, ask for a visual review ("make me
a visual review for 3.1"). You get a single web page that works completely
offline — concept maps, comparison tables, flows, retrieval prompts — written to
`_study/visuals/`. It's a study aid, labeled as such: no scoring, no answer
collection, no network, and it never touches your assessments.
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
    research/            # research-dive workspaces (sources, evidence,
                         #   synthesis, audit)
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

- `scripts/study_man.py [topic|--list] [--pretty]` — this manual, whole or by
  topic; `--pretty` gives a styled view in a terminal (on automatically when
  you run it by hand).
- `scripts/validate_study_vault.py <vault>` — integrity check: session
  structure, markers, statuses, visual-artifact contract. Run after anything
  odd; errors mean something needs deliberate repair.
- `scripts/sync_study_protocol.py <vault> [--apply]` — compares your
  installed `STUDY-PROTOCOL.md` to the skill's current template. Preview-only
  by default (a dry run); `--apply` rewrites the protocol file (only that
  file), and the agent then refreshes `STUDY-MANUAL.md` to match.
<!-- man:section-end id=scripts -->

<!-- man:section id=safety aliases="rules,protections,trust,evidence" -->
## Rules that protect you

- Your vault is treated as precious: nothing is deleted or overwritten
  without asking.
- Your answers are evidence. They're never rewritten — corrections and model
  answers live beside them, and grammar cleanup (if you ask for it) adds a
  copy, never replaces.
- Grades come only from what you produced: no credit for what a dive taught
  you five minutes ago, no penalty for asking for hints — just honest caps.
- The agent is the tutor. No API keys, no external quiz services; the only
  external-model calls are the opt-in advisory consult and research-dive
  source reading, both verified before use.
- Every action is recorded in the session file with a real date and time.
<!-- man:section-end id=safety -->

<!-- man:section id=recovery aliases="stuck,resume,interrupted,undo,broken,help" -->
## Getting unstuck

- **Quiz died mid-way?** Say "quiz me" again — the disk-backed progress block
  lets it resume from the first unanswered question.
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
- **Installed into the wrong folder / false-start session?** Use
  `undo-obsidian-study-loop` — it lists what it would remove and previews
  the change before touching anything.
<!-- man:section-end id=recovery -->
