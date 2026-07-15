# Pedagogy and Flow

Use this reference to turn a topic list into an applied course that can verify
performance.

## Contents

1. Learner contract
2. Outcome and scope design
3. Authentic course spine
4. Module anatomy
5. Exercise and grading contract
6. Hint and solution policy
7. Tool-lab behavior
8. Competency and progression
9. Runbooks and portfolio evidence
10. Content authoring rules
11. Failure modes

## 1. Learner contract

Design for one primary learner even when more people may eventually use the
course. Record:

- current role, prior knowledge, and familiar tools;
- target role or real-world performance;
- likely anxiety points and misconceptions;
- weekly time, total duration, and interruption pattern;
- device, operating system, connectivity, and accessibility constraints;
- artifacts a reviewer, manager, or hiring panel can inspect.

Do not infer beginner status from lack of programming experience. Preserve
existing domain expertise and use it as the bridge into technical work.

## 2. Outcome and scope design

Write outcomes as observable performances:

- weak: "understand joins";
- strong: "choose a join that retains entities with no activity, explain why,
  and diagnose a query that silently drops them."

For each outcome, name:

- the task;
- the conditions and available tools;
- the quality bar;
- the edge case;
- the evidence produced;
- the non-technical explanation expected.

Keep an explicit in-scope and out-of-scope list visible in the course. Every
module must support an outcome. Cut interesting topics that do not fit the time
budget or target performance.

Use a one-version rule. Select one teaching tool for each concept and commit to
it. Add comparison material only after the learner can use the default.

## 3. Authentic course spine

Prefer one growing story, dataset, system, investigation, product, or operational
project across the course. It should:

- begin with a manual or incomplete process;
- contain realistic dirt, failure, ambiguity, or constraints;
- grow in complexity as new concepts become necessary;
- produce artifacts that assemble into one coherent portfolio project;
- end with a capstone that replaces or improves the original process;
- support a before/after measure such as time, error rate, cost, or risk.

Generate planted defects deliberately and maintain a defect manifest:

| Defect | First visible | Learner task | Check that catches it |
|---|---|---|---|
| duplicate entity | early exploration | identify grain | uniqueness check |
| missing value | cleaning | choose handling | null invariant |
| broken reference | modelling | trace lineage | relationship check |
| transient failure | automation | retry safely | deterministic fault test |

Do not announce every planted defect. The learner should discover some defects
through inspection and failed checks.

## 4. Module anatomy

Use this default order:

1. **Prerequisite gate**
   - Ask at most three targeted questions or tasks.
   - Route a failure to the exact missing concept or exercise.
   - Do not restart the whole prior module.
2. **Understand**
   - State the real problem and why it matters.
   - Build intuition with a concrete system, object, trace, or visual.
3. **Reason**
   - Ask the learner to predict, compare, explain, or debug before giving a rule.
   - Expose the decision boundary and the common misconception.
4. **Guided practice**
   - Supply orientation and a bounded next move.
   - Check the actual action, not a "done" button.
5. **Independent solution**
   - Restate the task in stakeholder language.
   - Remove scaffolding that is no longer needed.
   - Include at least one realistic edge case.
6. **Operate**
   - Require exact run steps, success signals, failure signals, recovery, and
     escalation.
   - Add a short teach-back for a non-technical audience when communication is
     part of the target role.
7. **Exit task and artifact**
   - Execute and machine-check a task.
   - Save a usable file, report, model, configuration, analysis, or runbook.

Keep explanation adjacent to the decision it supports. Avoid long prose followed
by an unrelated lab.

## 5. Exercise and grading contract

Represent each executable exercise as structured data. At minimum include:

- stable ID and module;
- stakeholder brief;
- runtime or tool mode;
- starter state;
- seeded inputs;
- expected behavior;
- checks;
- progressive hints;
- solution;
- artifact path;
- execution-level label: real, browser-isolated, or field.

Use a shared four-part quality rubric:

1. **Correct:** the expected behavior or output matches.
2. **Robust:** null, empty, invalid, repeated, and failure paths are handled.
3. **Readable:** another practitioner can maintain it.
4. **Documented:** another practitioner can run and recover it.

Use consistent result states:

| State | Meaning | Feedback |
|---|---|---|
| Pass | every required check passed | show evidence and next action |
| Runs, wrong | execution succeeded; behavior differs | show result/invariant diff |
| Error | runtime or tool failed | show raw error with relevant context |
| Rejected | behavior may work but violates a rule | name the rule and consequence |

Do not grade only by source text. Pattern checks may enforce an anti-pattern or
required construct, but behavioral checks remain the authority.

Every solution must pass its own checks in automated tests. An unsatisfiable
exercise is a release blocker.

## 6. Hint and solution policy

Hints are instructional support, not currency. Do not deduct points or attach
shame to their use. Log them to understand where the course is unclear.

Use this ladder:

1. identify whether the tool, concept, or argument class is wrong;
2. point to the relevant state, input, or requirement;
3. narrow the next move without supplying the final expression;
4. reveal exact guided syntax after the configured honest-attempt threshold or
   when the learner explicitly asks.

Count meaningful attempts, not clicks. A blank submission should not unlock the
solution.

Reveal the model solution after a pass or a default of three honest attempts.
Open it in comparison mode, not as the learner's editable answer. Require one
meaningful difference, correction, or tradeoff to be recorded in the runbook or
debrief.

## 7. Tool-lab behavior

A visual terminal is not enough. A faithful command lab must parse and check:

- command name;
- arguments and flags;
- current path or active context;
- filesystem, repository, session, or service state;
- side effects and resulting state;
- exit status and output;
- repeated and out-of-order actions;
- pasted Unicode variants where names or punctuation matter.

When the learner uses the right command with the wrong argument, say so. When the
tool is wrong, name that distinction. Preserve command history and allow a clean
replay that resets lab state without erasing earned course evidence.

For a simulator, support only the commands needed for the course and respond
plainly to unsupported commands. Do not imply it is a general shell.

Prefer the real engine when it can run safely and consistently. Use deterministic
fault injection for rate limits, timeouts, malformed records, failed jobs, and
other reliability lessons.

## 8. Competency and progression

Use evidence levels rather than points:

- **Understand:** explains the concept or predicts behavior accurately.
- **Guided:** completes the workflow with prompts.
- **Independent:** completes a fresh task without hints or a tutorial.
- **Operational:** handles failure and leaves another person able to run it.

Progression should reflect dependencies. Use a DAG when modules have real
prerequisites; use a simpler map when they do not. Suggested statuses:

- pending: upstream evidence missing;
- running: active work exists;
- success: exit evidence passed;
- failed: exit evidence failed and downstream remains blocked;
- stale: prior evidence exceeds a meaningful freshness interval.

Avoid XP, streaks, confetti, and completion theater. Show the next action and why
it is available or blocked.

## 9. Runbooks and portfolio evidence

A runbook answers:

- What does this process produce and for whom?
- What exact prerequisites and inputs are required?
- What exact steps or commands run it?
- What proves success?
- What signals failure or stale output?
- How is it retried or recovered safely?
- How is it rolled back?
- When and to whom is it escalated?

Require useful minimum content, not merely a non-empty text area. Persist drafts.
Keep runbooks on their own surface so they support operation without crowding the
active lab.

Portfolio export should preserve meaningful names and a coherent repository
shape. Prefer real files over screenshots. Field modules may accept a screenshot
only when the actual external tool cannot export a stronger artifact.

## 10. Content authoring rules

- Store authored content outside view markup.
- Use one term for one concept across the course.
- Define a term at first use, then keep the name stable.
- Use real domain names, values, and constraints instead of foo/bar examples.
- Show anti-patterns with the consequence and a corrected alternative.
- Keep code and datasets executable; never publish untested snippets as answers.
- Write briefs in stakeholder language and checks in technical language.
- Make the artifact and definition of done visible before the learner starts.
- Treat solution files and expected outputs as protected course internals.

## 11. Failure modes

Reject these patterns:

- slide decks with a cosmetic terminal;
- self-attested "mark complete" exercises;
- multiple-choice exit checks for production skills;
- isolated toy exercises with no shared story or artifact;
- hints that immediately disclose the answer;
- solutions that have never run against their checks;
- a notes panel permanently consuming lab width;
- fake progress that ignores failed prerequisites;
- tool alternatives presented before the learner can use one;
- content welded into a single component or HTML file;
- badges or certificates with no exportable evidence;
- error messages rewritten so heavily that the learner never sees the real tool.
