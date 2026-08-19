---
name: unslop
description: "Always-on, preservation-first prose standard for docs, notes, commit messages, PR bodies, reports, and chat answers. Removes unnecessary AI-style filler and vague wording when authoring while preserving meaning, technical terminology, required wording, and established voice. Use humanizer for an explicit deep rewrite, technical-writing for document structure, and portable-markdown for Markdown portability."
# --- provenance ---
category: productivity
source: https://github.com/cursor/plugins/blob/main/pstack/skills/unslop/SKILL.md
author: Lauren Tan (cursor/plugins, pstack)
license: MIT
retrieved: 2026-08-19
modified-by: "Sharquille Andrew — rule 13 softened from a total em-dash ban to a density guideline, because this repo's own skills use ~290 em dashes as house style and a spurious always-on rule teaches the reader to discount the other 30. Description expanded to this repo's trigger/anti-trigger convention."
---

# Unslop

Write and edit prose with a human voice while preserving meaning and context.

## Preservation gate

Apply this skill as a light authoring pass by default. Improve clarity only when the
change preserves the claim, scope, technical context, and intended register.

Keep exact:

- code, commands, flags, paths, identifiers, API names, protocol terms, and schema names;
- security, legal, compliance, and policy wording when precision requires it;
- exact quotations, required headings, metadata, and repository terminology;
- established domain terms when they name a real mechanism.

Do not rewrite a sentence only because it contains a listed pattern or word. Check the
surrounding meaning first. A listed word is a problem only when it is vague, inflated,
repetitive, or misleading in context.

Technical, reference, legal, security, and agent-instruction prose stays neutral. Do
not add opinions, first person, deliberate informality, or "mess" unless the document's
mode calls for it.

## Process

1. Scan for the patterns below.
2. Rewrite. Preserve meaning, match intended tone.
3. Apply narrative voice when the document calls for it.
4. Self-audit: "What makes this obviously AI generated?" Fix remaining tells.

## Narrative voice when the document calls for it

Use this section for essays, commentary, personal writing, and other narrative prose.
Skip it for technical, reference, legal, security, compliance, and agent-control
documents.

Removing patterns is half the job. Sterile, voiceless writing is just as obvious.

- **Have opinions.** React to facts instead of neutrally listing pros and cons.
- **Vary rhythm.** Short sentences. Then longer ones that take their time. Mix it up.
- **Acknowledge complexity.** "Impressive but also kind of unsettling" beats "impressive."
- **Use "I" when it fits.** First person isn't unprofessional.
- **Let some mess in.** Perfect structure looks machine-made.
- **Be specific.** Not "this is concerning" but "there's something unsettling about agents churning away at 3am."

## Patterns to detect and fix

### Content

1. **Puffery.** "pivotal moment", "testament to", "evolving landscape", "setting the stage for", "indelible mark", "deeply rooted". Cut puffery, state what happened.
2. **Name-dropping.** Listing media outlets without context. Pick one, say what was said.
3. **Superficial -ing phrases.** "highlighting...", "ensuring...", "reflecting...", "showcasing...", "fostering...". Delete or expand with real sources.
4. **Promotional language.** "nestled", "vibrant", "breathtaking", "groundbreaking", "renowned", "stunning", "must-visit". Use neutral descriptions.
5. **Vague attributions.** "Experts believe", "Industry reports suggest", "Some critics argue". Name the source or delete.
6. **Formulaic challenges.** "Despite challenges... continues to thrive." Replace with specific facts.

### Language

7. **AI vocabulary.** Additionally, crucial, delve, enduring, enhance, fostering, garner, interplay, intricate, landscape (abstract), pivotal, showcase, tapestry (abstract), testament, underscore, vibrant. Replace with plain words.
8. **Unnecessary copula avoidance.** Replace constructions such as "serves as" or "stands as" when they inflate ordinary prose. Keep established technical wording when it describes a real capability or interface.
9. **"Not just X, but Y."** State the point directly instead.
10. **Rule of three.** Forcing ideas into groups of three. Use the natural number.
11. **Synonym cycling.** Protagonist, main character, central figure, hero all in one paragraph. Pick one, repeat it.
12. **False ranges.** "from X to Y" where X and Y aren't on a meaningful scale. List topics directly.

### Style

13. **Em dash overuse.** Flag stacked or ornamental em dashes. Keep a single dash when it expresses a genuine aside or sharp break, and do not replace punctuation mechanically.
14. **Colon overuse.** Colons are fine before a list or example. Not as mid-sentence connectors. "If you're coming from traditional automation: instead of registering event handlers, you describe conditions" adds nothing with the colon. Rewrite to let the point stand on its own without comparison framing. "Describing when the scheduler should fire works best as plain English." Same meaning, no crutch punctuation.
15. **Boldface overuse.** Don't bold every proper noun or acronym.
16. **Inline-header lists.** The tell is a bold label and colon that restates the line: "**Performance:** Performance improved...". Convert those to prose. A bold lead-in that ends in a period, names the item, and is followed by genuinely new detail ("**Schema in TypeScript.** Tables live in one file.") is fine, not a tell.
17. **Title case headings.** Use sentence case.
18. **Decorative emojis.** Remove from headings and bullets.
19. **Curly quotes.** Replace with straight quotes.

### Communication artifacts

20. **Chatbot phrases.** "I hope this helps!", "Let me know if...", "Of course!", "Certainly!", "Found the smoking gun!" Remove.
21. **Cutoff disclaimers.** "While specific details are limited..." Find sources or remove.
22. **Sycophantic tone.** "Great question! You're absolutely right!" Respond directly.

### Filler

23. **Filler phrases.** "In order to" becomes "To". "Due to the fact that" becomes "Because". "It is important to note that" gets deleted.
24. **Excessive hedging.** "could potentially possibly be argued that it might" becomes "may".
25. **Generic conclusions.** "The future looks bright." State specific plans or facts.

### Jargon

26. **Abstract metaphor nouns.** Treat words such as "substrate", "vector", "surface", "harness", "primitive", and "modality" as possible metaphorical overuse, not banned words. Replace them only when they are vague or figurative and a concrete term is clearer. Keep them when they name a real technical concept.

### Plain speech

27. **Say what it does, not how it feels.** "the database stays close at hand", "SQL you can read", "types that follow your schema" name a feeling. The fix names the mechanism or a number: "`.toSQL()` returns the exact string sent to the database", "a column rename fails the build". Ask what the sentence tells the reader to do or know, then write that. If you can't restate it as a concrete instruction, fact, or number, cut it. One more check: if the sentence could appear unchanged in another project's docs, it says nothing about this one. Cut it.
28. **Shorten or split dense sentences.** If the reader has to backtrack to parse a sentence, break it in two or drop clauses. One idea per sentence.
29. **Active voice.** Prefer active voice when it makes the actor or action clearer. Keep passive voice when the actor is unknown, irrelevant, obvious, or when the result is the point.
30. **Cut adverbs, or use a stronger verb.** "runs quickly" becomes "is fast" or the number. "significantly improves" becomes the measured delta. An adverb propping up a weak verb means the verb is wrong.
31. **Prefer the plain word.** "utilize" becomes "use", "leverage" becomes "use", "facilitate" becomes "help", "numerous" becomes "many", "in the event that" becomes "if". The fancier synonym is rarely clearer.

## Local scope

This skill owns the prose pattern catalog for this machine. Three neighbours own the rest, so keep each meaning in one place:

- **`anti-slop-standard`** — the code rules (write it once, only what is reached, the direct thing) and the handover check. It routes all prose questions here.
- **`humanizer`** — the deep rewrite workflow: voice calibration from a writing sample, and a draft-audit-final loop. Reach for it when finished prose needs reworking rather than a pass for tells.
- **`technical-writing`** — document structure for docs, RFCs, and readmes (Diátaxis mode, sentence style, one-thought-per-sentence, ambiguity). It applies this catalog to everything it touches.

Apply this catalog during authoring, but do not churn unchanged sentences merely to make them sound different.
