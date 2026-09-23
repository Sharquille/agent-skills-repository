# Practice planning and proficiency checks

`Practice.md` is an Obsidian question **bank**. Its size follows the taught content, not a fixed 8–12-card quota. A bank covers source-backed decisions; it does not prove a student has mastered them. Keep official answered stems in Quiz why and graded work outside the bank.

## Build the outcome inventory

Before writing questions, make `practice-plan.md` beside `Practice.md`. Use the ledger and Core notes to list **atomic, testable outcomes**: one decision or explanation that a reader can answer from the supplied source alone. A heading may hold several decisions (sampling methods); several headings may repeat one decision. Split or merge by the response the learner must produce, then record the Core heading and source locator. Exclude orientation headings, unrevealed keys, checklist names without explanatory body, unreadable material, and later sections. A name-only list may earn a recall item, but not an invented application question.

For each outcome `i`, record a risk flag `r_i`:

- `r_i = 1` if the source teaches a confusable contrast, a procedure or worked application, a documented error/trap, or explicit lecture emphasis that calls for a second **different** situation.
- `r_i = 0` otherwise. Multiple reasons still add only **one** extra item; record the reasons, not extra multipliers. Lecture emphasis needs a lecture artifact, not a guess.

The minimum bank count is:

```text
q_i = 1 + r_i
Q_min = Σ q_i = A + H
```

`A` is the number of earned, answerable atomic outcomes. `H` is the number with `r_i = 1`. This is a local **coverage heuristic**, not an experimental formula for guaranteed proficiency. No item is counted until its stem and answer pass the editorial check below. Give each item one primary outcome ID; a second topic mentioned in its scenario does not satisfy another outcome's floor. Audit existing items by the same rule. If `v_i` eligible items already target outcome `i`, the authoring gap is `Σ max(0, q_i − v_i)`. Preserve a useful extra item even if a section exceeds its minimum.

For an extra item, change both the surface situation **and** the response demand where possible: classify in one item, explain or correct an error in the other. For a confusable pair, test the distinction rather than asking for two independent definitions. Do not use an official question with its numbers changed as a shortcut.

## Sequence the item roles

Label the item role in the Primary item or Extra item cell. The roles control
order; they are not extra content types:

- **foundation** — one primary item for every outcome. Keep newly taught
  outcomes in a small blocked group until the learner can make the basic
  decision without a cue.
- **discriminate** — the varied extra for a confusable family. Use it only after
  each alternative has a foundation, and ask the learner to choose between
  plausible alternatives using the decisive feature.
- **transfer** — the varied extra for a procedure, worked application, trap, or
  emphasized objective. Change the surface situation and, where possible, the
  response demand. Error correction is a transfer item, not a fourth role.

Do not randomly interleave a whole chapter, isolated vocabulary, or unrelated
expository facts. Interleave related choices when discrimination is the skill;
otherwise establish the foundation first and vary the context afterward.

### Fade worked examples only for taught procedures

When the source demonstrates a procedure, Core should show one correct,
source-grounded worked example. Make the primary Practice item a completion
problem with one meaningful step withheld; make the flagged extra an
independent near-transfer problem. If an attempt is missed, restore the smallest
helpful cue, then fade it again on the next different problem. Do not manufacture
a worked procedure from a name-only list, and do not apply this ladder to prose
or terminology.

Ask the learner to explain why on causal, contrast, error-correction, or
evidence-analysis items where the reason reveals understanding. Do not append a
generic self-explanation prompt to every recall item or every line of a worked
example.

## Make the bank usable

Put the full, answerable prompt in the folded `[!question]-` title; its body stays hidden until tap. Group items by the source's sections. Use consecutive `Q01`, `Q02`, … IDs and short groups of about 6–8 questions per study round. `ceil(Q_min / 8)` is only a **planning estimate** for rounds; stop a round after about 10–15 minutes or when attention fails. A large bank is available across days, not one compulsory sitting.

Every revealed answer must state the decision, give the source-based reason, resolve offered alternatives, and point to a specific numbered Core topic. Reject a card if its stem states the verdict, names the answer category before the learner chooses it, contains several unrelated tasks, uses unexplained shorthand, or its key hedges with “maybe.” Review technical corrections against a primary source and note the source conflict in the ledger. Preserve exact course terminology where it matters.

In `practice-plan.md`, use a table with `Outcome ID | Core/source anchor | Learner decision | r_i and reason | Primary item | Extra item`. Write the role beside each question ID, for example `Q01 foundation` or `Q02 discriminate`. Reconcile the total: each earned outcome has one eligible item; every flagged outcome has a second eligible, varied item. Record unavailable objectives separately so a missing chapter page never silently inflates or shrinks `A`.

## Optional preview and cumulative review

For a long section with clear source objectives, the author may put **one or
two** specific preview questions before first reading. Follow each promptly with
the source explanation and feedback. Omit previews for short sections, isolated
terminology, missing source content, or when they add confusion. Preview items
do not count toward `Q_min`, the three-session check, or mastery; label them
Preview and keep them outside the numbered bank.

After foundation attempts exist across completed sections, a cumulative session
may sample their existing Practice items one at a time. Mix related distinctions
or the same decision in changed contexts; do not copy the items into a second
bank and do not randomize every topic merely to call it interleaving. Record
only the attempts that actually occurred.

These limits are deliberate. A prequestioning meta-analysis found gains mainly
for the content actually prequestioned
([Pan et al., 2024](https://doi.org/10.3758/s13423-023-02353-8)); an
interleaving meta-analysis found effects depended on the material and sometimes
favored blocking
([Brunmair and Richter, 2019](https://doi.org/10.1037/bul0000209)); and the
worked-example evidence used here is strongest in mathematics
([Barbieri et al., 2023](https://doi.org/10.1007/s10648-023-09745-1)). The
sequence is a guarded authoring rule, not a universal prescription.

## Decide when to restudy

The bank count is authoring evidence. Learner proficiency requires **unaided** first-attempt answers and feedback over time. Use this practical check per outcome:

1. Attempt an item before opening the answer. Record correct, partial, or missed only from an actual attempt.
2. After a miss, read the matching Core topic and explain the reason aloud; try a different situation later. A revealed answer copied back immediately is not a successful retrieval.
3. Revisit on separate sessions, such as Day 1, Day 3, and Day 7. Mark the outcome provisionally secure only after three unaided correct attempts across those sessions, including the varied extra item for `r_i = 1` and a cold Day 7 example or sort. An error resets that outcome's current run; the rest of the chapter does not reset.
4. End a round at the time limit. Treat the **section** as provisionally covered only when every earned outcome meets the check; use a later mixed review to test retention. Never invent scores, dates, or mastery from a completed file.

This three-session rule is a conservative workflow choice for this kit, not a universal mastery threshold. Retrieval practice and spacing have broad evidence ([Dunlosky et al., 2013](https://www.psychologicalscience.org/publications/journals/pspi/learning-techniques.html)). In experiments on conceptual material, [Rawson and Dunlosky, 2011](https://eric.ed.gov/?id=EJ934616) studied repeated correct recalls and spaced relearning; their specific dosage cannot be inferred from this bank's item count. If the learner supplies results, record them in `study-log.md`; never fabricate them or create a reminder without a request.

Do not tailor the kit to a declared learning-style category; the meshing claim
lacks an adequate evidence base
([Pashler et al., 2008](https://doi.org/10.1111/j.1539-6053.2009.01038.x)).
