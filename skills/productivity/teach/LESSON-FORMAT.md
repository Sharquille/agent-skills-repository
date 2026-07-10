# Lesson Format

Lessons in `./lessons/*.html` are the primary unit of teaching in this workspace. Each lesson is one self-contained HTML file, titled `0001-<dash-case-name>.html`, that teaches one tightly-scoped thing tied to the mission.

## Structure

```text
0001-<dash-case-name>.html
├─ Title, plus one line tying the lesson back to MISSION.md
├─ Knowledge — only what this lesson's skill requires, with citations
│  to entries in RESOURCES.md
├─ Practice — an interactive feedback loop: quiz widget, light
│  in-browser task, or a list of real-world steps to take
├─ Primary source — the single most high-trust resource to read or
│  watch on this topic
├─ Links — HTML anchors to related lessons and ./reference/ documents
└─ Footer — a reminder to ask the agent followup questions
```

## Rules

- **One tightly-scoped thing.** Completable very quickly, giving a single tangible win inside the user's zone of proximal development.
- **Local dependencies only.** Link the shared stylesheet and components from `./assets/`; never load external CDN scripts, stylesheets, fonts, or any other network resource.
- **Numbered, never overwritten.** Scan `./lessons/` for the highest existing number and increment. Never overwrite an existing lesson without the user's explicit confirmation.
- **Cited.** Back every claim with a link to a resource tracked in `RESOURCES.md`.
- **Beautiful.** Clean, readable typography and layout that prints well. Think Tufte.
- **No formatting clues in quizzes.** Each answer has exactly the same number of words (and characters, if possible).
