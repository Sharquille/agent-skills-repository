---
name: study-research-queries
description: "Generate focused research plans, search queries, and source-triage checklists for study gaps, certification objectives, course lessons, and Obsidian study notes. Use when the user needs help researching a missed objective, validating course content, finding authoritative references, preparing queries for CompTIA/Security+/IT topics, or deciding which sources to trust before filling notes. Do not trigger for full literature reviews, generic web browsing, or writing the user's gap note unless explicitly asked."
# --- provenance ---
category: productivity
source: self-authored as a companion to obsidian-study-loop
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-15
---

# Study Research Queries

Generate source-aware research plans for learning gaps. The output should help
the user research and fill their own notes, especially after an
`obsidian-study-loop` quiz marks an objective as `gap` or `partial`.

This skill does not call LLM APIs, does not add API keys, and does not browse by
default. If the user explicitly asks to search the web or needs current facts,
use available browsing tools and cite sources.

## Workflow

1. Identify the study target:
   - Course or certification, such as `CompTIA Security+ SY0-701`.
   - Domain, chapter, section, or objective number.
   - The exact gap, shaky detail, key term, or scenario the user needs to verify.
2. Prefer local context first:
   - Read the active study session when available.
   - Search the Obsidian vault for existing notes, key terms, and related MOCs.
   - Use the user's supplied course packet before external sources.
3. Split the target into research questions:
   - Definition: what the term means.
   - Distinction: what it is often confused with.
   - Exam angle: how the objective is tested.
   - Scenario: how it appears in a practical environment.
   - Edge case: common misconception or exception.
4. Generate queries that favor authoritative sources:
   - Official exam objectives and course materials.
   - Standards bodies and government guidance, such as NIST, CISA, OWASP, or
     vendor documentation when relevant.
   - Reputable technical references or textbooks.
   - Avoid generic SEO articles unless better sources are not available.
5. Provide a capture checklist for the user's note.

## Output Format

```markdown
## Research plan - <objective or gap>

### What to verify

- <specific fact or relationship>
- <specific distinction>

### Search queries

- "<course/cert> <objective number> <topic> official"
- "<topic> definition NIST OR CISA OR OWASP"
- "<topic A> vs <topic B> security control example"
- "<topic> CompTIA Security+ SY0-701 practice scenario"

### Preferred sources

- Course material already supplied by the user.
- Official exam objectives or vendor documentation.
- Standards or guidance from NIST, CISA, OWASP, cloud vendors, or product docs.
- Reputable textbooks or technical references.

### Source triage

- Prefer sources that define terms directly and give concrete examples.
- Cross-check any claim that appears in only one unofficial article.
- Reject sources that are promotional, vague, unsourced, or not tied to the
  objective.

### Capture checklist

- Definition in your own words.
- One compare/contrast point.
- One applied example or scenario.
- Key terms to add as `[[wikilinks]]` if matching notes exist.
- Any uncertainty to mark with `> [!warning]`.
```

## Query Patterns

Use multiple query types rather than one broad search:

- Exact objective: `"<certification>" "<objective number>" "<topic>"`
- Authoritative definition: `"<topic>" definition site:nist.gov OR site:cisa.gov`
- Standard or framework: `"<topic>" "NIST SP" security`
- Compare contrast: `"<term A>" vs "<term B>" cybersecurity`
- Scenario: `"<topic>" example scenario security control`
- Lab support: `"<topic>" simulator lab steps documentation`
- Misconceptions: `"<topic>" common mistakes Security+`

When a query uses a site filter, tailor it to the topic. For example, use OWASP
for application security, NIST/CISA for security concepts and risk, vendor docs
for product-specific configuration, and official course or certification pages
for exam mapping.

## Boundaries

- Do not invent citations, source names, or exam facts.
- Do not fill a gap note unless the user explicitly asks for help writing it.
- Do not overfit to one unofficial source.
- If sources conflict, flag the conflict and suggest what to verify next.
- Keep the output short enough that the user can act on it during a study block.
