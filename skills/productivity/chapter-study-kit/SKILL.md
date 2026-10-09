---
name: chapter-study-kit
description: >-
  Builds an expanding Monroe chapter study kit for any course (MA-235, EN-221,
  IT-100, LA-122, later): local OCR from the original PDF, PowerPoint, or
  screenshots, a source ledger, mermaid concept and sort maps, Core notes, an
  Obsidian Practice.md bank, and one GoodNotes notebook PDF per section plus a
  course-map notebook. Use when the user sends a chapter or section PDF,
  lecture slides, quiz notes, GoodNotes screenshots, or a flow map, asks to
  expand a course's overall map, or wants kit notebooks rebuilt or restyled.
  Do not use for week-folder bootstrap (continue-study-week), testing the
  learner on finished kits (chapter-competency-loop), ELI5 pages
  (eli5-explainer), Obsidian visualize-study-chapter, or graded submission
  writing. Every section build gets a read-only Sol review; other consult
  panels run only when this turn names one.
# --- provenance ---
category: productivity
source: self-authored (this repository); migrated from Education/.cursor/skills
author: Sharquille Andrew
license: MIT
retrieved: 2026-09-23
---

# Chapter study kit

Workflow version: **2.15.0**. Read the canonical version before executing a synced copy.

Turn one **section** into a kit: maps + Core notes, Obsidian `Practice.md`
for self-test, and one GoodNotes notebook PDF that holds the maps and Core. Grow the overall course map only with
concepts supported by supplied sources. Chapter-Kits stays light: no textbook
PDFs, no screenshot dumps, no copied slide decks. No per-section HTML quiz.

```text
SKILL_DIR=/Users/sharquilleandrew/Documents/development/github-local/agent-skills-repository/skills/productivity/chapter-study-kit
```

Run scripts from `$SKILL_DIR/scripts/`; never fetch them from the network. Edit
only this canonical folder; if a synced copy's version differs, use the
canonical instructions and report drift. Editing the skill itself (tests,
manifest, synced copies, Mermaid bump):
[references/maintaining.md](references/maintaining.md).

## Requirements

- macOS with Swift (Vision OCR) and Google Chrome at the default path.
- `python3` 3.10+ with the `markdown` package for the notebook builder; the
  Homebrew `python3` qualifies, `/usr/bin/python3` (3.9, no `markdown`) does
  not. The validator, scaffolder, PPTX extractor, and sync script are stdlib
  only and also run on 3.9.
- Network only for a notebook build: Chrome loads a pinned, integrity-checked
  Mermaid, and KaTeX when Core has math, from jsDelivr. Notes, maps, and
  sources never leave the Mac.

## Non-negotiables

- Do not git-init Monroe-University. Do not write graded posts or homework for
  submission; teach the method on a different example. Do not copy prior
  students' work.
- Read PDFs, PowerPoints, and screenshots **in place** (Downloads, Desktop,
  chat). Never copy them into Chapter-Kits, which holds only maps, notes,
  ledger, extracted text, and the kit contract files.
- A map node, Core heading, or trap needs ledger evidence from this section's
  sources. Never seed from a syllabus preview or prior knowledge.
- Quiz why and Retrieval prose stay on disk; the notebook prints maps and Core
  only. `Practice.md` stays in Obsidian.
- One course per Chapter-Kits folder and per notebook.
- Notebook pages carry no student IDs, emails, credentials, or personal
  filenames.
- Kits under `Monroe-University/` are sources-only: no web research and no
  CURRENT EXAM callouts. Other kits may research relevance on the web, pinned
  to the exam version studied
  ([references/relevance-research.md](references/relevance-research.md)).
- Coverage is what the sources supplied; understanding is what the student has
  shown. Never infer mastery from a finished kit or invent attempts, scores,
  or dates.

## Routing

| Request | Skill |
| --- | --- |
| Chapter or section sources, GoodNotes maps, expand the overall map, rebuild notebooks | this skill |
| Open a week folder, "bootstrap week N" | `continue-study-week` (a Cursor skill in `Education/.cursor/skills`; if it is not available here, say so instead of improvising) |
| "Test me", "am I ready", practice exam on finished sections | `chapter-competency-loop` (reads this kit's Core, ledger, `practice-plan.md`, and `study-log.md`) |
| ELI5 or picture-first page for one section | `eli5-explainer` (an optional view, not a kit file) |
| Sol review of every section build | [references/sol-review.md](references/sol-review.md); always, before the notebook |
| A named consult panel | [references/consult-panel.md](references/consult-panel.md); skip it on a routine drop |

## Workflow

```text
- [ ] 0. Non-negotiables (no git-init, no graded writing, no unearned map nodes)
- [ ] 1. Check batch state, register original sources, and wait if collecting
- [ ] 2. Extract locally by format; verify every page/image/slide
- [ ] 3. Write ledger.md (earned / not earned / relevance tiers); research relevance if allowed
- [ ] 4. Chapter maps
- [ ] 5. Expand overall map (backup first)
- [ ] 6. Source-grounded editorial review + Practice outcome plan + Core notes + figures
- [ ] 7. Sol review, then `validate_kit.py --kit` and the GoodNotes notebook PDF
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
from the course calendar, never from `Chapter-NN` (IT-100 6.4 is Week 2); the
section notebook is filed under that week.

Every kit names its course profile in `hub.json` (`quantitative`, `technical`,
`security`, or `general`); the validator refuses a kit without one. Read
[references/course-profiles.md](references/course-profiles.md) to pick it and
for what it changes. A `security` kit (CompTIA Security+ lives at
`Education/IT-Certifications/ComptiaSec+/Chapter-Kits`) also keeps
`objectives.md`, the exam objective items mapped to sections, and
`acronyms.md`, the official acronym list with the sections that use each.

Record each original path in the ledger source table and any matching slides in
`Chapter-Kits/SOURCES.md`. Register what is already on disk too: a PowerPoint
or lecture deck in `01-Study-Library/` or `00-Course-Guide/`, and this course's
`Week-XX/Materials/` or module slides for the same topic. A Downloads drop is
not the only source. Use current course slides for course emphasis and textbook
captures for supplied explanations and examples. Check actual section coverage
and edition; do not replace a detailed source with an overview deck just
because slides exist. Record conflicts and gaps instead of silently resolving
them.

Batch state follows
[references/source-and-batch-contract.md](references/source-and-batch-contract.md).
"More coming" or "wait" means collecting: record receipt and gaps, but do not
replace notes, maps, or published notebooks. A requested interim draft stays
collecting as files on disk. On "go" mark ready for this batch; mark coverage
partial if material is still missing. Never infer full chapter coverage from
permission to process a batch. The notebook builder refuses a collecting
section.

Chapter-Kits is canonical. Week `Work/` may point here. Week `Materials/`
gets this term's Blackboard files, not a second copy of textbook captures.

### 2. Extract locally

The contract's extraction routes cover PDF, PPTX, legacy PPT, and screenshots.
The bundled OCR uses macOS Vision and accepts **PDF only**. Run once per
registered PDF, writing to a temporary text file before promotion:

```sh
if swift "$SKILL_DIR/scripts/ocr_pdf.swift" "$ORIGINAL_PDF" 3 > "$SECTION/ocr-$SOURCE_ID.pending.txt"; then
  mv "$SECTION/ocr-$SOURCE_ID.pending.txt" "$SECTION/ocr-$SOURCE_ID.txt"
else
  echo "Extraction failed; retain the previous verified text and inspect the source."
fi
```

For a `.pptx`, run `python3 "$SKILL_DIR/scripts/extract_pptx.py" "$ORIGINAL_PPTX"`
through the same pending-then-promote pattern. It omits chart labels, image
text, and speaker notes; inspect those slides before maps or notes.
`SOURCE_ID` is a stable unique ID from the ledger, not a basename that can
collide. An extractor error means stop dependent authoring. A successful exit
still needs visual checks of formulas, signs, units, tables, figures, and
official answers. Never reconstruct illegible source content from prior
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
- **Relevance:** tag each earned item Tier 1 (tested: an objective line, an
  official quiz answer, or a source-taught trap; name the match), Tier 2
  (supporting: a Tier 1 explanation needs it), or Tier 3 (context). Tier 3
  items go in a **Context** list and stay out of Core. Rules:
  [references/notes-contract.md](references/notes-contract.md#relevance-first).

Relevance research ranks Tier 1 items and marks the heaviest **HIGH YIELD**.
Outside `Monroe-University/`, with `"relevance_research": "web"` and `"exam"`
in `hub.json`, check the current objectives and credible sources for the
pinned exam version when the network is available, and record them in the
kit's `relevance.md`; offline, rank from `objectives.md` and the sources.
Read [references/relevance-research.md](references/relevance-research.md)
first. Set `state.json` `revised` to the date whenever Core is rewritten.

Screenshots earn ledger entries and map nodes as a textbook page does; later
screenshots may fill gaps in the same section once their evidence is recorded.
File format does not decide what is earned. When the lecture file lists module
or section objectives, that list is the coverage spine. Do not invent traps the
source does not contain.

### 4. Chapter maps

Read [references/visual-language.md](references/visual-language.md) first: it
owns the palette, one job per map, earned course-language labels, and parallel
forks. LR = left-to-right concept map. TD = top-down quiz-sort. A split case is
one set of individuals with two variables (1.1 pineapples).

Name files so the notebook builder can find them: `*-concept-map.mmd`, `*-decision-flow.mmd`,
optional extra `*-flow.mmd`. At least one LR and one TD. Add a worked-example
map when the ledger has a split case. Add an extra legend flow for each earned
contrast or section (shop, storage, instruction cycle, I/O), not only stats
"levels / methods". Add `*-error-flow.mmd` when the source teaches mixups.
Name a homework bridge tool `*-bridge-tool.mmd`: it stays on disk beside its
notes and never prints in the notebook, because the section does not earn it.

**Where each map lands in the section notebook:**

```text
Map pages        concept map (plus one page per section hub when it is large)
                 + extra legend flows (contrasts, shop steps, tools)
Retrieval pages  TD sort maps only (*-decision-flow.mmd, *-error-flow.mmd),
                 each behind a blank "redraw from memory" page
```

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
   equivalent), with level-2 source sections and level-3 idea headings. It
   prints Tier 1 items and what they depend on, and says each fact once: a
   visual wherever an idea has structure, prose only for the reason or
   decision the visual cannot show, and definitions in margin TERMS boxes
   beside first use. Each heading follows the notes contract's explanation
   order (what it is, why it works when not already plain, a builds-on tag, a
   worked example for a calculation, TEST MOVE as clue and decision).
   Notation-heavy sections open with a Symbols table; math is `$...$`.
   Codes and labels are spelled out before use; every formula gets Read it
   aloud / Use it when / Don't use it when; several formulas get a Which rule
   table.
   Worked examples use Situation / Given / Steps / Answer / Check, and every
   number is given or produced by a visible step.
   The kit's profile adds its own rules on top
   ([references/course-profiles.md](references/course-profiles.md)): margin
   TERMS for every abbreviation in technical and security kits, scenario-clue
   TEST MOVEs and objective-driven relevance for security kits, and figures
   only for structure in general kits. When rewriting an existing Core, keep
   every Tier 1 item, figure, and Practice item; move cut detail to the
   ledger's Context list, and compare old and new Tier 1 coverage before
   rebuilding.
2. **Figures** (default for every section): follow the Figures section of
   [references/visual-language.md](references/visual-language.md). One idea
   per figure after the text it shows, built with `scripts/svg_figure.py`,
   saved beside the notes, embedded as `![idea](file.svg)`; one
   `> [!TIP]` **SKETCH:** or **RECALL:** margin prompt per level-2 group.
   Render and inspect each figure page before release.
3. **Quiz why** (disk only) explains why printed official answers are right.
   If the ledger has no official quiz, omit it; never synthesize one.
4. Write `$SECTION/practice-plan.md` before `Practice.md`: atomic source-backed
   decisions, `Q_min = A + H = <A> + <H> = <total>`, and a role for each item
   (**foundation**, **discriminate**, **transfer**). The count is a coverage
   heuristic, not proof of mastery. Outcome rows start with a numeric ID.
5. `$SECTION/Practice.md`: folded `[!question]-` callouts with the full question
   in the title and `**Answer:**`, `**Why:**`, `**Review:**` in the body. New
   wording of earned Core ideas only; no official stems, homework, or HTML quiz.
6. Study path: Map → Core → Practice on first contact; closed-book first on
   return. Adapt cues from actual attempts, never a learning-style label.
7. Run the editorial review in the notes contract before publishing. Report the
   Obsidian Reading-view fold check as pending when you cannot do it.
8. Check this section alone, even while other sections are still collecting:

   ```sh
   python3 "$SKILL_DIR/scripts/validate_kit.py" --section "$SECTION"
   ```

9. **Sol review.** Send the section to Sol through `agent-orchestra` with
   `scripts/review_brief.py` (add `--before` with the old notes on a rewrite),
   check each finding against the ledger and sources, apply what holds up,
   rerun item 8, and record `verification.review` and `review_note` in
   `state.json`. Several sections run in parallel, one call each. Commands,
   fallbacks, and how to judge findings:
   [references/sol-review.md](references/sol-review.md).

If the user later sends the quiz they actually missed, fold those stems into
Quiz why **on disk**. Refresh Practice.md only with new-wording transfer items,
then **re-run item 8 above**.

### 7. GoodNotes notebook PDF

Run local validation first. `--kit` is the filing contract: hub.json, study-order
README, COURSE/week pointers, leftover pending files, section maps/notes, map
direction (concept map LR, sort maps TD), and `state.json` week, title, status,
coverage, verification, figures (safe, labelled, palette-only SVGs whose
numbers the notes or ledger supply), and worked examples (all five parts, every
number traced). Warnings (for example a legacy ledger with no
`| S001 |` source rows, or free-text verification values) do not block
publishing; report them.

```sh
python3 "$SKILL_DIR/scripts/validate_kit.py" --kit "$KIT"
python3 "$SKILL_DIR/scripts/validate_kit.py" --sources "$KIT/SOURCES.md"
python3 "$SKILL_DIR/scripts/build_section_pdf.py" --kit "$KIT" --section 3.2
```

`validate_kit.py --section` takes a folder path; `build_section_pdf.py
--section` takes the section ID. Omit `--section` to rebuild every section
(after a style change, for example). Each section becomes one PDF in its week's
`Work/` folder, named `<COURSE>_<section>_<Title>_GoodNotes.pdf`. That copy
is the one to open; pass `--downloads` (a copy to Downloads for AirDrop) only
when the user asks, because the duplicates pile up. Every run also rebuilds
`00-Course-Guide/<COURSE>_Course-Overview_GoodNotes.pdf` from `overall-flow.mmd`:
the whole map, then one page per chapter. The live file stays one map.

Notebook order: cover → map pages (step 4) → Core with its figures and a ruled
writing margin holding the SKETCH/RECALL prompts, each level-2 section after
the first on a new page → redraw-then-check Retrieval pages →
scratch pages. Core is the text before the first H1 titled Quiz why or
Retrieval. A concept map with 4+ hubs and 20+ edges also gets one page per hub.
The build stops unless every Mermaid diagram drew and every equation typeset
without an error, and a failed build leaves the previous PDF in place.

`hub.json` names the course for the cover and the filing contract (`title`,
`prefix`, `goodnotes_root`, `goodnotes_term`, `goodnotes_course`); give each
`state.json` a short human `title`. Filing in GoodNotes is one notebook per
section:

```text
Monroe University → 2026 Fall → MA-235 Statistics → Week 03
→ 3.2 Measures of Variation   (one notebook)
Monroe University → 2026 Fall → MA-235 Statistics → 00 Course Overview
→ Course map   (one notebook)
```

A rebuilt notebook replaces the old one in GoodNotes: the user deletes the old
notebook by hand, never automatically. After a build that passed, set
`verification.local` and `verification.render` to `passed` in `state.json`.
Whether it reads well on the iPad is the separate `verification.import` check:
report it pending until the user confirms. When the user says it reads well,
set `import` to `passed` and `status` to `complete`; the validator rejects
`complete` while any check is not `passed`. Also confirm Practice.md in
Obsidian Reading view on a fold tap.

### 8. File into Chapter-Kits

Write `Chapter-Kits/README.md` with study order (Map → Core Notes → Retrieval
sort maps → Obsidian Practice.md) and the notebook naming rule.
Write `Chapter-NN/README.md` (sections present, earned vs not earned).
Point that week's `Work/README.md` and `Materials/README.md`, plus `COURSE.md`,
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
- Sol reviewed the section, its findings were checked and resolved, and
  `state.json` records the result.
- Local checks and the notebook render check passed; the on-iPad check is
  reported separately.
- Notes are source-grounded, editorially reviewed, and follow the lecture
  checklist. Core prints Tier 1 items and their support once each, with
  definitions in the margin; Tier 3 context sits in the ledger. Core figures
  show each spatial or contrastive idea, and every level-2 group has one margin
  prompt. `practice-plan.md` reconciles the outcome count to eligible Practice
  questions; `Practice.md` is tap-to-reveal transfer, not the book quiz.
- Status is complete only per step 7; otherwise it stays ready and the
  summary names each pending check. Complete does not mean mastered.
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

**User:** "English Everyday Use" or "Communication slides"
→ OCR in place into that course's own kit: EN-221/Chapter-Kits with hub.json
prefix `English`, or LA-122/Chapter-Kits with prefix `Communication`. Its
notebooks file under that course only. Do not fill the worksheet.

**User:** "the notebook layout needs a wider margin"
→ Change the style in `build_section_pdf.py`, run the tests, then rebuild every
course without `--section`. Tell the user which notebooks to replace in GoodNotes.

**User:** "GoodNotes of this quiz I failed" + screenshots
→ read the images **in place**, fold those stems into Quiz why on disk, refresh
Practice.md with new-wording items if needed, rebuild that section's notebook.
Do not copy the PNGs into Chapter-Kits. Do not replace the PDF quiz. Do not
put the missed quiz in a GoodNotes notebook.

**User:** "3.2 looks good on the iPad"
→ Set that section's `verification.import` to `passed` and `status` to
`complete`, run `validate_kit.py --kit`, and report that complete means the
batch is verified, not that the section is mastered.
