# Question lenses

A lens is the angle a question takes on one concept. Rotating lenses is what
turns recall into understanding: the same idea asked as "what is it," then "why
would you care," then "what happens if," then "use it here." Pick the lens
from the concept's kind and its status, never from habit.

Every question opens with a short scenario: one or two sentences that put the
learner somewhere real, then one question. Keep numbers small enough for a
calculator and a phone screen.

## Write an unambiguous scenario

A real-world scenario is read as real, so it has to behave like the real
thing:

- **Say how the data changes, in every part that uses it.** "A new 8th check
  of 180 ms is added" and "the 29 ms reading is replaced by 180" give
  different answers (45 and 26 vs. 47.29 and 25). Don't state it once in one
  bullet and leave a later bullet to guess.
- **Default to how the real system works.** Logs, checks, and surveys gain
  new observations; they don't rewrite old ones. If a question needs a
  replacement, call it a correction ("the 29 was a typo for 180").
- **Give every number a unit and a count.** "7 checks, in ms."
- **When you bridge from an earlier concept, name the difference.** Reusing a
  familiar test ("who decides?") for a new job without saying so makes the new
  question look like the old one. Random *selection* (who gets into the study)
  and random *assignment* (who gets the treatment) both use chance for
  different jobs; say which one the question is about.
- **A miss caused by the question's wording isn't scored.** Keep the row as
  history, but label its Item without a `Core N` so it doesn't count toward
  the concept's status, and say why in the reason.

## Lenses for every concept

| Lens | The learner has to… | Example stem (networking field) |
| --- | --- | --- |
| **plain words** | say it in their own words, as if to a teammate | "A new hire asks what a *sample* is versus a *population*. What do you tell them?" |
| **why it matters** | name the decision it supports or what breaks without it | "Why does it matter whether your 200 log lines are a sample or every line from last night?" |
| **how it works** | walk the mechanism, step by step | "Walk me through how you'd pick every 25th log line fairly." |
| **real-world map** | apply it to a new situation and make the call | "You test a new firewall rule on 10 servers you picked yourself. What's wrong with calling that an experiment?" |
| **contrast** | separate it from its nearest neighbor by the deciding feature | "Stratified or cluster: you sample some hosts from every subnet. Which, and what tells you?" |
| **error hunt** | find and fix a wrong claim or step | "A report says 'median latency rose because of one 900 ms spike.' What's wrong?" |
| **predict** | say what happens when one thing changes, before computing | "One ping jumps to 400 ms. Which moves more, the mean or the median, and why?" |
| **teach-back** | explain it to a beginner without jargon (use last, as the transfer check) | "Explain standard deviation to a manager who just wants to know if the network is stable." |

## Extra lenses for formulas and procedures

For any concept with an equation or a step procedure (class width, mean, s,
quartiles, weighted average, relative frequency, IQR), add these. They are the
"not dry" version of "know the formula."

| Lens | The learner has to… | Example stem |
| --- | --- | --- |
| **which tool** | choose the formula or measure for the situation, and say why | "You want one number for typical latency that a single outage won't wreck. Which measure, and why?" |
| **anatomy** | say what each part of the formula is doing | "In s = √[Σ(x − x̄)² ÷ (n − 1)], why square the deviations? Why n − 1 instead of n?" |
| **compute** | work it with numbers, showing each step | "Pings: 20, 22, 23, 25, 30 ms. Find x̄ and s. Show the deviation table." |
| **read the result** | turn the number into a sentence with units and meaning | "s came out 3.8 ms. What does that tell you about this connection?" |
| **stress test** | say what makes the result move or mislead | "When would a grouped-data mean be noticeably off from the real mean?" |
| **value** | say what the number adds that the raw list doesn't | "Your boss has 500 ping times. What does giving them the IQR add?" |

A formula concept is not understood until the learner can **compute**, **read
the result**, and answer **anatomy** or **stress test**. Computing alone is
recall with a calculator.

## Choosing the lens

- **Diagnostic sweep (unassessed concepts):** one question per concept, using
  **real-world map** for ideas and **compute** + **read the result** (as one
  item) for formulas. Those two reveal the most in one answer.
- **After a miss (fragile):** break it down with `teach-complex-concepts`,
  then queue **two** twins at least 3 questions later: same logic, different
  scenarios. Repeating the same stem, numbers, or picture tests memory of the
  card, not understanding.
- **Twin after a confident correct answer:** harder, with the same deciding
  cues. Add a step, a distractor, or a depth lens; keep the decision the same.
- **Developing concepts:** push toward **why it matters**, **anatomy**, **stress
  test**, or **contrast**, the lenses that show depth.
- **Near-secure concepts:** finish with **teach-back** or a **real-world map**
  in a field the learner hasn't seen yet.

## Scenario sources

Use the learner's field first (stored in their profile or stated in the
session), then everyday life, then the course's own examples, reworded. For a
networking and cybersecurity learner, strong anchors are:

| Concept family | Scenario anchor |
| --- | --- |
| Individuals, variables, levels | a table of devices with OS (nominal), severity (ordinal), uptime hours (ratio) |
| Sampling | auditing every kth firewall log line; surveying users per office (strata) or whole offices (clusters) |
| Study design | rolling a config change to random vs. hand-picked servers; a placebo-style "no-op" change |
| Frequency tables, histograms, ogives | response times grouped into classes; "how many requests finished under 200 ms" |
| Graph choice, Pareto | alert types ranked by count; bandwidth over a week as a time series |
| Stem-and-leaf | latency readings where the exact values still matter |
| Center, resistance, skew | ping times with outage spikes |
| Spread, s, variance | jitter as spread; a stable vs. an unstable link with the same average |
| Percentiles, quartiles, IQR | "95th-percentile latency" as a service target; the middle 50% of response times |

Industry facts used as scenery (for example, that teams track 95th-percentile
latency) are context, not course content. Say so in one clause if the learner
might mistake them for something on the exam.

## Grading an answer

Classify with `teach-complex-concepts`' own response classes, then log it:

| Classification | Logged result |
| --- | --- |
| correct and reasoned | `correct` |
| correct but fragile (right answer, thin or missing why) | `partial` |
| productive error | `partial` |
| guess, misconception, repeatedly stuck, or answer shown by the tutor | `missed` |

Give feedback in this order: what's right (specifically), the first thing that
went wrong, the fix in one or two sentences. Then move on. Don't lecture.

**Before marking an answer wrong, check it against every reasonable reading
of the question.** If the learner's numbers are right for a reading the
wording allowed (especially the real-world one), the answer is correct: grade
it so, say which reading they used, show the other reading's result as
context, and fix the question's wording for next time. If a result was already
logged, regrade the row in `study-log.md` (the learner asking you to regrade
counts as the confirmation) and adjust any queued twin to match.
