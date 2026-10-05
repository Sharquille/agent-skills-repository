---
name: chapter-study-kit
description: >-
  Builds an expanding Monroe chapter study kit for any course (MA-235, EN-221,
  IT-100, LA-122, later). OCR from the original PDF or PowerPoint path, Core notes,
  mermaid maps (TD sort maps for Retrieval), Obsidian Practice.md, and one
  GoodNotes notebook PDF per section. Use when the user sends a chapter
  PDF, quiz notes, GoodNotes screenshots, flow map, or asks to expand that
  course’s overall map. Do not copy PDFs or screenshots into Chapter-Kits. Do
  not put Quiz why or Retrieval prose in the GoodNotes notebook. Do not mix two
  courses in one notebook. Do not use for week-folder bootstrap
  (continue-study-week), graded submission writing, or Obsidian
  visualize-study-chapter. Consult only if this turn names a panel.
---

# Chapter study kit

Workflow version: **2.9.1**. Read the canonical version before executing a synced copy.

Turn one **section** into a kit: maps + Core notes, Obsidian `Practice.md`
for self-test, and one GoodNotes notebook PDF that holds the maps and Core. Grow the overall course map only with
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
and the kit contract files only.

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

Notebook pages must not carry student IDs, emails, or credentials.

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
- [ ] 6. Source-grounded editorial review + Practice outcome plan + Core notes
- [ ] 7. `validate_kit.py --kit` then the GoodNotes notebook PDF
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
source/coverage table in `ledger.md`. The section notebook is filed under
that week. Do **not** infer week from `Chapter-NN` (IT-100 6.4 is Week 2).
"More coming" or "wait" means collecting: record receipt and gaps, but do not
replace notes, maps, or published notebooks. On "go" mark ready for this batch; mark
coverage partial if material is still missing. Never infer full chapter coverage
from permission to process a batch. The notebook builder refuses collecting or
partial sections, so a requested draft stays as files on disk.

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

Name files so the notebook builder can find them: `*-concept-map.mmd`, `*-decision-flow.mmd`,
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

**Where each map lands in the section notebook:**

```text
Map pages        concept map (plus one page per section hub when it is large)
                 + extra legend flows (contrasts, shop steps, tools)
Retrieval pages  TD sort maps only (*-decision-flow.mmd, *-error-flow.mmd),
                 each behind a blank "redraw from memory" page
```

Quiz why and Retrieval prose never go in the notebook. Sort maps stay.

### 5. Expand overall map

Read [references/expanding-map.md](references/expanding-map.md) and follow it.
Build `overall-flow.candidate.mmd` first. Validate against the untouched live
file before backing up and replacing it. Preserve old nodes, labels, and edges;
see the reference for the exact check and deliberate correction handling.

### 6. Notes + Practice.md

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

The notebook builder reads one `*Study-Notes.md` per section and prints
**Core only** (text before the first H1 titled Quiz why or Retrieval).
`Practice.md` never goes in the notebook. Put source sections at level-2 and
idea headings at level-3: each level-2 section starts a new page, so a long
Core reads A–E with room to write.

If the user later sends the quiz they actually missed, fold those stems into
Quiz why **on disk**. Refresh Practice.md only with new-wording transfer items.
Do **not** put Quiz why in the notebook. Then **re-run step 7**.

### 7. GoodNotes notebook PDF

Run local validation first. `--kit` is the filing contract: hub.json, study-order
README, COURSE/week pointers, leftover pending files, section maps/notes, map
direction (concept map LR, sort maps TD), and `state.json` week, title, status,
and coverage. Warnings (for example a legacy ledger with no `| S001 |` source
rows) do not block publishing; report them.

```sh
python3 "$SKILL_DIR/scripts/validate_kit.py" --kit "$KIT"
python3 "$SKILL_DIR/scripts/validate_kit.py" --sources "$KIT/SOURCES.md"
python3 "$SKILL_DIR/scripts/build_section_pdf.py" --kit "$KIT" --section 3.2 --downloads
```

Omit `--section` to rebuild every section (after a style change, for example).
Each section becomes one PDF in its week's `Work/` folder, named
`<COURSE>_<section>_<Title>_GoodNotes.pdf`, and `--downloads` copies it to
Downloads for AirDrop. Every run also rebuilds
`00-Course-Guide/<COURSE>_Course-Overview_GoodNotes.pdf` from `overall-flow.mmd`:
the whole map, then one page per chapter. The live file stays one map.

Notebook order: cover (course, week, contents, study path) → map pages (a
concept map with 4+ hubs and 20+ edges also gets one page per hub) → legend
flows → Core notes with a ruled writing margin, each level-2 section on a new
page → for each sort map, a blank "redraw from memory" page, then the map to
check → scratch pages. Tall diagrams print on portrait pages, wide ones on
landscape.

Dependencies: Google Chrome (headless print), the Python `markdown` package,
and a network connection, because Mermaid loads from jsDelivr. Chrome renders
the page twice: first a DOM dump, and the build stops unless every Mermaid
diagram drew without a syntax error; then the print. A failed build leaves the
previous PDF in place. The builder refuses a section whose batch is collecting
or partial.

`hub.json` names the course for the cover and the filing contract (`title`,
`prefix`, `goodnotes_root`, `goodnotes_term`, `goodnotes_course`); give each
`state.json` a short human `title`. Filing in
GoodNotes is one notebook per section:

```text
Monroe University → 2026 Fall → MA-235 Statistics → Week 03
→ 3.2 Measures of Variation   (one notebook)
Monroe University → 2026 Fall → MA-235 Statistics → 00 Course Overview
→ Course map   (one notebook)
```

A rebuilt notebook replaces the old one in GoodNotes: the user deletes the old
notebook by hand, never automatically. Rendering is checked locally; whether it
reads well on the iPad is a separate check. Report it pending until the user
confirms. Confirm Practice.md in Obsidian Reading view on a fold tap.

### 8. File into Chapter-Kits

Write `Chapter-Kits/README.md` with study order (Map → Core Notes → Retrieval
sort maps → Obsidian Practice.md) and the notebook naming rule.
Write `Chapter-NN/README.md` (sections present, earned vs not earned).
Point that week’s `Work/README.md` and `Materials/README.md`, plus `COURSE.md`,
at the kit and list the section notebook PDF. Do not copy maps or notes into
`Work/`; the notebook PDF is the only kit output there.
Delete leftover `ocr-*.pending.txt` after promote or failed inspect.
Delete `overall-flow.candidate.mmd` after it becomes live + `.prev`.

```text
Chapter-Kits/            # one folder per course; do not mix EN-221 into MA-235
  hub.json               # course name, prefix, GoodNotes route
  overall-flow.mmd
  overall-flow.prev.mmd
  Chapter-NN/README.md
  Chapter-NN/<section>/   # state.json, ledger, maps, canonical notes, Practice.md, extracted text
  SOURCES.md              # pointers to slides / original PDFs
Week-NN_.../Work/<COURSE>_<section>_<Title>_GoodNotes.pdf
00-Course-Guide/<COURSE>_Course-Overview_GoodNotes.pdf
```

## Done

- New nodes exist only on the earned overall map plus that section's maps.
- Local checks and the notebook render check passed; the on-iPad check is
  reported separately.
- Notes are source-grounded, editorially reviewed, and follow the lecture
  checklist. `practice-plan.md` reconciles the outcome count to eligible
  Practice questions; `Practice.md` is tap-to-reveal transfer, not the book quiz.
- Batch marked complete only after local checks, the render check, and the
  user's on-iPad check pass. Otherwise keep ready and report exactly which
  verification remains pending. Source coverage may still be partial; complete
  does not mean mastered.
- User can AirDrop one notebook PDF per section (plus the course map) to iPad.
- The summary names each notebook's GoodNotes destination using two-digit week
  folders; Practice.md remains in Obsidian.

## Examples

**User:** "here is 1.2" + PDFs
→ OCR each original PDF into `ocr-*.txt` (leave PDFs in Downloads), map any
matching slides in `SOURCES.md`, ledger, 1.2 maps, backup overall map, add
`CH1_2` beside `CH1_1`, Core notes + Practice.md, then build the 1.2 notebook
PDF (its sort map lands on the Retrieval pages) and the refreshed course map.

**User:** "IT files in Downloads" + existing Week Materials
→ Register Downloads *and* on-disk week/course-guide files. Inspect figure
slides, not only `extract_pptx.py` text. IT-100/Chapter-Kits with hub.json prefix
`IT`. Core follows the lecture A–E checklist; maps use module terms plus extra
legends for shop, storage, processor, I/O. Point COURSE.md and Week Work/ at the
kit. Do not fill the assignment.

**User:** "English Everyday Use"
→ OCR story/lecture in place, EN-221/Chapter-Kits with hub.json prefix
`English`, maps + Core + Practice.md, section notebook PDF. Do not fill the
worksheet.

**User:** "Communication slides"
→ LA-122/Chapter-Kits with hub.json prefix Communication; its notebooks file
under LA-122 Communication, never inside another course.

**User:** "the notebook layout needs a wider margin"
→ Change the style in `build_section_pdf.py`, run the tests, then rebuild every
course without `--section`. Tell the user which notebooks to replace in GoodNotes.

**User:** "GoodNotes of this quiz I failed" + screenshots
→ read the images **in place**, fold those stems into Quiz why on disk, refresh
Practice.md with new-wording items if needed, rebuild that section's notebook.
Do not copy the PNGs into Chapter-Kits. Do not replace the PDF quiz. Do not
put the missed quiz in a GoodNotes notebook.
