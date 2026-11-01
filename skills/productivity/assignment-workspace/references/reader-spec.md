# Reader spec

`build_reader.py SPEC.json OUT.html` takes this shape:

```json
{
  "title": "Week 8 Reader",
  "sources": [
    {
      "key": "A",
      "label": "Angelou · “Liked for Myself”",
      "short": "Angelou",
      "cite_author": "Angelou",
      "source_line": "Maya Angelou, “Liked for Myself.” Textbook pp. 148–151 (cite the printed page).",
      "pdf": "../Materials/reading/Liked_for_Myself%20rev_removed.pdf",
      "blocks": [
        {"id": "a1", "label": "¶1", "page": 148, "pdf_page": 1, "text": "For nearly a year, …"}
      ]
    }
  ],
  "questions": {
    "a-a2": {
      "source": "A",
      "title": "After 2 · What she teaches about communication",
      "tip": "The walk, ¶9–14. …",
      "blocks": ["a9", "a11", "a12"],
      "phrases": ["language is man's way of communicating with his fellow man"]
    }
  }
}
```

## Rules

- **`page`** is the page to cite: the printed page when there is one,
  otherwise the handout page. A paragraph that crosses pages may use
  `"150–151"`; its citation tag takes the first page. **`pdf_page`** is the
  page in the PDF file, used for the "PDF p." links.
- **Block ids** are unique across sources. Labels follow the text's own
  numbering (`¶7`) or list numbering (`12.`).
- **Question ids** match the workspace section ids, so
  `Reader.html#<id>` opens the right question.
- **`phrases`** must appear verbatim in one of that question's `blocks`. The
  build fails otherwise. Use the transcribed text's exact punctuation,
  including curly quotes.
- **Highlights mark where to look, not the answer.** Pick phrases a strong
  answer would quote, and keep the tip to where and what, not the
  interpretation.
- `pdf` paths are relative to the output file and URL-encoded (`%20`).

## Getting the text

Prefer the kit OCR (`Chapter-Kits/.../ocr-S00N.txt`), with page markers and
the ledger's notes on dropped words. Otherwise, use the PDF text layer
through PDFKit, or Vision OCR for scans. Rebuild paragraphs from the line
breaks, restore printed paragraph numbers that OCR turned into letters
(`i`, `s`, `?`, `&`, `»`), drop pull quotes, running heads, and footers,
and fix plain typos with a note to the learner.
