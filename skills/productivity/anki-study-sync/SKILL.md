---
name: anki-study-sync
description: "Generate a deterministic, question-first Anki text-import file from completed Obsidian study notes. Use when obsidian-study-loop has made a chapter content-ready and the learner wants high-volume recall practice in Anki. Preserve stable card identities across revisions, cite every card back to a vault-relative note heading, reject mixed-review deictic or duplicate-answer active cards, and treat Anki activity as practice rather than competency evidence. Do not use for grading mastery, changing study-loop status, reading Anki review history, deleting cards, or exporting cards from unverified learner mistakes."
# --- provenance ---
category: productivity
source: self-authored companion to obsidian-study-loop
author: Sharquille Andrew
license: MIT
retrieved: 2026-08-27
---

# Anki Study Sync

Turn a content-ready chapter manifest into a repeatable Anki import. This is a file
handoff, not a live Anki integration: generate the UTF-8 TSV, show the learner
where it is, and let Anki perform the import. Never install an add-on, open a
local API, or mutate an Anki collection without a separate explicit request.

## Boundary

- Obsidian notes are the source of truth for explanations and cited context.
- This skill owns recall-card generation plus stable updates.
- `obsidian-study-loop` owns applied questions, assistance provenance, scoring,
  competency, and chapter completion.
- Anki ratings, intervals, lapses, and leech status never become mastery
  evidence and never change a chapter state.
- Create cards only from content-ready notes. Do not make permanent cards from
  a learner's incorrect answer or from an unresolved claim.

## Inputs

The caller creates `_study/anki/<chapter-slug>.json`:

```json
{
  "schema": "anki-study-sync.manifest",
  "version": 1,
  "chapter_id": "security-plus-chapter-3",
  "deck": "Security+::Chapter 3",
  "notetype": "Basic",
  "objectives": [
    "3.1 Compare control types"
  ],
  "cards": [
    {
      "id": "security-plus.ch3.control-types.basic",
      "objective": "3.1 Compare control types",
      "type": "basic",
      "prompt": "What distinguishes a preventive control?",
      "answer": "It acts before an event to reduce its likelihood.",
      "source": "Notes/Security+ Ch3.md#Control types",
      "revision": 1,
      "status": "active",
      "tags": ["security-plus", "chapter-3", "objective-3-1"]
    }
  ]
}
```

Required manifest and card fields are exactly the fields shown. `type` is
`basic` or `typed`; the portable TSV renders both through Anki's built-in
`Basic` note type and preserves the distinction as a tag. `status` is `active`
or `retired`. Every card objective must appear in the manifest's unique
`objectives` list, and every listed objective must have at least one active
card. Every source is a vault-relative Markdown path plus an exact heading
anchor. Verify that the note and heading exist before writing the manifest.

## Stable identity

- Derive `id` from course, chapter, objective, retrieval target, and card type.
- A wording or formatting improvement keeps the same ID and increments
  `revision`; the GUID column is intended to let Anki match and update the
  existing note instead of creating a duplicate. Scheduling remains Anki-owned.
  Confirm the target Anki version's import preview reports updates before
  relying on schedule-preserving replacement.
- A semantic change to what the learner must retrieve gets a new ID. Retain the
  old manifest row as `retired` so the export tags it `study-loop::retired`;
  tell the learner to suspend that tag after import. If its original heading is
  removed, archive that source under `_study/workpages/` and point the retired
  row to the archive. Never delete it silently or leave a broken source.
- IDs must remain unique across the chapter manifest.

The first regular TSV field is always the learner-facing question. The stable
external ID is a separate special GUID import column, so Anki can update the
same note without exposing an internal identifier on the card front. Do not use
Anki's numeric note or card IDs as application identifiers.

## Generate

Run:

```text
scripts/build_anki_import.py <manifest.json> --vault <VAULT_PATH> --output <chapter.tsv>
```

Without `--output`, the TSV is written to standard output. The generator sorts
by stable ID, verifies every exact note heading, rejects deictic or
duplicate-answer active prompts, escapes multiline content as
HTML, rejects unsafe sources and duplicate IDs, and replaces a vault-local
output file atomically.

The generated TSV uses Anki's built-in `Basic` note type. Its four columns are
`Front`, `Back`, `GUID`, and `Tags`. File headers mark `GUID` and `Tags` as
special columns, so only `Front` and `Back` map to note fields. The GUID value
is the manifest's application-owned stable card ID. The front is the question.
The back contains the answer plus a small objective and source footer. No
custom note type or card template is required.

Import the generated file with updating enabled. Retired notes remain
recoverable and should be suspended, not deleted.
This `Basic` handoff does not migrate notes previously imported through the
custom `Study Loop` note type. During a transition, use a distinct deck and
verify the import preview instead of mixing the two formats.
If the learner wants randomized new-card practice, point them to Anki's Deck
Options and let them choose a random gather or sort order. This file handoff
does not change deck options.

## Card quality

Active cards must survive mixed review: shuffled into unrelated cards from the
same course, a competent learner still knows what to retrieve.

### Short, visual, speakable cards

Reuse the learner's stated preferences and the caller's session context. When
the learner prefers visual cues, whisper-reading, or shorter attention windows,
apply the pattern below. Treat these as adjustable preferences, not a diagnosis
or fixed learning-style label. Do not add a learner-profile file or manifest
fields. The caller may record an adopted preference in its existing
`## Session log`, as the study loop specifies.

- Front: one direct question, with at most one small cue when useful. Aim for
  a question the learner can whisper in one short sentence. Preserve technical
  terms and any conditions needed to make the answer unambiguous.
- Back: put the answer first in one short sentence, then at most two short
  lines for a necessary explanation or visual relationship. These are authoring
  targets, not word-count validation rules. Leave fuller teaching in the cited
  note; split a card when it asks for several independent answers.
- Use plain-text arrows, labeled stages, or two labeled contrast lines when
  they clarify the retrieval target. Every symbol needs a meaning the learner
  can say aloud. Avoid decorative icons, wide tables, and diagrams that depend
  on spaces lining up. Use real newlines in field values (`\n` in JSON); the
  exporter renders them as line breaks. Markdown, Mermaid, and supplied HTML
  are not rendered as rich card content by this exporter.
- A front-side cue may show a situation or an incomplete relationship, but
  must withhold the answer. Put the completed relationship on the back. Do not
  turn recall into copying a visible answer or recognizing a distinctive layout.
- When the concept needs an actual image, keep that instruction in the source
  note or the study loop's visual helper. Use a self-contained text card only
  if it still tests the intended target; report an unsupported image-dependent
  target to the caller instead of pretending a text substitute covers it.

For example, when the cited note supports the relationship:

```json
{
  "prompt": "When does a preventive control act relative to an unwanted event?",
  "answer": "Before the event, to reduce its likelihood.\nPreventive action → possible event\nRead left to right as time order."
}
```

This fragment supplies only the two visible fields; the full manifest still
requires the existing identity, objective, source, revision, status, and tags.
Keep the same ID when adding this presentation to an unchanged retrieval
target and increment its revision. Do not add alternate visual/oral copies of
the same card.

### Retrieval and coverage

- Cover each objective broadly enough for recall practice: normally a core
  concept card, a condition or contrast card, and an example cue when the note
  supports them. Add more only for genuinely distinct retrieval targets; never
  pad a chapter to a fixed quota.
- One retrieval target per card.
- Name that target on the front. Do not use "this section", "this chapter",
  "this course", "listed in", or a numbered lab/exercise as the cue.
- The answer must be supported by the cited note heading. If the heading and
  the answer disagree, change the card or the note before import.
- Prefer production over recognition. Use `typed` only as metadata for a prompt
  whose answer is an exact short response; the portable TSV still renders it as
  a normal `Basic` card.
- Put the answer in the learner's words only when those words were verified;
  otherwise use the canonical note wording.
- Keep source context in the answer when it prevents a misleading absolute.
- Do not add trivia merely to increase card count.
- Two active cards may not share the same prompt or the same answer. A wording
  fix keeps the id and increments `revision`. A new retrieval target gets a
  new id; retire the old row.
- Image and image-occlusion cards require a separate media workflow. This text
  generator must not invent a media path or copy files into Anki media.

Before generation, read each active front without its back or neighboring
cards: is the target clear, is its answer hidden, and can the expected response
be brief? Then check the answer against the cited heading. The scripts check
structure, heading existence, and mixed-review defects; they do not verify
factual support, visual usefulness, answer leakage, or attention load.

`scripts/build_anki_import.py` rejects deictic and duplicate-answer active
cards. After publication, also run:

```text
scripts/lint_anki_quality.py --vault <VAULT_PATH>
```

That read-only sweep covers every manifest under `_study/anki/`. Fix findings
before recording `## Anki handoff` as ready.

## Practice handoff

When whisper-reading is preferred, give this routine once in the handoff,
not on every card: whisper the question, look away and answer or sketch from
memory, then reveal and compare. Whisper the correction if needed; reading the
revealed answer is feedback, not a successful recall attempt. Never claim to
hear or grade speech in text-only mode.

Offer a short practice window, such as 5-10 minutes, with one card at a time;
this is an adjustable starting point, not a required dose or completion quota.
After attention drifts, return to the current question and its named target,
or pause. Do not restart the chapter or reread the whole source by default.
Repeated confusion calls for the exact source heading and, if needed, the
study loop's teaching or applied-check path. Keep scheduling and ratings
Anki-owned; add no second review schedule, assessment kind, or mastery ledger.

The caller owns `## Anki handoff` and lifecycle updates. Missing or failed Anki
generation is deferred; `not-required` means the learner explicitly declined.
Preserve the study loop's diagnostic-first order: never require Anki practice
before its initial diagnostic or expose card answers during an active check.

## Completion report

Return the manifest path, TSV path, active/retired counts, note type, deck, and
the one manual import action. Report generation failures to the study session
as `Anki deferred — <reason>`; they do not block note publication or erase
competency evidence.
Include the brief practice routine when relevant and any image-dependent
coverage still deferred. Do not claim that a generated TSV was imported or
that this presentation has improved retention without learner evidence.

## References

- Anki Manual, [Text Files](https://docs.ankiweb.net/importing/text-files.html)
- Anki Manual, [Exporting](https://docs.ankiweb.net/exporting.html)
- Anki Manual, [Deck Options](https://docs.ankiweb.net/deck-options.html)
- Anki Manual, [Field Replacements](https://docs.ankiweb.net/templates/fields.html)
