# Quantitative moves (Math / numeric intuition)

Moves for sanity-checking a number before trusting it, and for producing a
usable estimate without full data. Mostly plug into TRACE's Apply and Check
steps.

**Order-of-magnitude (Fermi) estimation.** Break an unknown quantity into
factors you *can* estimate, multiply, and sanity-check the result's number of
digits before refining it. The goal is "is this 10, 100, or 100,000" before
"is this exactly 847."
*Diagnostic case*: "Roughly how many piano tuners are there in Chicago?" —
what factors would you multiply, and what order of magnitude do you land on?
*Common failure*: refusing to answer because exact data isn't available,
instead of decomposing into estimable factors.

**Base rates.** Before updating on a specific piece of evidence, know how
common the thing being tested for is in general — a rare condition stays
unlikely even after a positive test with a low false-positive rate, if the
base rate is low enough.
*Diagnostic case*: "A test for a rare disease (1 in 10,000 people) correctly
identifies 99% of people who have it, and correctly clears 99% of people
who don't. Someone tests positive. How worried should they be?" — the base
rate calculation, not either 99% figure alone, drives the answer.
*Common failure*: anchoring on the accuracy figure and ignoring the base
rate entirely (base-rate neglect).

**Rates vs. totals.** A quantity described as a rate (per unit time, per
capita) and the same quantity as a raw total answer different questions —
conflating them produces a wrong comparison.
*Diagnostic case*: "City A has more total crimes than City B. Is City A less
safe?" — what's missing to answer this, and why does population matter?
*Common failure*: comparing raw totals across groups of different size
without normalizing.

**Regression to the mean.** An extreme measurement is disproportionately
likely to be followed by a less extreme one, purely from noise, without any
causal intervention. Mistaking this for a real effect (of a diet, a coaching
change, a new policy) is one of the most common quantitative reasoning
errors.
*Diagnostic case*: "A student scored unusually low on a test, got tutoring,
and scored higher next time. Did the tutoring work?" — what alternative
explanation does regression to the mean supply, and what would distinguish
it from a real effect?
*Common failure*: treating any post-intervention improvement after an
extreme low as proof the intervention worked.

**Proportional reasoning and scaling.** When one quantity in a relationship
changes, ask what happens to the others, and whether the relationship is
linear, or scales differently (area with the square of length, for example).
*Diagnostic case*: "A room's floor is being retiled. If both the width and
length of the room double, how does the amount of tile needed change?"
*Common failure*: assuming a linear relationship (tile needed doubles) when
floor area actually scales with the product of the two dimensions
(quadruples). A related trap: this quadratic scaling applies to floor and
ceiling area, but wall paint — with ceiling height held fixed — scales with
the room's *perimeter*, not its area, so "how much paint" and "how much
tile" are not interchangeable versions of the same question.

**Sanity-checking against a mental model.** Before accepting a computed or
quoted number, ask whether it's plausible given a rough independent estimate
— a wildly different order of magnitude is a sign of an error upstream, not
a surprising discovery.
*Diagnostic case*: a calculation yields "the population of a mid-size city
is 40 billion" — what step is almost certainly wrong, and how would you find
it without redoing the whole computation? *Common failure*: accepting an
implausible output because the arithmetic that produced it "must be right."
