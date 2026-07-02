# Licensing & Attribution

This repository uses a **mixed-licensing model**.

## Original work — MIT © 2026 Sharquille Andrew

The root [LICENSE](LICENSE) (MIT) covers all original content:

- **Self-authored skills:** `agent-orchestra`, `agent-repo-security`,
  `build-security-policy`, `deploy-agent-skills`, `enhance-skill`, `name-skill`,
  `powershell-enterprise-app`, `vet-skill`.
- **Curation & tooling:** `REGISTRY.md`, `install.sh`, `scripts/`,
  `skills/_template/`, and the repository structure.
- **Enhancements & adaptations** made to imported skills (the *changes*, not the
  underlying third-party work).

## Third-party skills — original authors' licenses

Imported skills keep their own `LICENSE` file in their directory and remain under
their original author's copyright. Each skill's `SKILL.md` frontmatter records:

- `source:` — where it came from
- `author:` — the original author (retained as required by MIT/Apache)
- `license:` — the upstream license
- `modified-by:` — present when this repository has changed the skill; the change
  is the only part covered by the root MIT license. The original author's rights
  are unchanged.

Enhancing a third-party skill does **not** transfer its ownership. Such skills
are derivative works: original author's content + this repository's modifications,
each credited separately.

`agent-orchestra` references OpenAI's `openai/codex-plugin-cc` behavior and
installation flow, but does not vendor the plugin source. The upstream plugin
retains its Apache-2.0 license.

## If you reuse a skill from here

Check that skill's `SKILL.md` frontmatter and directory `LICENSE` for its terms,
and preserve the original copyright notice.
