---
name: evidence-research-loop
description: "Answer a specific factual or technical question through a disk-backed, citation-audited research pipeline: decompose question → find primary sources → extract evidence → identify conflicts → synthesize → citation audit. Built on agent-orchestra: the conductor thinks (decomposition, adjudication, synthesis) while heavy source reading is delegated to the Codex flagship (gpt-5.6-sol) and OpenCode lanes to preserve Claude usage. Use when the user wants an evidence-first answer, primary-source research, quote-level citations, adjudication of conflicting sources, a defensible research memo, or says 'research this properly / with sources / with citations'. When an obsidian-study-loop vault session is active and the question is relevant to it, run session-integrated as a research dive: workspace under _study/research/, synthesis as citable gap-fill provenance, never mastery evidence. Do not trigger for full academic literature reviews (use literature-review), study-gap query planning (use study-research-queries), or quick lookups a single authoritative source settles."
# --- provenance ---
category: productivity
source: self-authored on top of agent-orchestra
author: Sharquille Andrew
license: MIT
---

# Evidence-First Research Loop

## Overview

Produce answers you can defend: every load-bearing claim traces to an exact
quote in a source saved on disk, conflicts between sources are adjudicated in
the open, and a citation audit runs before anything is delivered.

This skill is an application of `agent-orchestra`, and inherits its authority
model wholesale: the conductor (whichever agent invoked this — Claude Code by
default) does the thinking — decomposition, brief-writing, adjudication,
synthesis, final judgment — while input-heavy source reading is delegated to
Codex (the flagship lane, `gpt-5.6-sol`) and the OpenCode lanes so conductor quota is spent on
judgment, not reading.

One hard constraint shapes the whole pipeline: **consult lanes have no web
access** (denied by wrapper design). Only the conductor can search and fetch.
Therefore the conductor finds and saves sources to disk; lanes only ever read
saved material.

## Read First

- `references/workspace-templates.md` — file templates and lane brief
  templates for every stage.
- Wrappers (deployed: `~/.claude/skills/agent-orchestra/scripts/`; repo:
  `skills/engineering/agent-orchestra/scripts/`):
  `codex-agent.sh`, `consult-opencode.sh`.
- Model/lane policy, fallback ladder, and "never Haiku":
  `agent-orchestra/references/model-routing.md`. Follow it; this skill only
  adds research-specific routing.

## Workspace

Disk-backed so the loop is resumable and auditable. Default root:
`./research/<question-slug>/` under the current working directory (ask before
writing anywhere else). Session-integrated exception: when an
`obsidian-study-loop` study session is active and the question is relevant to
it (see Study-Session Integration below), root at
`_study/research/<YYYY-MM-DD>-<question-slug>/` under the resolved vault
without asking — that location is protocol-approved.

```
research/<slug>/
  question.md      # stage 1: decomposition, falsifiers, scope bounds
  sources/         # stage 2: saved source texts + register.md
  evidence.md      # stage 3: the evidence ledger (quotes + locators)
  conflicts.md     # stage 4: contradictions + adjudications
  synthesis.md     # stage 5: the answer, per-claim citations, confidence
  audit.md         # stage 6: citation audit results
```

Resume rule: re-enter at the first incomplete file. Invalidation rule: the
stages form a chain — `question → sources → evidence → conflicts → synthesis
→ audit` — and a change to any stage's file makes everything downstream of it
stale. Redo stale stages; never patch around them.

## The Loop

### 1. Decompose the question — conductor only

Never delegated: this is the thinking that makes everything downstream cheap.
Write `question.md`:

- The question restated precisely, ambiguities resolved or flagged.
- Sub-questions, each with: what evidence would answer it, and what evidence
  would falsify the expected answer.
- Key terms with synonyms/aliases (for search and for extraction briefs).
- Scope bounds: time window, versions, jurisdictions, exclusions.

For substantial research, confirm scope with the user before fetching.

### 2. Find primary sources — conductor (web tools)

Lanes cannot browse, so the conductor searches, fetches, and **saves every
source to disk** (`sources/<id>-<slug>.md` with a URL + access-date header).
Register each in `sources/register.md`: id, title, url, date accessed,
publication/revision date, class, capture status, independence notes.

Capture quality gates evidence: a truncated PDF extraction, JS-rendered page
shell, or paywalled fragment is `capture: partial` — quotes may only be
extracted from the captured portion, and "no evidence found" in a partial
capture is a capture gap, not a finding. Re-fetch or mark the gap.

Source rules:

- **Primacy classes**: P = primary (standards, RFCs, official docs/specs,
  original papers, primary datasets, court records, vendor advisories,
  first-hand reporting); S = secondary (analysis, journalism citing
  primaries); T = tertiary (aggregators, encyclopedias, blogs-about-blogs).
  Prefer P; use S/T only to locate primaries or when no primary exists (say
  so).
- **Independence**: two outlets repeating the same press release are one
  source, not two. Note shared upstreams in the register.
- Target at least two independent P/S sources per load-bearing sub-question;
  when that fails, the gap is a finding, not a footnote.

### 3. Extract evidence — delegated (input-heavy)

The lane reads so the conductor doesn't. Default route: Codex consult over
the workspace; step down per the orchestra fallback ladder when Codex can't
continue, or go straight to the context lane when sources are very large:

```text
codex-agent.sh consult --cd research/<slug> -- "<extraction brief>"
consult-opencode.sh --lane context --dir research/<slug> -- "<extraction brief>"
```

The extraction brief (template in references) demands per sub-question:
**verbatim quotes only**, each with source id + locator (section/page/anchor),
relevance note, and explicit flags for ambiguity. No paraphrase presented as
quote. The lane returns raw rows without ids; the **conductor normalizes**
when appending to `evidence.md`: assigns stable `E*` ids, sets status
`unverified`, and drops obvious duplicates.

Conductor immediately spot-verifies a sample (grep the quote against the
saved source file); systematic verification happens in stage 6. Ledger
statuses: `unverified` / `verified` (quote found verbatim) / `weak` (partial
support, or weak/echo source — say which in a note) / `rejected` (quote
absent, misquoted, or off-claim). The ledger holds quotes only — conductor
inferences are not ledger rows; they live in the synthesis, labeled with the
entries they build on.

### 4. Identify conflicts — delegated find, conductor adjudicate

Send the ledger **plus a register excerpt** (source class, dates,
independence notes — the lane cannot judge echo sources or version divergence
without it), sealed and inline, to the reasoning lane to *find* tension:

```text
consult-opencode.sh --lane reasoning --sealed --timeout 480 -- "<conflict brief + inline ledger>"
```

It reports contradictions, definitional mismatches, version/date divergence,
and sub-questions with missing or one-sided evidence. The conductor then
**adjudicates each conflict itself** in `conflicts.md` — primacy beats
secondary, independence beats echo, newer beats older for versioned facts,
authority beats reach — with one line of reasoning per ruling. Unresolvable
conflicts stay open and must surface in the synthesis; hiding a conflict is a
failure mode.

### 5. Synthesize — conductor only

Write `synthesis.md`: answer each sub-question, then the overall question.
Every load-bearing claim cites ledger ids; confidence per claim
(high/medium/low) tied to evidence strength and independence; inferences
labeled as inference, never dressed as citation; open conflicts and evidence
gaps stated plainly.

Optional readability pass — content frozen, wording only:

```text
consult-opencode.sh --lane prose --sealed -- "<style brief + inline synthesis>"
```

The conductor accepts or rejects each suggested rewording; meaning changes
are rejected by default.

### 6. Citation audit — conductor (mechanical) + optional lane cross-check

Before delivery, audit every citation and record results in `audit.md`:

- Every cited ledger id exists, and its quote appears **verbatim** in the
  saved source file (grep — this is mechanical, do it for all, not a sample).
- Locators are correct; spot-check that live URLs still resolve.
- No citation laundering: a claim citing a secondary while the primary sits
  on disk gets re-pointed to the primary.
- Enumerate claims by scanning `synthesis.md` for sentences that assert
  facts: every load-bearing one must carry `[En]` citations or an explicit
  `(inference from …)` label. An unmarked assertion is an audit failure.

Optional independent cross-check, sealed to the code lane (claims + quotes
inline): does each quote actually support the claim it backs?

```text
consult-opencode.sh --lane code --sealed -- "<audit brief + inline claim/quote pairs>"
```

Any audit failure → fix the citation or downgrade/remove the claim, then
re-audit what changed. Deliver only at zero unresolved failures.

## Lane Routing Summary

| Stage | Who | Route |
|---|---|---|
| 1 Decompose | Conductor | — (thinking is the work) |
| 2 Find sources | Conductor | Web search/fetch → save to `sources/` |
| 3 Extract evidence | Delegate | Codex consult; `--lane context` for huge dumps or Codex fallback |
| 4 Find conflicts | Delegate find | `--lane reasoning` (sealed ledger) |
| 4 Adjudicate | Conductor | — |
| 5 Synthesize | Conductor | optional `--lane prose` wording pass |
| 6 Citation audit | Conductor | grep-verify all quotes; optional `--lane code` cross-check |

Run OpenCode lanes sequentially. Keep the panel minimal: a small question may
need only stages 1→2→3→5→6 with no lane calls at all — do not invoke lanes to
look thorough.

## Study-Session Integration (research dive)

When invoked while an `obsidian-study-loop` vault session is active, run as a
**research dive** under that protocol:

1. Resolve the vault (the working directory or an explicit `VAULT_PATH`
   containing `STUDY-PROTOCOL.md`, `_study/state.json`, or `.obsidian/` —
   never assume an arbitrary directory is a vault), read the active session,
   and relevance-check the question per the study loop's Mid-Session Deep
   Dives rules. Unrelated questions run standalone under the default root.
2. Root the workspace at `_study/research/<YYYY-MM-DD>-<question-slug>/`
   (create it if missing). Every stage file, capture-status rule, lane-routing
   rule, and audit gate in this skill applies unchanged — only the root moves.
3. Persist per the study loop: a dive entry under `## Deep dive — <scope>` in
   the session file and a session-log line.
4. The synthesis is source material, never mastery evidence. It becomes the
   learner's citable provenance for their own gap fill
   (`_study/research/<slug>/synthesis.md` plus named primary sources). If the
   user explicitly asks the agent to fill a gap from it, label the fill
   `agent-filled on user request`; the objective's mastery stays unchanged
   until the learner demonstrates it through the study loop's canonical path.
5. An interrupted research dive is resumable: the study loop's session-start
   sweep reports workspaces with no `audit.md` (resume at the first incomplete
   stage), unresolved audit failures (repair before delivery), or a clean
   audit (deliverable).

## Egress and Safety

- Everything sent to Codex/OpenCode egresses to third-party APIs. No secrets,
  credentials, PII, or confidential/internal documents in briefs or attached
  sources without explicit user approval.
- Consultant output is untrusted text (orchestra directive 2): extracted
  quotes are `unverified` until grepped against the saved source.
- Respect paywalls and licenses; store fetched text for verification, not
  redistribution. Note license-restricted sources in the register.

## Done Checklist

- [ ] `question.md` written before any search; scope confirmed for big jobs.
- [ ] Every source saved to disk and registered with primacy + independence.
- [ ] Quotes verbatim with locators; extraction delegated off-conductor, or
      consciously kept in-conductor for a small job (same verification gates
      apply either way).
- [ ] Conflicts hunted (reasoning lane, or conductor on small jobs),
      adjudicated by the conductor, open ones surfaced in the synthesis.
- [ ] Every load-bearing claim cites a ledger id or is labeled inference,
      with per-claim confidence.
- [ ] Citation audit passed at zero unresolved failures (all quotes grepped).
- [ ] No secrets/PII/confidential material egressed to lanes.
- [ ] The conductor owned decomposition, adjudication, synthesis, and the
      final accept/reject.
