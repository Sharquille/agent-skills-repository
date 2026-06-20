# Research foundations and product-pattern review

Use this reference to design substantial lessons or learning paths. It is a
practical synthesis, not a claim that one method works equally well for every
learner, domain, or objective.

## Contents

1. Review of Brilliant's public learning approach
2. Principles adopted by this skill
3. Important limits and corrections
4. Learning-science evidence
5. Source list

## Review of Brilliant's public learning approach

Research reviewed on 2026-06-20 from Brilliant's public site, help center, and
engineering/learning-design blog.

### Strong and portable patterns

| Public pattern | Why it matters | Translation for a conversational skill |
| --- | --- | --- |
| Learn by doing | Interaction exposes the learner's model and creates feedback loops. | Ask for predictions, manipulations, traces, comparisons, and constructions rather than relying on explanation alone. |
| Ask instead of tell | A learner-generated step is more diagnostic and memorable than passive agreement. | Prompt before explaining when a meaningful attempt is possible. |
| Visual and concrete before abstract | Representations can make structure perceptible and reduce needless verbal load. | Use small diagrams, tables, spatial metaphors, concrete values, and linked representations. |
| One concept with a progressive difficulty curve | Tight scope helps the learner form and refine one schema. | Select one bottleneck and vary it from simple to complex before combining it with other ideas. |
| Immediate, custom feedback | Feedback is useful when tied to the learner's action and misconception. | Respond to the first divergence in reasoning, not only the final answer. |
| Adaptive practice | Learners need different amounts and kinds of support. | Maintain a lightweight evidence model and choose the next prompt from performance, reasoning, and confidence. |
| Pretest before instruction | An initial attempt can activate prior knowledge and make later instruction more meaningful. | Use a prediction or attempt when the learner has enough context; consolidate afterward. |
| Targeted review, spacing, and mixed practice | Retrieval and discrimination support durable access and method selection. | Revisit weak concepts, mix problem types, and remove cues during review. |
| Multiple lenses on one idea | Transfer improves when the learner connects representations and purposes. | Teach the same structure through examples, visuals, notation, mechanism, and application. |
| Human-reviewed correctness and quality checks | A broken learning problem can teach the wrong model and damage confidence. | Verify solvability, answer correctness, clarity, edge cases, and alternate solutions before presenting a problem. |
| Tutoring that fades away | The end state is independent thinking, not dependence on hints. | Reduce scaffolding and ask the learner to generate the tutor's questions. |

### Product ideas that should not be copied literally

- Brilliant's graphical manipulatives, learner telemetry, content graph, and
  game engine are product infrastructure. A text agent should not imply it has
  those capabilities.
- Streaks, leagues, points, sounds, and haptics can support habit formation, but
  they are not evidence of understanding. This skill does not manufacture
  pseudo-rewards or prolong sessions for engagement metrics.
- Proprietary lesson sequences, prompts, characters, and branded tutor behavior
  should not be reproduced. Use the general pedagogical ideas to create original
  instruction.

## Principles adopted by this skill

### Interaction over exposition

Explanations remain useful, especially for novices, but each explanation should
usually prepare an action. The smallest useful loop is:

1. pose a meaningful question or prediction;
2. observe the learner's reasoning;
3. provide targeted feedback or a minimal model;
4. try a near-neighbor;
5. retrieve or transfer without the same support.

### Bounded productive struggle

Challenge can improve learning when it activates relevant knowledge and is
followed by consolidation. It becomes unproductive when the learner lacks the
prerequisites, receives no informative feedback, or repeatedly fails without a
new representation.

Use a challenge-first approach only when:

- the task can be understood before the formal method is known;
- the learner has enough prerequisite knowledge to generate a candidate;
- likely attempts will be useful during the explanation;
- the tutor can consolidate the idea immediately afterward.

Otherwise, use a concrete anchor or worked example first.

### Guidance that fades

Novices often benefit from worked examples and explicit structure. As knowledge
grows, the same guidance can become redundant. Move through this progression:

1. model a complete example;
2. ask the learner to explain key steps;
3. remove one or more steps for completion;
4. solve a similar problem independently;
5. choose the method among mixed problems;
6. transfer the structure to a new context.

### Feedback on reasoning

Good feedback answers three questions:

- What goal are we aiming for?
- What does the current response show?
- What is the smallest next move?

Do not replace reasoning feedback with generic encouragement. Avoid correcting
every detail at once; repair the earliest error that causes downstream mistakes.

### Agency and intrinsic motivation

Make progress visible through capability, not artificial urgency. Offer meaningful
choices such as context, representation, pace, or challenge level. Curiosity is
supported when the learner can form a prediction, notice a gap, and resolve it.
Relevance should illuminate the concept rather than become a forced anecdote.

### Retrieval, spacing, and interleaving

Initial learning and durable learning are different jobs. After a concept makes
sense:

- retrieve it after intervening material;
- revisit weak ideas more often than strong ones;
- mix problem types so the learner must select a method;
- vary surface features while preserving deep structure;
- include uncued review where hints and visuals fall away.

### Self-explanation and teach-back

Ask learners to explain why a step works, compare two methods, identify an
assumption, or teach the idea to a plausible novice. Judge the explanation
for causal or structural content, not polished wording.

## Important limits and corrections

### Do not make "never give the answer" an absolute

Persistent withholding can waste time, increase frustration, and turn help into
a power struggle. Use a finite hint ladder. When the learner asks directly or
has made reasonable attempts, provide the answer with reasoning and follow it
with a completion or retrieval task.

### Do not use pretesting mechanically

Pretesting is useful when an attempt activates relevant ideas. For a learner with
no usable entry point, begin with orientation, a concrete case, or a worked
example. A blind guess supplies little diagnostic value.

### Do not mistake activity for active learning

Clicking, choosing, or chatting is not automatically cognitively active. The
action must require the learner to retrieve, discriminate, predict, explain, or
construct something relevant to the objective.

### Do not overload the visual channel

Visuals help when they expose relationships. Decorative imagery, separated
labels, or multiple competing representations can increase cognitive load.
Integrate words with the relevant part of the diagram and introduce one change
at a time.

### Do not overfit to immediate performance

Fluent repetition can look like mastery. Use delayed retrieval, mixed practice,
explanation, and transfer before calling a concept secure.

## Learning-science evidence

The following sources inform the workflow. Apply findings within their studied
scope and avoid presenting effect sizes as universal guarantees.

- **Active learning in STEM:** Freeman et al. found improved performance and
  lower failure rates across many undergraduate STEM studies. This supports
  learner action, but not every activity design.
  https://doi.org/10.1073/pnas.1319030111
- **Retrieval practice:** Roediger and Karpicke showed that retrieving learned
  material can improve delayed retention relative to repeated study.
  https://doi.org/10.1111/j.1467-9280.2006.01693.x
- **Pretesting and generation:** Unsuccessful retrieval attempts can improve
  later learning when followed by the correct information.
  https://doi.org/10.1037/a0015729
- **Productive failure:** Kapur studied problem solving before instruction as a
  route to stronger conceptual preparation and consolidation under designed
  conditions.
  https://doi.org/10.1080/07370000802212669
- **Worked examples and cognitive load:** Sweller and Cooper found benefits from
  worked examples during early algebra learning, supporting explicit guidance
  for novices and later fading.
  https://doi.org/10.1207/s1532690xci0201_3
- **Self-explanation:** Chi et al. linked effective example study with learners'
  explanations of steps and principles.
  https://doi.org/10.1207/s15516709cog1302_1
- **Interleaved mathematics practice:** Rohrer and Taylor found benefits from
  mixing problem types rather than practicing only blocked sets.
  https://doi.org/10.1002/acp.1346
- **Distributed practice:** Cepeda et al. reviewed evidence that spacing study
  events benefits long-term retention, with timing dependent on the retention
  goal.
  https://doi.org/10.1037/0033-2909.132.3.354
- **Feedback:** Hattie and Timperley synthesized how feedback can address goals,
  current progress, and next actions; the level and form of feedback matter.
  https://doi.org/10.3102/003465430298487
- **Intelligent tutoring systems:** Kulik and Fletcher's meta-analysis supports
  the potential of adaptive tutoring while also showing variation by system and
  outcome measure.
  https://doi.org/10.3102/0034654315581420

## Brilliant public sources

- Mission and learning method: https://brilliant.org/about/
- Tutor behavior: https://brilliant.org/help/features/how-does-koji-work/
- Guided learning paths: https://brilliant.org/help/features/what-are-learning-paths/
- Interactive learning-game design:
  https://blog.brilliant.org/hand-crafted-machine-made/
- Correctness checks for generated problems:
  https://blog.brilliant.org/when-almost-right-is-catastrophically-wrong-evals-for-ai-learning-games/
- Multiple representations in algebra:
  https://blog.brilliant.org/visual-algebra/
- Decomposition and verifiable subproblems:
  https://blog.brilliant.org/decomposition-and-abstraction/
- Tutor philosophy and fading support:
  https://blog.brilliant.org/a-world-class-tutor-in-every-home/
