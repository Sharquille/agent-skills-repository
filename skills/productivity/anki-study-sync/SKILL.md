---
name: anki-study-sync
description: "Generate a deterministic, question-first Anki text-import file from completed Obsidian study notes. Use when obsidian-study-loop has made a chapter content-ready and the learner wants high-volume recall practice in Anki. Preserve stable card identities across revisions, cite every card back to a vault-relative note heading, and treat Anki activity as practice rather than competency evidence. Do not use for grading mastery, changing study-loop status, reading Anki review history, deleting cards, or exporting cards from unverified learner mistakes."
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
by stable ID, verifies every exact note heading, escapes multiline content as
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

- Cover each objective broadly enough for recall practice: normally a core
  concept card, a condition or contrast card, and an example cue when the note
  supports them. Add more only for genuinely distinct retrieval targets; never
  pad a chapter to a fixed quota.
- One retrieval target per card.
- Prefer production over recognition. Use `typed` only as metadata for a prompt
  whose answer is an exact short response; the portable TSV still renders it as
  a normal `Basic` card.
- Put the answer in the learner's words only when those words were verified;
  otherwise use the canonical note wording.
- Keep source context in the answer when it prevents a misleading absolute.
- Do not add trivia merely to increase card count.
- Visual and image-occlusion cards are a later media workflow. This text
  generator must not invent a media path or copy files into Anki media.

## Completion report

Return the manifest path, TSV path, active/retired counts, note type, deck, and
the one manual import action. Report generation failures to the study session
as `Anki deferred — <reason>`; they do not block note publication or erase
competency evidence.

## References

- Anki Manual, [Text Files](https://docs.ankiweb.net/importing/text-files.html)
- Anki Manual, [Exporting](https://docs.ankiweb.net/exporting.html)
- Anki Manual, [Deck Options](https://docs.ankiweb.net/deck-options.html)
- Anki Manual, [Field Replacements](https://docs.ankiweb.net/templates/fields.html)
