---
name: course-baseline
description: "Create, rebuild, audit, and release rigorous course websites and learning platforms with authentic project work, real or faithful tool integration, machine-checked competency, focused workspaces, polished paper-and-console UI, regression tests, and deployment evidence. Use when a user asks to turn a course vision, syllabus, job description, training plan, or existing slide-like course into a static site or interactive application; requests a Brilliant-style, lab-driven, terminal-based, or portfolio-producing course; wants this LexLabs-inspired look and flow; or asks to test, audit, deploy, and safely push a course platform. Do not use for a conversational tutoring session, a marketing-only landing page, or a non-learning website that has no curriculum or assessment behavior."
---

# Course Baseline

Build a course as a working learning environment, not a decorated syllabus. Make
the learner perform the target work, receive specific evidence, and leave with
artifacts another person can inspect or run.

## Load only what the task needs

- Read [pedagogy-and-flow.md](references/pedagogy-and-flow.md) before designing
  curriculum, modules, exercises, feedback, competency, or solution release.
- Read [ui-and-interaction.md](references/ui-and-interaction.md) before creating
  or revising screens, tokens, responsive layouts, focus mode, or terminal/tool
  surfaces.
- Read [verification-and-delivery.md](references/verification-and-delivery.md)
  before writing the test plan, auditing a draft, deploying, or changing Git.
- Copy [COURSE_CONTRACT.template.md](assets/COURSE_CONTRACT.template.md) into the
  target project as `COURSE_CONTRACT.md` for a substantial build. Complete it
  from evidence; do not retain placeholder text.
- Run `scripts/audit_course.py <project-root>` for structural feedback and
  `scripts/audit_course.py <project-root> --release` after the production build.
  Treat its result as one gate, not as proof that the course teaches well.

## Preserve authority

- Treat the user's learner, outcomes, subject, tone, visual references, time
  budget, and delivery constraints as authoritative.
- Study an existing course before changing it. Preserve working behavior and
  user-owned files unless the request clearly replaces them.
- Use existing project conventions when sound. Introduce a new framework only
  when the required execution, persistence, routing, or testing cannot fit the
  current architecture cleanly.
- Pair with domain-specific teaching or engineering skills when useful. This
  skill owns the integrated course contract, experience, validation, and release.

## 1. Discover the real course

Inspect the source material, repository, learner profile, target role or task,
available assets, runtime constraints, and current failure modes. Identify:

- one primary learner and what they can already do;
- observable end-state performance, not topic coverage alone;
- weekly time and total duration;
- in-scope and explicitly out-of-scope subjects;
- one authentic story, system, dataset, toolchain, or project spine;
- the artifacts that prove competence outside the course;
- which work must execute for real, may use a faithful simulator, or must happen
  in an external field module;
- the deployment target and offline/account/backend constraints.

Ask only for information that cannot be inferred safely. Do not pause an
otherwise actionable build for cosmetic preferences.

## 2. Freeze the course contract

Complete `COURSE_CONTRACT.md` before broad implementation. Commit to one default
tool per concept; compare alternatives briefly only where workplace literacy
requires it. Derive modules from outcomes, then sequence them as:

`Foundation -> Core competency -> Applied practice -> Extension or capstone`

Every required module must define:

- a surgical prerequisite gate;
- an authentic business or operational brief;
- a five-move learning path: understand, reason, guided practice, independent
  solution, operate;
- a machine-verifiable exit task;
- a shippable artifact;
- a runbook or handoff requirement when the work has operational consequences.

If a module looks optional, cut it or make its dependency explicit. Avoid
scope-creep samplers that do not improve the target performance.

## 3. Choose the smallest credible platform

Use a static HTML/CSS/JavaScript course when content, interaction, and checks can
remain small and maintainable. Use an application framework when the experience
needs multiple workspaces, content authoring, persistent attempt history, large
execution engines, offline caching, or shared state. Prefer the repository's
existing stack; for a new rich local-first build, a practical default is:

- Vite, React, and strict TypeScript;
- content in MDX, Markdown, or typed data outside component markup;
- accessible primitives and a restrained token system;
- CodeMirror for code work;
- IndexedDB for local progress and attempts;
- proven browser runtimes or domain libraries for execution;
- unit tests plus Playwright for desktop and mobile behavior.

Do not install heavyweight infrastructure merely to imitate a tool. Choose one
of these execution levels and label it honestly:

1. **Real local runtime:** preferred when a safe browser or local engine exists.
2. **Browser-isolated simulator:** model command, arguments, path/state, side
   effects, errors, and persistence; never accept a command by string decoration.
3. **Field module:** use the actual external tool with an evidence upload or
   checklist when local execution would be misleading.

Build one complete vertical slice before scaling: source content -> task ->
execution -> grading -> persistence -> responsive UI -> regression test.

## 4. Make assessment the product

Use the same grading semantics everywhere:

- **Pass:** all behavioral and quality checks pass.
- **Runs, wrong:** execution succeeds but expected output differs; show the diff
  or failed invariant without exposing the answer.
- **Error:** show the useful raw tool/runtime error and preserve context.
- **Rejected:** the output may work, but it violates a named maintainability,
  safety, or domain rule.

Check correctness, robustness, readability, and documentation. Correct-only work
does not establish operational competence. Test every supplied solution against
its own checks. Make invalid input, empty/null cases, state transitions, pasted
Unicode, repeated attempts, refresh, and recovery part of regression coverage.

Use progressive hints. Name the mistaken tool or argument class first, narrow
the next move second, and reveal exact syntax only after repeated honest attempts
or an explicit request. Reveal a model solution after a pass or the configured
attempt threshold, then require comparison rather than passive copying.

## 5. Build the course, not a landing page

The first screen must be the usable course console or map. Keep orientation and
progress separate from concentrated work:

- course console/map for dependencies, status, and the next action;
- module document for explanation and sequencing;
- workbench for the brief, editor/tool, results, and attempt history;
- data/tool explorer where inspection is part of the skill;
- portfolio for accumulated evidence;
- runbook for exact operations, success signals, recovery, and escalation.

In the workbench, make the task surface dominant. Keep the brief collapsible,
put notes/runbooks on their own surface, provide focus mode, and avoid persistent
sidebars that consume learning space. A visible terminal must behave like a
terminal or be clearly labeled as a browser-isolated training environment.

Use the LexLabs visual baseline from `ui-and-interaction.md` as a starting point,
then adapt the identity to the subject. Preserve the paper/console contrast,
quiet borders, compact geometry, readable typography, semantic status colors,
and restrained motion. Do not reproduce a generic blue dashboard or a grid of
decorative cards.

## 6. Build in evidence gates

Work in this order:

1. **Source/data first:** create the authentic inputs, planted edge cases, task
   definitions, and defect manifest.
2. **Engine first:** prove one representative task and one high-risk runtime or
   simulator path end to end.
3. **Persistence:** attempts, progression, artifacts, and reload behavior.
4. **Course structure:** map, prerequisites, stale/failed states, and next action.
5. **Design system:** tokens and responsive layouts after the interactions work.
6. **Pilot content:** finish a small foundation slice and use it before authoring
   the entire curriculum.
7. **Expansion:** add the remaining modules based on observed confusion.
8. **Release:** production build, preview, deployment audit, public verification,
   and safe Git delivery.

At every gate, run focused checks first and broader checks at the barrier. Never
replace verification with a screenshot, self-attested completion, or an agent's
claim that code looks correct.

## 7. Audit the draft and release

Follow `verification-and-delivery.md`. At minimum, verify:

- every authored solution passes its own checks;
- wrong, error, rejected, hint, and recovery paths behave as designed;
- progress, attempts, artifacts, and runbooks survive refresh;
- primary journeys work at desktop and mobile viewports with no overlap;
- keyboard navigation, focus, contrast, and reduced motion are credible;
- real runtimes and faithful simulations execute in the production build;
- the browser console has no unexplained errors;
- deployment documentation matches the actual build and host requirements;
- the public URL serves deep links, assets, workers, and WebAssembly correctly.

Before Git delivery, inspect status and remotes, preserve unrelated changes,
scan staged content for secrets, stage an explicit allowlist, review the staged
diff, commit once gates pass, and push normally. Never force-push unless the user
explicitly requests it and the consequences have been reviewed. Push `main`
only when the user explicitly asks for `main`, then verify the remote SHA.

## Required closeout

Report what was built, which learner outcomes are implemented, which execution
level each tool uses, exact verification results, the local/public URL, the
commit and branch when pushed, and any remaining content or runtime gaps. Say
plainly when a check, deployment, or device matrix was not run.
