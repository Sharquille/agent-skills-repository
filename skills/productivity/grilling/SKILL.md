---
name: grilling
description: "Interview the user relentlessly about a plan, decision, or design until every branch of the design tree is settled — questions asked in rounds along a moving frontier, each with a recommended answer, facts looked up rather than asked. Use when the user wants their thinking stress-tested, says 'grill me' or 'poke holes in this', or when a workflow needs a rigorous scoping interview before committing to work. Do not trigger when the user wants the answer rather than the interrogation, or for a quick clarifying question that a single AskUserQuestion settles."
# --- provenance ---
category: productivity
source: https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling
author: Matt Pocock (mattpocock/skills)
license: MIT
retrieved: 2026-08-19
modified-by: Sharquille Andrew (description expanded to this repo's trigger/anti-trigger convention; local callers noted)
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Each question should be formatted like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.

## Local use

This is the reusable interview primitive. Reach for it from any workflow that needs scoping before work starts, rather than writing a fresh interview loop:

- `project-build-loop` — the discovery interview before a roadmap is generated.
- `obsidian-study-loop` — scoping objectives and section content at session start.
- `teach-complex-concepts` — diagnosing what the learner already holds.

Those skills currently carry their own interview logic; when editing one of them, prefer moving it onto this frontier model over deepening the local copy.
