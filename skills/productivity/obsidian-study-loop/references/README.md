# Study Loop References

Load only the reference needed for the current action. The active study workflow
and mastery rules remain authoritative in `STUDY-PROTOCOL.md` and this skill.

| File | Authority | Load when |
|---|---|---|
| `study-protocol-template.md` | Vault protocol installed and synced by the bundled scripts | Installing or syncing a vault |
| `visual-review-standard.md` | Markdown/Mermaid visual-review contract for `_study/visuals/` | Creating or validating an explicit Markdown visual review |
| `manpage.md` | Learner-facing explanation and quick reference | The user asks how the loop works |
| `tactile-study-surface/` | Legacy HTML compatibility fixtures and assembler | Repairing an existing legacy HTML artifact only |
| `legacy-browser-quiz-template.html` | Legacy browser-quiz reference | Inspecting an old generated artifact only |

There are two visual lanes. This workflow owns explicit, current-scope Markdown
and Mermaid reviews at `_study/visuals/<YYYY-MM-DD>-<scope-slug>.md`. The
automatic chapter endpoint delegates HTML to `visualize-study-chapter`, which
owns its separate `<vault>/Visuals/` output. Never mix those contracts, and do
not load the legacy files for normal study, quiz, review, or note actions.
