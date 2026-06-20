# Lesson and activity patterns

Use this reference to select an interaction that matches the concept, learner
state, and evidence needed.

## Contents

1. Progression architecture
2. Activity selection
3. Hint ladder
4. Misconception repair
5. Practice construction
6. Mastery evidence
7. Lesson-authoring format

## Progression architecture

Use the smallest sequence that achieves the objective:

1. **Orient** - State the capability and connect it to something the learner
   already recognizes.
2. **Elicit** - Ask for a prediction, estimate, choice, trace, or explanation.
3. **Model** - Supply the smallest representation or worked example that resolves
   the bottleneck.
4. **Guide** - Solve a near-neighbor with prompts or missing steps.
5. **Perform** - Ask for an independent solution on a familiar form.
6. **Discriminate** - Mix examples and non-examples or competing methods.
7. **Transfer** - Change the context, representation, or surface form.
8. **Retrieve** - Revisit later without the original cues.
9. **Teach back** - Ask the learner to explain the structure and likely trap.

Do not require every stage in a short explanation. Do not skip independent
performance in a mastery session.

## Activity selection

### Mechanism or causal system

Use:

- predict-observe-explain;
- change one variable and predict the consequence;
- order a causal chain;
- locate a bottleneck or feedback loop;
- test a counterfactual;
- distinguish correlation from mechanism.

Evidence sought: the learner can track direction, dependencies, and boundary
conditions rather than repeat vocabulary.

### Mathematics or quantitative reasoning

Use:

- estimate sign, scale, or range before calculating;
- connect a concrete quantity, diagram, table, graph, and expression;
- solve one step and justify the operation;
- compare two valid methods;
- diagnose an incorrect solution;
- vary a parameter and predict what remains invariant;
- create an example satisfying stated constraints.

Evidence sought: representation choice, structural reasoning, and error checking,
not only arithmetic accuracy.

### Programming and algorithms

Use:

- trace state through a tiny example;
- predict output before running code;
- identify an invariant;
- debug a minimal failing case;
- complete a missing line or branch;
- compare implementations with the same behavior;
- change an input constraint and revise the design;
- explain time or space growth using concrete input sizes.

Evidence sought: a step-by-step state model and the ability to transfer beyond the
memorized syntax.

### Classification or conceptual boundaries

Use:

- examples and near-miss non-examples;
- sort cases and explain the rule;
- identify the smallest change that flips the category;
- compare necessary and sufficient conditions;
- generate a counterexample;
- resolve two cases that share surface features but differ structurally.

Evidence sought: the learner can articulate and apply the boundary.

### Abstract theory

Use:

- one anchor example and one deliberately different example;
- analogy followed by "where does the analogy break?";
- claim-evidence-assumption maps;
- competing explanations for the same observation;
- translate between plain language and formal terms;
- derive a consequence rather than restating a definition.

Evidence sought: relational understanding and awareness of assumptions.

### Process, protocol, or workflow

Use:

- reorder shuffled steps;
- choose the next action from a state;
- identify the purpose and failure mode of each stage;
- run a small case through the workflow;
- remove a step and predict the consequence;
- compare normal, edge, and failure paths.

Evidence sought: conditional use of the process, not rote sequence recall.

### Dense source material

Use:

- extract the central claim;
- map claims to evidence;
- identify definitions and hidden assumptions;
- turn a paragraph into a causal or dependency diagram;
- compare the author's model with an alternative;
- apply the model to a fresh case.

Evidence sought: reconstruction and application rather than summary alone.

## Hint ladder

Select the least revealing hint likely to produce a new attempt.

| Level | Tutor move | Example |
| --- | --- | --- |
| 1. Goal | Restate the target or ask what is known. | "What quantity must stay equal on both sides?" |
| 2. Attention | Point to the relevant feature. | "Watch what happens to the loop condition after the last update." |
| 3. Principle | Recall a rule or simpler analogue. | "Try the same reasoning on 2 items before 20." |
| 4. Structure | Expose a subgoal, representation, or missing setup. | "Split the force into horizontal and vertical components." |
| 5. Worked step | Demonstrate one decisive step, then return control. | "First substitute the boundary value; now you take the next step." |
| 6. Resolution | Give the answer and reasoning, then test a near-neighbor. | "The key is X because Y. What changes if Z?" |

Escalate when a hint produces no new reasoning. Do not repeat the same hint in
different words indefinitely.

## Misconception repair

### Find the earliest divergence

Ask the learner to expose a short chain:

1. What did you think the goal was?
2. Which principle or representation did you choose?
3. What was the first step?
4. What result did you expect?

Repair the first incorrect premise or move. Later errors may disappear
automatically.

### Preserve what is valid

Use this response shape:

- "Your reasoning that ___ is useful."
- "The first place it changes is ___."
- "That matters because ___."
- "Try this smaller or contrasting case: ___."

Do not use the first sentence if nothing in the reasoning was valid.

### Choose the repair

| Symptom | Likely issue | Repair |
| --- | --- | --- |
| Repeats a memorized rule in the wrong setting | Boundary not understood | Contrast example and near-miss; ask what feature flips the choice. |
| Can follow but cannot start | Method-selection gap | Mix two problem types and ask which representation or method applies. |
| Gets lost midway | Working-memory overload | Externalize state in a table, diagram, labels, or smaller subgoals. |
| Correct procedure, no explanation | Fragile schema | Ask why each step preserves the goal; compare with an invalid step. |
| Correct on identical forms only | Surface memorization | Change representation, context, order, or irrelevant details. |
| Repeated random guesses | No usable model | Stop quizzing; give a concrete model or worked example. |
| Overconfident wrong answer | Miscalibrated confidence | Ask for confidence before feedback, then use a decisive counterexample. |
| Knows idea but makes slips | Automaticity gap | Use short, accurate practice with immediate correction, then space it. |

## Practice construction

Build a practice set around one learning objective:

1. one straightforward item;
2. one item varying a surface feature;
3. one common misconception trap;
4. one mixed item requiring method selection;
5. one transfer or construction item.

For interactive tutoring, present these progressively rather than as a batch.
For lesson authoring, include solutions and misconception notes separately.

### Problem quality checks

Confirm:

- the prompt has enough information;
- terminology and units are consistent;
- the intended answer is correct;
- alternate valid answers are accepted or explicitly constrained;
- difficulty comes from the target concept, not accidental ambiguity;
- distractors correspond to plausible misconceptions;
- the learner can explain why the answer is right;
- the final transfer changes something meaningful, not only numbers or names.

## Mastery evidence

Use a small evidence ledger:

| Dimension | Evidence |
| --- | --- |
| Recall | Retrieves the principle without the original cue. |
| Explanation | States why it works and names an assumption or boundary. |
| Application | Solves a familiar form independently. |
| Discrimination | Selects the right method among plausible alternatives. |
| Error detection | Finds and repairs a flawed solution. |
| Transfer | Applies the structure in a changed context or representation. |
| Calibration | Confidence broadly matches performance and uncertainty is named. |

Call a concept secure only when evidence comes from more than one dimension. Call
it transfer-ready only after an independent transfer task or strong teach-back.

## Miniature guided-session example

Topic: recursion for a learner who understands functions but loses track of
recursive calls.

1. **Target:** Trace a recursive function and explain what happens before and
   after the recursive call returns.
2. **Diagnostic:** Show a three-line countdown function and ask, "For input 3,
   what prints first, and what is waiting?"
3. **Likely misconception:** The learner imagines the function restarting and
   erasing the earlier call.
4. **Model:** Draw a three-row table with one row per active call: input, current
   line, and what must happen after the inner call finishes.
5. **Guided action:** Ask the learner to add the row for input 2.
6. **Fade:** Give the table headings but no rows for a similar function.
7. **Discriminate:** Compare a version that prints before the recursive call with
   one that prints after it.
8. **Transfer:** Ask the learner to predict the order for a recursive traversal
   of a two-level tree.
9. **Teach-back:** "Explain the call stack without using the phrase 'it calls
   itself.'"

The example is a pattern, not a mandatory script. Preserve the target and
evidence logic while adapting the language, representation, and difficulty.

## Lesson-authoring format

When asked to create a complete lesson, use:

1. **Learning target**
2. **Prerequisites**
3. **Likely misconceptions**
4. **Diagnostic prompt**
5. **Concrete or visual model**
6. **Guided interaction**
7. **Independent practice**
8. **Mixed and transfer practice**
9. **Retrieval checkpoint**
10. **Solutions and feedback notes**
11. **Mastery criteria**
12. **Next lesson**

Keep learner-facing material free of answer leakage. Verify every item before
shipping the lesson.
