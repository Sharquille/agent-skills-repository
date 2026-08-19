---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
# --- provenance ---
category: productivity
source: https://github.com/mattpocock/skills/tree/main/skills/productivity/handoff
author: Matt Pocock (mattpocock/skills)
license: MIT
retrieved: 2026-08-19
modified-by: Sharquille Andrew (save location bound to this machine's scratchpad convention; cross-agent handoff and study/project session state added)
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save it to the session scratchpad directory when one is set, otherwise the OS temporary directory — never the current workspace.

Include a "suggested skills" section in the document, naming which skills the next agent should call the Skill tool for.

Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.

## Local use

Name the receiving agent when it is not Claude. Codex, Gemini, and OpenCode read different global instruction files and reach skills by different paths, so state which wrappers or skills the next session should use rather than assuming a shared setup.

When a `obsidian-study-loop` or `project-build-loop` session is active, that workflow's own on-disk state is the source of truth for progress. Point at those files and record only what is not already written there: live hypotheses, rejected approaches and why, and the next decision waiting on the user.

Record what was verified versus assumed, per `anti-slop-standard`. An unmarked assumption inherited by a fresh session is the most expensive thing a handoff can carry.
