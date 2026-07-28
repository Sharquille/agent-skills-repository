# Study Loop References

`study-protocol-template.md` is the canonical install/sync template.

`visual-review-standard.md` defines the active Markdown and Mermaid contract,
traceability rules, deterministic checks, and Obsidian QA gate for
`_study/visuals/` artifacts.

`tactile-study-surface/` and its JSON assembler are retained only for legacy
HTML compatibility. They are no longer part of the active generation workflow.

`legacy-browser-quiz-template.html` is retained only to make old generated
browser-quiz artifacts understandable. It is not part of the active workflow.
New visual output must be local, current-scope Markdown with Mermaid and written
to `_study/visuals/<YYYY-MM-DD>-<scope-slug>.md` in the target vault. Do not
generate new HTML visual artifacts.
