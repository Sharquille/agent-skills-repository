# Workspace and Brief Templates

Copy-adapt these. Keep ids stable once assigned: sources are `S1, S2, …`,
evidence rows are `E1, E2, …`, conflicts are `C1, C2, …`.

## question.md

```markdown
# Question
<the question, restated precisely; ambiguities resolved or flagged>

## Scope
- Time window / versions / jurisdiction: …
- Explicitly out of scope: …

## Sub-questions
### Q1: <sub-question>
- Would answer it: <what evidence settles this>
- Would falsify it: <what evidence overturns the expected answer>
### Q2: …

## Key terms
<term> — synonyms/aliases: …
```

## sources/register.md

```markdown
| id | title | url | accessed | published/rev | class | capture | independence notes |
|---|---|---|---|---|---|---|---|
| S1 | RFC 9110 | https://… | 2026-07-06 | 2022-06 | P | full | IETF original |
| S2 | Vendor advisory X | https://… | 2026-07-06 | 2026-05-14 | P | full | — |
| S3 | Coverage of S2 | https://… | 2026-07-06 | 2026-05-15 | S | partial: intro only, paywalled | derives from S2 — not independent |
```

Class: P primary · S secondary · T tertiary. Capture: `full`, or
`partial: <what is missing>` — quotes only come from captured text, and "no
evidence" inside a partial capture is a capture gap, not a finding. Saved
text lives at `sources/<id>-<slug>.md` with a header block:

```markdown
<!-- source: S1 | url: https://… | accessed: 2026-07-06 | license-note: … -->
```

## evidence.md (the ledger)

Block records, not a table: verbatim quotes contain pipes, newlines, and
markdown that break table cells and silently mutate the quote — which then
fails the stage-6 grep. The fenced block preserves the quote byte-for-byte.

````markdown
### E1 · Q1 · S1 §4.2 · status: unverified
claim: <the claim this quote supports>
note: <optional: ambiguity flag, weak-source reason>
quote:
```text
<verbatim quote, exactly as it appears in sources/S1-….md>
```
````

Status: `unverified` → `verified` (quote grepped verbatim in the saved
source) / `weak` (partial support, or weak/echo source — the note says which)
/ `rejected` (quote absent, misquoted, or does not support the claim).
The ledger holds quotes only. Conductor inferences are never ledger rows —
they appear in `synthesis.md` labeled `(inference from E…)`.

The extraction lane returns raw rows without ids or status; the conductor
assigns `E*` ids, sets `unverified`, and drops duplicates when appending.

## conflicts.md

```markdown
### C1: <one-line statement of the conflict>
- Entries: E3 (S1, P) vs E7 (S4, S)
- Type: contradiction | definition mismatch | version/date divergence | gap
- Ruling: <which stands> — <one line: primacy/independence/recency/authority>
- Status: resolved | open (must surface in synthesis)
```

## synthesis.md

```markdown
# Answer: <question>

## Q1: <sub-question>
<answer> [E1, E4] (confidence: high)
<inference, labeled> (inference from E2+E5; no direct source)

## Overall
<the synthesized answer>

## Open conflicts and gaps
- C2 remains open: …
- No primary source found for …: …
```

## audit.md

```markdown
| check | result |
|---|---|
| all cited ids exist | pass |
| all quotes verbatim in saved sources (grep, 100%) | pass — E9 fixed (typo in quote) |
| locators correct | pass |
| URL spot-check resolves | pass |
| no citation laundering (S cited where P on disk) | pass — E12 re-pointed S3→S2 |
| every load-bearing claim cited or labeled inference | pass |
Verdict: deliverable | blocked on <…>
```

---

# Lane Brief Templates

## Extraction brief (Codex consult / `--lane context`)

```text
You are extracting evidence from saved source files in this directory
(sources/*.md). Sub-questions:
Q1: <…>   Q2: <…>

For each sub-question, return ledger rows in exactly this format:
| sub-q | claim | exact quote | source id | locator |

Rules: quotes must be VERBATIM from the files — no paraphrase, no
normalization, no added words. Locator = section/heading/anchor as present in
the file. Take source ids from the file header comments. If a passage is
ambiguous or only partially supports a claim, flag it as AMBIGUOUS with one
line of reasoning. If a sub-question has no supporting material, say NO
EVIDENCE for that sub-question — do not stretch. Do not draw conclusions;
extraction only.
```

## Conflict brief (`--lane reasoning`, sealed, ledger inline)

```text
Below is an evidence ledger (id | sub-q | claim | quote | source | locator).
Sources classed P/S/T in the register excerpt that follows it.

Identify, citing ledger ids only:
1. Direct contradictions between entries.
2. Definitional mismatches (same term, different meanings across sources).
3. Version/date divergence (claims true for different versions or times).
4. Sub-questions whose evidence is one-sided, thin, or missing.

For each finding: the ids involved, the type, and one line on why it
qualifies. Do NOT adjudicate — do not say which source wins. Finding
conflicts is your job; ruling on them is not.

<ledger>
<register excerpt>
```

## Audit cross-check brief (`--lane code`, sealed, pairs inline)

```text
Below are claim/quote pairs from a research synthesis. For each pair answer:
SUPPORTED (quote clearly supports the claim), PARTIAL (supports part; state
which part is unsupported), or UNSUPPORTED (quote does not establish the
claim). One line of reasoning each. Judge only what the quote states —
no outside knowledge, no charity.

<claim/quote pairs with ids>
```

## Prose pass brief (`--lane prose`, sealed, synthesis inline)

```text
Improve readability of the text below WITHOUT changing meaning: no claim
added, removed, weakened, or strengthened; citations ([En]) and confidence
labels stay exactly where they are. Return the revised text plus a list of
each change made. Flag any sentence you could not improve without changing
meaning.

<synthesis>
```
