# TRACE: the meta-loop

TRACE is the one loop taught across every substrate. It does not carry
domain content by itself — each step is a slot that a substrate-specific
move (from `moves/*.md`) fills in for the case at hand.

- **T — Target**: what is the question actually asking? Distinguish "what
  caused this" from "what should I do" from "what does this term mean" — the
  rest of the loop depends on getting this right.
- **R — Record**: what facts are directly given? Nothing inferred yet — a
  common failure is smuggling an inference into this step disguised as an
  observation.
- **A — Apply**: what principle connects the recorded facts to an answer?
  This is where a substrate move usually does its work (a causal-inference
  move, a definitional move, an estimation move).
- **C — Check**: what assumptions, alternatives, or edge cases matter? This
  is where falsifiability, controlled-comparison, and bias-check moves plug
  in — Check is the step most failures skip.
- **E — Express**: state the strongest conclusion the evidence actually
  supports — no stronger, no weaker. Calibration moves govern this step: the
  confidence stated here should track the evidence recorded in R and the
  gaps found in C, not the learner's prior belief.

## Worked example

Prompt: "A store changed its sign and sales doubled the next month. What can
we conclude?"

A tempting first-pass answer treats "the new sign was more visually
captivating" as a fact and concludes the sign caused the increase. Walking it
through TRACE catches this:

- **Target**: what can we validly conclude from this evidence — not what's
  the most likely story.
- **Record**: only two facts are given — the sign changed, and sales doubled
  the following month. Nothing about *why* the sign worked, what else changed
  that month, or the base rate of month-to-month sales swings.
- **Apply**: temporal sequence (*after*) is evidence *for* a causal claim but
  does not establish it (inference deck: correlation vs. causation).
  "Captivating" is not evidence anyone recorded — it is an invented
  explanation smuggled in at Record.
- **Check**: alternative explanations exist (a promotion, a seasonal
  pattern, a competitor closing) and the case gives no way to rule them out.
  Falsifiability move: what would we expect to see if the sign *did* cause
  it, versus if it didn't? Controlled-comparison move: the cleanest test
  changes one variable (the sign) and holds the rest constant — this
  real-world case did not do that, so the evidence is weak by design, not
  just by bad luck.
- **Express**: "Sales doubled after the sign changed. The sign may have
  contributed, but this evidence alone cannot establish that it caused the
  increase — other factors could equally explain it." Confidence: low, and
  that low confidence is *because* Check surfaced live alternatives, not a
  hedge for its own sake.

## Teaching notes

- Introduce TRACE by name the first time, walking one case end-to-end as
  above. After that, invoking it by name ("run TRACE on this one") is enough
  — do not re-explain the five letters every session.
- The most common learner failure is skipping straight from Record to
  Express, or worse, letting an invented explanation enter at Record instead
  of Apply. Naming the exact step where the slip happened is more useful
  feedback than a general "not quite."
- A precision failure specific to Express: overclaiming certainty language
  ("must," "proves," "establishes") when the evidence only supports weaker
  language ("suggests," "is consistent with," "may indicate"). See the
  calibration deck's hedging-verb move.
