# Source and batch contract

## Batch state

Create section `state.json` before new processing (`scripts/new_section.py`
writes this shape):

```json
{
  "status": "collecting",
  "week": 1,
  "title": "Data Basics and Levels",
  "coverage": "partial",
  "batch": 1,
  "release_note": "More screenshots are coming",
  "missing": ["Remaining worked-example pages"],
  "verification": {"local": "pending", "http": "pending", "import": "pending"}
}
```

- `collecting`: user is still sending sources. Record receipts and source IDs.
  Do not replace existing study outputs or expand the live overall map.
- `partial`: user requested an interim draft. Build an offline preview only.
- `ready`: user released this batch for processing. Source coverage may still
  be partial. Record the release instruction; do not infer missing pages exist.
- `complete`: released batch processed, with local, HTTP, and actual import
  checks passed. Keep ready while any check is pending, including when no browser
  is available. Report pending checks without claiming successful import.

`validate_kit.py --kit` requires `state.json` on every processed section, with
a positive integer `"week"`, a nonempty `"title"` (the GoodNotes section folder
name), `"status"` from the four states below, and `"coverage"` of `partial` or
`full`. Do not infer week
from `Chapter-NN`. A
legacy folder without one fails that check until you add the file (status and
coverage as known; do not invent missing pages). The live hub builder runs
`--kit` and will not write while the contract fails.

A new batch increments `batch` and returns to collecting when more is coming.
Keep the previously published kit intact until the replacement is ready.
An ordinary complete-source request authorizes processing without an extra
confirmation. "Wait" requires an actual release, not a timeout. Old sections
without a state file are legacy/unverified; do not retroactively invent state.

## Source table in ledger.md

Use stable IDs such as `S001`; do not renumber old sources. Record:

| ID | Original location | Locator | Extraction | Coverage / availability |
| --- | --- | --- | --- | --- |
| S001 | Local original path | PDF pp. 1–3 | ocr-S001.txt | Read; page 3 formula checked |
| S002 | Original image path or attachment identifier | image 2 | Short transcript below | Read; bottom cropped |

For local files, record SHA-256 and byte size when available. This identifies
repeated batches or changed sources without copying binaries into the kit.
Do not store names, IDs, credentials, or private source paths in imported notes.
For temporary attachments, retain a short local text transcription plus locator
before the attachment disappears. If the original is gone, state unavailable;
never invent a recoverable link or claim visual verification occurred.

Each earned claim needs a source ID + locator + brief evidence. Source previews
and matching slide filenames are not proof of coverage. Distinguish source-taught
traps, official printed feedback, derived explanation, and newly created practice.
Existing untraceable claims remain legacy/unverified until supporting evidence
is recovered. Keep unavailable evidence visible instead of silently discarding it.

`SOURCES.md` is the course-level slide/original index. Use paths relative to that
file. From Chapter-Kits, its course's study library is `../01-Study-Library/`.
Run `validate_kit.py --sources` after updating it. Its Markdown-link check cannot
validate prose-only path mentions or access to remote links.

## Extraction routes

- **PDF:** run `ocr_pdf.swift` from the original path, then check all page markers
  against the PDF page count. It buffers output and exits nonzero if any page
  fails or contains no recognized text. A blank or diagram-only page therefore
  needs local visual review; record it separately rather than pretending OCR
  succeeded. Do not replace verified OCR with an error or a partial result.
- **PPTX:** run `extract_pptx.py` from the original path, writing its stdout to a
  pending text file and promoting only after success, as for PDF. It extracts
  slide text in presentation order, not image text, chart labels, or speaker
  notes. Inspect those visually (usage charts, OS-family figures, instruction
  cycles) before maps or notes; export to PDF locally for Vision OCR when needed.
  An image-only slide causes a clear error so it cannot silently disappear.
  A lecture-notes checklist in Week `Materials/` is a coverage spine, not a
  substitute for the slide body.
- **Legacy PPT:** the PDF and PPTX scripts cannot read this format. Open it in
  an available local presentation app and export to a temporary PDF outside
  Chapter-Kits, then OCR and record the conversion. If no local converter is
  available, report that specific limitation and request an exported PDF.
- **Screenshots:** read original images locally in order and record image IDs,
  short evidence transcripts, cropping, and unreadable regions. No PDF conversion
  or copying into Chapter-Kits is needed. A screenshot can earn a concept just
  as a textbook page can; evidence and section scope determine coverage.

Always visually check mathematical symbols, signs, units, table alignment, and
printed answers. Extraction success is not proof of correct mathematical reading.
Keep local source metadata out of generated claim URLs, including filenames that
contain personal information. HTTP checks transmit the encoded note/map content
to GoodNotes; offline previews do not contact the service.
