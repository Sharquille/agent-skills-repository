---
name: chapter-study-kit
description: >-
  Builds an expanding Monroe chapter study kit for any course (MA-235, EN-221,
  IT-100, LA-122, later). OCR from the original PDF or PowerPoint path, Core notes,
  GoodNotes mermaid maps (TD sort maps in Retrieval/), Obsidian Practice.md,
  and a per-course hub HTML via hub.json. Use when the user sends a chapter
  PDF, quiz notes, GoodNotes screenshots, flow map, or asks to expand that
  course’s overall map. Do not copy PDFs or screenshots into Chapter-Kits. Do
  not import Quiz why or Retrieval prose into GoodNotes. Do not mix two
  courses in one HTML. Do not use for week-folder bootstrap
  (continue-study-week), graded submission writing, or Obsidian
  visualize-study-chapter. Consult only if this turn names a panel.
---

# Chapter study kit

Workflow version: **2.8.0**. Read the canonical version before executing a synced copy.

Turn one **section** into a kit: GoodNotes maps + Core notes, Obsidian
`Practice.md` for self-test, hub HTML. Grow the overall course map only with
concepts supported by supplied sources. Chapter-Kits stays light: no textbook
PDFs, no screenshot dumps, no copied slide decks. No per-section HTML quiz.

Canonical `SKILL_DIR` (git-tracked in the agent-skills repository):
`/Users/sharquilleandrew/Documents/development/github-local/agent-skills-repository/skills/productivity/chapter-study-kit`

| Location | Kind | How it updates |
| --- | --- | --- |
| `~/.claude/skills/chapter-study-kit` | symlink to canonical | automatically |
| `~/.agents/skills/chapter-study-kit` | real-folder copy | `sync_skill.py` |
| `Education/.cursor/skills/chapter-study-kit` | real-folder copy for Cursor | `sync_skill.py` |

Edit only the canonical folder. Do not treat the copies as a second source of
truth. If versions differ, use the canonical instructions and report drift.
`MANIFEST.json` lists managed file hashes. After canonical edits, run the tests,
then regenerate it from the reviewed SKILL.md, references, scripts, and tests
(exclude caches). Run canonical `scripts/sync_skill.py --destination <copy>` for
a dry run on each real-folder copy, then add `--write`. It stops on unreviewed
deployed edits, refuses symlinks, and verifies SHA-256 hashes afterwards.
Preserve unrelated files. For initial adoption without a manifest, compare and
back up each copy first; record its reviewed baseline hashes before syncing.
Never auto-adopt a mismatch.

Do not git-init Monroe-University. Do not write graded posts or homework for
submission. Do not copy prior students' work. Do not fetch these scripts from
the network; run `$SKILL_DIR/scripts/`.

## Routing

This skill: chapter/section PDFs, GoodNotes maps, expand the overall map.

`continue-study-week`: user opens a week folder or says bootstrap week N.

## Orchestra panel (when the user asks)

Run only if this turn names a consult or those models. Use the `agent-orchestra`
wrappers directly; OpenCode lanes run sequentially. This panel deliberately
overrides the orchestra's default consult pair: never Kimi K3, skip Sol /
ChatGPT. If `agent-orchestra` renames a model, follow its routing reference and
keep these exclusions.

```text
ORCH=/Users/sharquilleandrew/Documents/development/github-local/agent-skills-repository/skills/engineering/agent-orchestra/scripts
"$ORCH/consult-opencode.sh" --sealed --model opencode-go/glm-5.3-flash --reasoning max --timeout 240 -- "<brief>"
"$ORCH/consult-opencode.sh" --sealed --model opencode-go/deepseek-v4.1-flash --variant max --timeout 240 -- "<brief>"
"$ORCH/consult-opencode.sh" --sealed --model opencode-go/minimax-m3 --variant max --timeout 240 -- "<brief>"
"$ORCH/consult-opencode.sh" --sealed --model opencode-go/muse-spark-1.3-contributor --variant max --timeout 240 -- "<brief>"
```

DeepSeek is `deepseek-v4.1-flash`, not `deepseek-v4-flash`. Muse Spark 1.3 is
the OpenCode Go contributor model. If Muse rejects `--variant max`, retry
without variant and report the miss.

Sealed briefs. No `01-University-Records`, no Drive dumps, no secrets, no
homework keys. Verify every consultant claim against the section `ocr-*.txt` (or the
original screenshots **in place**) before writing.

Skip the panel on a routine screenshot drop unless the user names it.

## Screenshots and PowerPoints as source

If they send screenshots of the chapter, GoodNotes, or a failed quiz: **read
them locally from the path they gave** (Downloads, Desktop, chat). Do **not**
copy PNGs into Chapter-Kits. That folder is maps, notes, ledger, OCR text,
and the hub only.

When screenshots are the only source, they **earn** ledger and map nodes.
Later screenshots may add previously missing concepts to the same section.
Record their evidence first; file format does not determine what is earned.
A source earns coverage, not proof that the student understands it.

If a PowerPoint (or lecture PDF deck) exists for the section in
`01-Study-Library/` or `00-Course-Guide/`, **map it** in `Chapter-Kits/SOURCES.md`.
Do not copy the deck into Chapter-Kits. Use current course slides for course emphasis and textbook captures for supplied
explanations and examples. Check actual section coverage and edition; do not
replace a detailed source with an overview deck just because slides exist.
Record conflicts and gaps instead of silently resolving them.

Claim URLs must not carry student IDs, emails, or credentials.

Notes shape: [references/overwhelm-scaffold.md](references/overwhelm-scaffold.md)
and [references/notes-contract.md](references/notes-contract.md).

## Workflow

```text
- [ ] 0. Guardrails (no git-init, no graded writing, no unearned map nodes)
- [ ] 1. Check batch state, register original sources, and wait if collecting
- [ ] 2. Extract locally by format; verify every page/image/slide
- [ ] 3. Write ledger.md (earned / not earned)
- [ ] 4. Chapter maps
- [ ] 5. Expand overall map (backup first)
- [ ] 6. Source-grounded editorial review + Practice outcome plan + Core-only 414 split
- [ ] 7. `validate_kit.py --kit` then Hub + HTTP 200
- [ ] 8. Chapter README + file into Chapter-Kits + GoodNotes folder rule
```

### 1. Register sources and batch state

```text
KIT=/Users/sharquilleandrew/Documents/Education/Monroe-University/<TERM>/<COURSE>/Chapter-Kits
```

`<TERM>` is the current term folder (for example `2026-Fall`); never assume it.
Section folder: `Chapter-NN/<section>/` (example: `Chapter-01/1.1/`). Scaffold
a new section with its contract boilerplate in the collecting state:

```sh
python3 "$SKILL_DIR/scripts/new_section.py" --kit "$KIT" --section 3.2 --week 3 --title "Measures of Variation"
```

It writes `state.json`, the `ledger.md` source table, and the
`practice-plan.md` header only, and refuses an existing folder. Take the week
from the course calendar.

**Do not copy** the user's PDFs, screenshots, or `.ppt`/`.pptx` into that
folder. Record the original path and any matching study-library or
`00-Course-Guide` slides in `Chapter-Kits/SOURCES.md`. If this course already
has `Week-XX/Materials/` or module slides for the same topic, register those
too — a Downloads drop is not the only source.

Read [references/source-and-batch-contract.md](references/source-and-batch-contract.md).
Each section has `state.json` (including a positive integer `"week"`) and a
source/coverage table in `ledger.md`. The hub groups import buttons under
that week. Do **not** infer week from `Chapter-NN` (IT-100 6.4 is Week 2).
"More coming" or "wait" means collecting: record receipt and gaps, but do not
replace notes, maps, or the live hub. On "go" mark ready for this batch; mark
coverage partial if material is still missing. Never infer full chapter coverage
from permission to process a batch. A requested draft uses the offline preview.

Chapter-Kits is canonical. Week `Work/` may point here. Week `Materials/`
gets this term's Blackboard files, not a second copy of textbook captures.

### 2. Extract locally

Follow [references/source-and-batch-contract.md](references/source-and-batch-contract.md)
for PDF, PPTX, legacy PPT, and screenshot handling. Keep originals in place.
The bundled extractor uses macOS Vision and accepts **PDF only**. Run once per
registered PDF, writing to a temporary text file before promotion:

```sh
if swift "$SKILL_DIR/scripts/ocr_pdf.swift" "$ORIGINAL_PDF" 3 > "$SECTION/ocr-$SOURCE_ID.pending.txt"; then
  mv "$SECTION/ocr-$SOURCE_ID.pending.txt" "$SECTION/ocr-$SOURCE_ID.txt"
else
  echo "Extraction failed; retain the previous verified text and inspect the source."
fi
```

For a `.pptx`, use the same pending-then-promote pattern:

```sh
if python3 "$SKILL_DIR/scripts/extract_pptx.py" "$ORIGINAL_PPTX" > "$SECTION/ocr-$SOURCE_ID.pending.txt"; then
  mv "$SECTION/ocr-$SOURCE_ID.pending.txt" "$SECTION/ocr-$SOURCE_ID.txt"
fi
```

`SOURCE_ID` is a stable unique ID from the ledger, not a basename that can collide.
An extractor error means stop dependent authoring. A successful exit still needs
visual checks of formulas, signs, units, tables, figures, and official answers.
PPTX text extract omits chart labels and speaker notes; inspect those slides
before maps or notes. Never reconstruct illegible source content from prior
knowledge. Tell the user what was extracted locally and which pages, if any,
remain unresolved.

### 3. Ledger

Write `$SECTION/ledger.md` before any map or notes:

- **Earned:** definitions, individuals/variables, worked examples, official
  quiz answers, source-taught traps, and lecture-objective items that the
  slides or figures actually teach. Each claim references a source ID,
  page/image/slide, and a short supporting excerpt or observation.
- **Uncertain:** unreadable material, contradictory sources, unavailable
  originals, and checklist objectives with no body on the extracted slides.
  Do not invent the missing procedure (spill recovery, USB eject, pizza
  analogy) from general knowledge.
- **Not earned:** later sections, syllabus previews, anything the PDF only
  names for later.

When the lecture file lists module or section objectives, that list is the
coverage spine. Do not invent traps the PDF does not contain.

### 4. Chapter maps

Read [references/visual-language.md](references/visual-language.md) first.
LR = left-to-right concept map. TD = top-down quiz-sort. A split case is one
set of individuals with two variables (1.1 pineapples).

Name files so the hub can find them: `*-concept-map.mmd`, `*-decision-flow.mmd`,
optional extra `*-flow.mmd`. At least one LR and one TD. Add a worked-example
map when the ledger has a split case. Add an extra legend flow for each earned
contrast (not only stats “levels / methods”). Add `*-error-flow.mmd` when the
source teaches mixups.

Each map has one job. Labels are **earned course language** from the ledger
(OCR, lecture objectives, inspected figures): `IPOS`, `stored program`,
`Individual`, `Appearance`. Stats 1.1 is the pattern. Do not invent quiz-show
phrasing a reader cannot match to the notes (`Can it load a new program?`).

A taxonomy root can be the module or section title. A quiz-sort root can be a
question the source actually asks. Leaves answer the job. Do not mix shop,
storage, and “what is a computer” on one chart. Extra legend maps when the
source has another contrast or section (shop, storage, instruction cycle, I/O).

Independent ideas after a named hub are a **parallel fork**, not a chain.
1.1: `VAR --> VT` and `VAR --> DS`.

**GoodNotes filing (per section):**

```text
Map/        concept-map + extra legend flows (contrasts, shop steps, tools)
Notes/      Core import only
Retrieval/  TD sort maps only (*-decision-flow.mmd, *-error-flow.mmd)
```

Do not put Quiz why or Retrieval markdown in Retrieval/. The student deletes
those notebooks if an older hub imported them. Sort maps stay.

### 5. Expand overall map

Read [references/expanding-map.md](references/expanding-map.md) and follow it.
Build `overall-flow.candidate.mmd` first. Validate against the untouched live
file before backing up and replacing it. Preserve old nodes, labels, and edges;
see the reference for the exact check and deliberate correction handling.

### 6. Notes + Practice.md + Core-only 414 split

Read [references/notes-contract.md](references/notes-contract.md),
[references/practice-planning.md](references/practice-planning.md), and
[references/overwhelm-scaffold.md](references/overwhelm-scaffold.md) first; they
own the detail. Order and non-negotiables:

1. Map first. Then one canonical `*Study-Notes.md`: numbered, unslop, portable
   GFM alerts only. Core follows the lecture's objective spine (A–E or
   equivalent), with level-2 source sections and level-3 idea headings. Each
   heading is 1–3 sentences plus a TEST MOVE, with a table when the source
   teaches a list. That shape is per heading, not a word-count ceiling that
   lets a 100-slide module collapse into ten recap headings.
2. **Quiz why** (disk only) explains why printed official answers are right.
   If the ledger has no official quiz, omit it; never synthesize one.
3. Write `$SECTION/practice-plan.md` before `Practice.md`: atomic source-backed
   decisions, `Q_min = A + H = <A> + <H> = <total>`, and a role for each item
   (**foundation**, **discriminate**, **transfer**). The count is a coverage
   heuristic, not proof of mastery. Outcome rows start with a numeric ID.
4. `$SECTION/Practice.md`: folded `[!question]-` callouts with the full question
   in the title and `**Answer:**`, `**Why:**`, `**Review:**` in the body. New
   wording of earned Core ideas only; no official stems, homework, or HTML quiz.
5. Study path: Map → Core → Practice on first contact; closed-book attempt
   before reopening Map/Core on return sessions. Adapt cues from actual
   attempts, never a learning-style label.
6. Run the editorial review in the notes contract before publishing. Report the
   Obsidian Reading-view fold check as pending when you cannot do it.
7. Check this section alone, even while other sections are still collecting:

   ```sh
   python3 "$SKILL_DIR/scripts/validate_kit.py" --section "$SECTION"
   ```

The builder reads one `*Study-Notes.md` per section and derives GoodNotes
imports from **Core only** (text before the first H1 titled Quiz why or
Retrieval). `Practice.md` is never a claim URL. Do not hand-edit derived
chunks. Short Core notes remain one import. Longer Core splits at level-1/2
headings using actual encoded URL length (default local budget 7600 characters;
this is a conservative setting, not a guaranteed service limit). Put source
sections at level-2 and idea headings at level-3 so a long Core splits A–E,
not mid-table. An oversized block fails with an actionable message: add a
meaningful heading without breaking a worked stem, table, or explanation.
Old Core/Quiz/Retrieval files are fallback inputs only when no canonical notes
exist; GoodNotes still gets Core only. Before first migration, the builder
compares old splits to canonical notes, allowing blank-line differences only. Conflicting content stops the
build for reconciliation. A successful live build saves `notes-migration.json`
with legacy hashes; later changes to those old files require review. Never
manually approve hashes without inspecting the diff.

If the user later sends the quiz they actually missed, fold those stems into
Quiz why **on disk**. Refresh Practice.md only with new-wording transfer items.
Do **not** re-import Quiz why into GoodNotes. Then **re-run step 7**.

### 7. Hub + HTTP 200

Claim URLs send encoded notes to `web.goodnotes.com`. No names, IDs, or
credentials in the markdown.

```text
python3 "$SKILL_DIR/scripts/build_goodnotes_hub.py" \
  --kit "$KIT" \
  --downloads
```

The script discovers `Chapter-NN/<section>/` maps and Core notes. Quiz-sort
maps (`*-decision-flow.mmd`, `*-error-flow.mmd`) get a **Retrieval maps** hub
row so they file into GoodNotes Retrieval/. Other maps file into Map/. Do not
hardcode a new section. Preserve Topic Card. Live Overall Map is `overall-flow.mmd`.
When the whole map no longer fits one claim URL, the builder splits it into
**Overall Map Ch N** buttons (root + that chapter's hubs and branches, styles
kept). It refuses a split that would drop a node or edge. The live file stays
one map; the split exists only in the hub. After the first split, tell the user
to delete the old single Overall Map notebook in GoodNotes.
Each course kit has its **own** import HTML. Put `hub.json` in that course’s
`Chapter-Kits/` (`title`, `editable_stem`, `preview_stem`, `prefix`,
`goodnotes_root`, `goodnotes_term`, `goodnotes_course`; the live contract
requires all seven). Give each `state.json` a short human `title` for its
section; the contract requires it. The hub prints the complete filing route
beside every import group:

```text
Monroe University → 2026 Fall → MA-235 Statistics → Week 03
→ 3.2 Measures of Variation → Map | Notes | Retrieval
```

The course-wide map goes in `00 Course Overview`. Create only routes printed by
the hub; do not create empty categories or a second folder for Practice.md.
Do not mix
MA-235 and EN-221 buttons in one file. A missing `hub.json` fails the live
contract; only an `--offline` preview falls back to the Statistics filenames.
The HTML groups buttons under collapsible **Week 1**, **Week 2**, … sections
from `state.json` `"week"`. Course-wide stays at the top. The latest week is
open; earlier weeks stay collapsed. Missing week is **Unscheduled** on offline
previews; live `--kit` requires a positive integer week.
It refuses a live rebuild while any registered batch is collecting or partial;
use `--offline` for a separately named, visibly unverified preview. Older sections
without state files remain readable and are reported as completeness unverified.

Run local validation first. `--kit` is the filing contract: hub.json, study-order
README, COURSE/week pointers, leftover pending files, section maps/notes, map
direction (concept map LR, sort maps TD), and `state.json` week, title, status,
and coverage. The live hub builder runs the same check and refuses to write if
it fails. Warnings (for example a legacy ledger with no `| S001 |` source rows)
do not block publishing; report them. Do not use `--offline` to skip filing.

```sh
python3 "$SKILL_DIR/scripts/validate_kit.py" --kit "$KIT"
python3 "$SKILL_DIR/scripts/validate_kit.py" --sources "$KIT/SOURCES.md"
```

Every claim URL must print `HTTP 200` before the live hub is written. On 414,
reduce `--max-url-chars` and rebuild. An HTTP response verifies reachability;
it does **not** prove successful import, editable diagrams, or legibility.
Inspect one changed map and the Core notes import in GoodNotes when browser
access is available; otherwise report import/render verification pending. Do
not create multiple imports merely to repeat a check. Confirm Practice.md in
Obsidian Reading view on a fold tap, not via the hub. An offline preview never
overwrites the published hub, derived imports, or Downloads copies.

The live builder writes derived notes into section `imports/` plus hub HTML and
link txt into Chapter-Kits; `--downloads` also exports the two hub files. It
compares the new claims with the previous link txt (ignoring the random map
claim ID) and prints **New**, **Changed**, and **Removed** imports. Tell the
user to re-import only those buttons; removed notebooks are deleted by hand in
GoodNotes, never automatically.
Older generated chunks may remain on disk but only current discovered inputs
appear in the hub. Do not delete them automatically.

### 8. File into Chapter-Kits

Write `Chapter-Kits/README.md` with study order (Map → Core Notes → Retrieval
sort maps → Obsidian Practice.md) and the AirDrop filename from `hub.json`.
Write `Chapter-NN/README.md` (sections present, earned vs not earned).
Point that week’s `Work/README.md` and `Materials/README.md`, plus `COURSE.md`,
at the kit. Do not copy hub HTML or maps into `Work/`.
Delete leftover `ocr-*.pending.txt` after promote or failed inspect.
Delete `overall-flow.candidate.mmd` after it becomes live + `.prev`.

```text
Chapter-Kits/            # one folder per course; do not mix EN-221 into MA-235
  hub.json               # title, HTML stem, prefix — separate import panel
  overall-flow.mmd
  overall-flow.prev.mmd
  <editable_stem>.html   # e.g. English-Editable-GoodNotes.html
  <editable_stem>-link.txt
  preserved-claims.json
  Chapter-NN/README.md
  Chapter-NN/<section>/   # state.json, ledger, maps, canonical notes, Practice.md, extracted text
  Chapter-NN/<section>/imports/  # derived GoodNotes Core markdown; do not edit
  SOURCES.md              # pointers to slides / original PDFs
```

## Done

- New nodes exist only on the earned overall map plus that section's maps.
- Local checks passed; HTTP and actual import/render checks reported separately.
- Notes are source-grounded, editorially reviewed, and follow the lecture
  checklist. `practice-plan.md` reconciles the outcome count to eligible
  Practice questions; `Practice.md` is tap-to-reveal transfer, not the book quiz.
- Batch marked complete only after local, HTTP, and actual import checks pass.
  Otherwise keep ready and report exactly which verification remains pending.
  Source coverage may still be partial; complete does not mean mastered.
- User can AirDrop the published hub HTML to iPad.
- Every hub import group prints its exact GoodNotes destination using named,
  two-digit week folders; Practice.md remains in Obsidian.

## Examples

**User:** "here is 1.2" + PDFs
→ OCR each original PDF into `ocr-*.txt` (leave PDFs in Downloads), map any
matching slides in `SOURCES.md`, ledger, 1.2 maps, backup overall map, add
`CH1_2` beside `CH1_1`, Core notes + Practice.md + Core-only 414 split, rebuild
hub (discovery picks up 1.2). File the quiz-sort map into GoodNotes Retrieval/.

**User:** "IT files in Downloads" + existing Week Materials
→ Register Downloads *and* on-disk week/course-guide files. Inspect figure
slides, not only `extract_pptx.py` text. IT-100/Chapter-Kits with hub.json stem
`IT-Editable-GoodNotes`. Core follows the lecture A–E checklist; maps use
module terms plus extra legends for shop, storage, processor, I/O. Point
COURSE.md and Week Work/ at the kit. Do not merge into the Statistics HTML.
Do not fill the assignment.

**User:** "English Everyday Use + separate import HTML"
→ OCR story/lecture in place, EN-221/Chapter-Kits with hub.json stem
`English-Editable-GoodNotes`, maps + Core + Practice.md, live hub. Do not merge
into the Statistics HTML. Do not fill the worksheet.

**User:** "Communication slides + own import HTML"
→ LA-122/Chapter-Kits with hub.json prefix Communication and stem
`Communication-Editable-GoodNotes`. Do not merge into English or Statistics HTML.

**User:** "html pages are getting cluttered, add week sections"
→ Group every course hub HTML under collapsible Week 1 / Week 2 from
`state.json` `"week"`. Rebuild all published import HTML. Do not infer week from
Chapter-NN.

**User:** "GoodNotes of this quiz I failed" + screenshots
→ read the images **in place**, fold those stems into Quiz why on disk, refresh
Practice.md with new-wording items if needed, re-run the hub for maps/Core only.
Do not copy the PNGs into Chapter-Kits. Do not replace the PDF quiz. Do not
import the missed quiz as a GoodNotes notebook.
