---
name: assignment-workspace
description: "Build local HTML workspaces for a Monroe graded assignment or discussion (EN-221 essays, POV rewrites, reflections, discussion posts and replies; IT-100 Word/PowerPoint/Excel tasks) and coach the learner through writing it. Reads the captured prompt in the week's Work/prompts/, then builds: a workspace page (requirements checklist, one autosaving box per question or paragraph with sentence and word counters, evidence and where-to-look notes, MLA Works Cited, copy-all); a highlighting reader that opens each course text at the right paragraph with key phrases marked and click-to-copy citations; and, on request, an annotated scene or a model example on invented content. Then reviews each pasted paragraph against the prompt and source text with marked, minimal edits. Use when the learner says set up a workspace, make me a sheet or .html for this assignment, help me write my essay, discussion post, or reflection, check my paragraph, or check my Google Doc before submitting. Do not use to write graded answers for the learner, for chapter notes or GoodNotes kits (chapter-study-kit), for quizzes on finished chapters (chapter-competency-loop), or for ELI5 pages (eli5-explainer)."
# --- provenance ---
category: productivity
source: self-authored (this repository)
author: Sharquille Andrew
license: MIT
retrieved: 2026-11-01
---

# Assignment workspace

Turn one graded assignment into local pages that hold the prompt, the
evidence, and the learner's own writing, then coach the draft to submission.
The learner writes every graded sentence. This skill builds the scaffolding,
finds the evidence, and checks the work.

Workflow version: **1.1.0**

```text
SKILL_DIR=/Users/sharquilleandrew/Documents/development/github-local/agent-skills-repository/skills/productivity/assignment-workspace
```

## Non-negotiables

- **The learner writes graded text.** Plans, beat lists, evidence, frames
  with blanks, and marked edits of the learner's own sentences are fine. Never
  add a new sentence to a graded answer; put a bracketed prompt
  (`[YOUR SENTENCE: …]`) where one is needed. Details in
  [references/coaching-rules.md](references/coaching-rules.md).
- **Prompt first.** Read every image or file in the week's `Work/prompts/`
  before building. Record the due date, time zone, length rules (paragraphs,
  sentences per paragraph, words, pages), font, citation style, and every
  sub-question. If a prompt is missing, ask for it. Do not guess the task.
- **Evidence is verbatim and located.** Every quote shown to the learner
  comes from the course file, with the printed page (or the handout page when
  none is printed) and the paragraph number. Fix obvious scan errors and say
  so. Tell the learner to check exact wording against the original page.
- **Local HTML in the week's `Work/` folder,** not artifacts. Follow the page
  contract in [references/page-contract.md](references/page-contract.md).
  Send each new page with `SendUserFile` (display `render`), because relative
  links break when the session's folder changes.
- **No mixing.** One assignment per workspace. Keep group projects and
  individual work in separate pages and separate replies.

## Routing

| Request | Skill |
| --- | --- |
| Workspace, reader, annotated scene, model example, paragraph or Doc check for a graded task | this skill |
| Chapter notes, GoodNotes notebook, course map | `chapter-study-kit` |
| "Test me" on finished chapters | `chapter-competency-loop` |
| Picture-first explainer for a concept | `eli5-explainer` |
| The learner is lost on a concept mid-assignment | `teach-complex-concepts`, then return here |
| Deadlines into Reminders and Calendar | `study-deadlines` |

## Workflow

1. **Capture.** Read the prompt images or files, the rubric if present, and
   the week's `Materials/`. Find the course texts and any kit OCR
   (`Chapter-Kits/<chapter>/<section>/ocr-*.txt`, `ledger.md`) for the text,
   page markers, and known OCR faults.
2. **Status table.** Tell the learner each deliverable, its due date and time
   zone, what's late, and the order to do it in (late and short first,
   biggest piece next, replies last).
   Then record every deadline in the week's `deadlines.json` and sync it to
   Reminders and Calendar with `study-deadlines`.
3. **Plan from the learner's material.** For personal or reflective
   questions, ask for their story or context first. Build angles and beat
   lists from what they give and from this semester's texts they already
   know. Flag factual traps early, such as a wrong decade, a word that means
   something else ("cartel"), or a detail that contradicts the text.
4. **Build the workspace page** ([page-contract.md](references/page-contract.md)):
   requirements checklist, plan, one box per question or paragraph, counters
   matched to the prompt's limits, Works Cited, and copy-all.
5. **Build the reader** when the task uses course texts. Write a spec
   ([reader-spec.md](references/reader-spec.md)), then run
   `python3 -I "$SKILL_DIR/scripts/build_reader.py" spec.json <Work>/<COURSE>_WeekN_Reader.html`.
   The build fails if a highlight phrase is not verbatim in its paragraphs.
   Link every evidence question in the workspace to `Reader.html#<question-id>`.
6. **Optional pages, on request:** an annotated scene (source excerpt split
   into scraps, with numbered notes under the highlights and gaps the original
   narrator left), or a model example on invented, unrelated content that
   shows the shape with notes on which requirement each part meets.
7. **Coach paragraph by paragraph** ([coaching-rules.md](references/coaching-rules.md)).
   Check each paste against the prompt, the source, and the earlier
   paragraphs. When asked for an updated version, return the learner's text
   with only marked fixes.
8. **Final check.** Read the submitted file (Google Doc through the Drive
   connector, or a local .docx/.pptx/.xlsx by unzipping the XML). Check the
   heading, title, length, citations, Works Cited, and leftover typos. List
   the layout items you can't see (font, spacing, indents, header) for the
   learner to confirm. If the Doc hasn't changed since the last read, say so
   and check `modifiedTime` instead of reporting old errors as new.
9. **Verify pages in the browser pane** before handing them over: content
   renders, counters update, and reader highlights and links work.

## Course defaults

- **EN-221 (Chante Hope):** MLA 9. Story handouts are cited as
  `Course handout provided by Chante Hope, EN221, Monroe University, 2026.`
  Cite the printed page number, and say so when a handout has none. Present
  tense for literary analysis.
- **IT-100:** follow the prompt's file list exactly. Cite Parsons, not the
  lecturer, for slide content.
- Check the original's pagination and cite one copy consistently. If page
  numbers come from two copies, they can't be mixed.

## Files

- [references/page-contract.md](references/page-contract.md): the pages and
  their required parts
- [references/reader-spec.md](references/reader-spec.md): the reader's JSON
  spec
- [references/coaching-rules.md](references/coaching-rules.md): the edit and
  feedback protocol
- `scripts/build_reader.py`, `tests/test_build_reader.py`
