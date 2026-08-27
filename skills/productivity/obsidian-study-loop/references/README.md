# Study Loop References

Load only the reference needed for the current action. The active study workflow
and mastery rules remain authoritative in `STUDY-PROTOCOL.md` and this skill.

| File | Authority | Load when |
|---|---|---|
| `study-protocol-template.md` | Vault protocol installed and synced by the bundled scripts | Installing or syncing a vault |
| `visual-review-standard.md` | Markdown/Mermaid visual-review contract for `_study/visuals/` | Creating or validating an explicit Markdown visual review |
| `manpage.md` | Learner-facing explanation and quick reference | The user asks how the loop works |

There are two visual lanes. This workflow owns explicit, current-scope Markdown
and Mermaid reviews at `_study/visuals/<YYYY-MM-DD>-<scope-slug>.md`. The
automatic chapter endpoint delegates HTML to `visualize-study-chapter`, which
owns its separate `<vault>/Visuals/` output. Never mix those contracts.

The HTML assembler and browser-quiz fixtures that once lived here are removed.
Never generate a new `.html` artifact. Existing `.html` artifacts in a vault
remain readable and are still checked by `validate_study_vault.py` under the
legacy contract in `visual-review-standard.md`.
