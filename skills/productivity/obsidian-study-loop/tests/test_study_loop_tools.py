from __future__ import annotations

import importlib.util
import json
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SYNC_PATH = SKILL_DIR / "scripts" / "sync_study_protocol.py"
VALIDATOR_PATH = SKILL_DIR / "scripts" / "validate_study_vault.py"
SKILL_PATH = SKILL_DIR / "SKILL.md"
TEMPLATE_PATH = SKILL_DIR / "references" / "study-protocol-template.md"
TEACH_SKILL_PATH = SKILL_DIR.parent / "teach-complex-concepts" / "SKILL.md"


def load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sync = load_script("obsidian_study_loop_sync", SYNC_PATH)
validator = load_script("obsidian_study_loop_validator", VALIDATOR_PATH)


class VaultFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.vault = Path(self.temporary.name) / "Vault"
        (self.vault / ".obsidian").mkdir(parents=True)
        (self.vault / "_study" / "sessions").mkdir(parents=True)
        (self.vault / "_study" / "visuals").mkdir(parents=True)
        (self.vault / "Notes").mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_state(self, active: str | None, **extra: object) -> None:
        state = {"active_session": active, **extra}
        (self.vault / "_study" / "state.json").write_text(
            json.dumps(state), encoding="utf-8"
        )

    def write_protocol(self) -> None:
        (self.vault / "STUDY-PROTOCOL.md").write_text(
            f"# Study Protocol\n\n- `NOTES_DIR`: `{self.vault / 'Notes'}`\n",
            encoding="utf-8",
        )

    def write_valid_session(self, name: str = "2026-07-09-topic.md") -> Path:
        session = self.vault / "_study" / "sessions" / name
        session.write_text(
            """---
topic: Topic
created: 2026-07-09T12:00:00-0400
status: reviewed
objectives:
  - 1.1 Topic
---

## Study content

Content.

## Unit progress

| Scope | Quiz | Notes | Review |
|---|---|---|---|
| 1.1 | quizzed | notes-written | reviewed |

## Quiz progress — 1.1

- Planned: Topic
- Consumed by Assessment — 1.1 on 2026-07-09T12:10:00-0400

## Assessment — 1.1

- Topic: solid (8)

## Notes written — 1.1

- 2026-07-09T12:20:00-0400 - Wrote `Notes/Topic.md`.

## Review — 2026-07-09

- Topic: APPROVED — no changes.

## Mastery evidence

| Date | Scope | Objective | Evidence | Score | Mastery | Confidence | Notes |
|---|---|---|---|---:|---|---|---|

## Session log

- 2026-07-09T12:30:00-0400 - Review completed. Status: reviewed.
""",
            encoding="utf-8",
        )
        return session

    def write_valid_note(self, name: str = "Topic.md", check_id: str = "1.1-fit") -> Path:
        note = self.vault / "Notes" / name
        note.write_text(
            f"""---
title: Topic
type: learning
status: reviewed
---

## Topic

<!-- study-check:start id={check_id} type=scenario-response scope=1.1 objective=topic -->
### Mastery check: Fit

<!-- learner-answer:response -->
- **Response:** A defensible answer.

> [!TIP]
> **Review — 2026-07-09 · Score 8/8 (solid)**
> **What worked:** Correct.

<!-- study-check:end id={check_id} -->
""",
            encoding="utf-8",
        )
        return note

    def write_valid_visual(self, name: str = "2026-07-09-1.1-topic.html") -> Path:
        artifact = self.vault / "_study" / "visuals" / name
        artifact.write_text(
            """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'none'; img-src data:; font-src 'none'; connect-src 'none'; form-action 'none'; base-uri 'none'">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="referrer" content="no-referrer">
  <meta name="study-source" content="Notes/Topic.md">
  <meta name="study-scope" content="1.1 Topic">
  <meta name="study-generated" content="2026-07-09T12:30:00-0400">
  <meta name="study-visual-version" content="1">
  <title>1.1 Topic visual review</title>
  <style>
    a:focus-visible { outline: 3px solid currentColor; }
    .flow { transition: transform 120ms ease; }
    @media (prefers-reduced-motion: reduce) {
      .flow { transition: none; }
    }
  </style>
</head>
<body>
  <header><p>Visual review artifact - not an assessment</p></header>
  <main id="main">
    <h1>1.1 Topic</h1>
    <a href="#flow">Jump to flow</a>
    <svg id="flow" class="flow" aria-label="Topic relationship flow"></svg>
  </main>
</body>
</html>
""",
            encoding="utf-8",
        )
        return artifact

    def write_valid_markdown_visual(
        self, name: str = "2026-07-09-1.1-topic.md"
    ) -> Path:
        artifact = self.vault / "_study" / "visuals" / name
        artifact.write_text(
            """---
study-source: Notes/Topic.md
study-scope: 1.1 Topic
study-generated: 2026-07-09T12:30:00-0400
study-visual-version: 2
---

Visual review artifact - not an assessment

# 1.1 Topic

## Relationship

```mermaid
flowchart TD
    A["Sender"] --> B["Recipient"]
```

## Retrieval prompt

> [!QUESTION]- Which side receives the message?
> The recipient.
""",
            encoding="utf-8",
        )
        return artifact


class SyncTests(VaultFixture):
    def test_uninstalled_obsidian_vault_does_not_overwrite_unrelated_manual(self) -> None:
        manual = self.vault / "STUDY-MANUAL.md"
        manual.write_text("unrelated personal manual\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SYNC_PATH), str(self.vault), "--apply", "--no-diff"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("uninstalled or partial", result.stderr)
        self.assertEqual(manual.read_text(encoding="utf-8"), "unrelated personal manual\n")
        self.assertFalse((self.vault / "STUDY-PROTOCOL.md").exists())

    def test_directory_state_blocks_sync_before_any_document_change(self) -> None:
        self.write_protocol()
        state = self.vault / "_study" / "state.json"
        state.mkdir()
        manual = self.vault / "STUDY-MANUAL.md"
        manual.write_text("keep manual\n", encoding="utf-8")
        protocol_before = (self.vault / "STUDY-PROTOCOL.md").read_text(encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SYNC_PATH), str(self.vault), "--apply", "--no-diff"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("not a regular file", result.stderr)
        self.assertEqual(manual.read_text(encoding="utf-8"), "keep manual\n")
        self.assertEqual(
            (self.vault / "STUDY-PROTOCOL.md").read_text(encoding="utf-8"),
            protocol_before,
        )

    def test_relative_notes_dir_resolves_from_vault(self) -> None:
        resolved = sync.resolve_notes_dir(Path("Notes"), self.vault.resolve())
        self.assertEqual(resolved, (self.vault / "Notes").resolve())

    def test_cli_relative_notes_dir_is_independent_of_cwd(self) -> None:
        self.write_state(None)
        self.write_protocol()
        result = subprocess.run(
            [
                sys.executable,
                str(SYNC_PATH),
                str(self.vault),
                "--notes-dir",
                "Notes",
                "--apply",
                "--no-diff",
            ],
            cwd=Path(self.temporary.name),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        protocol = (self.vault / "STUDY-PROTOCOL.md").read_text(encoding="utf-8")
        expected_notes = self.vault.resolve() / "Notes"
        self.assertIn(f"- `NOTES_DIR`: `{expected_notes}`", protocol)
        manual = (self.vault / "STUDY-MANUAL.md").read_text(encoding="utf-8")
        self.assertTrue(manual.startswith(sync.MANUAL_BANNER))

    def test_apply_refreshes_stale_manual_when_protocol_is_current(self) -> None:
        self.write_state(None)
        self.write_protocol()
        first = subprocess.run(
            [
                sys.executable,
                str(SYNC_PATH),
                str(self.vault),
                "--notes-dir",
                "Notes",
                "--apply",
                "--no-diff",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        manual = self.vault / "STUDY-MANUAL.md"
        manual.write_text("stale manual\n", encoding="utf-8")
        dry = subprocess.run(
            [sys.executable, str(SYNC_PATH), str(self.vault), "--no-diff"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(dry.returncode, 2, dry.stderr)
        applied = subprocess.run(
            [sys.executable, str(SYNC_PATH), str(self.vault), "--apply", "--no-diff"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertTrue(manual.read_text(encoding="utf-8").startswith(sync.MANUAL_BANNER))

    def test_symlinked_protocol_target_is_rejected(self) -> None:
        victim = Path(self.temporary.name) / "victim.md"
        victim.write_text("keep", encoding="utf-8")
        target = self.vault / "STUDY-PROTOCOL.md"
        target.symlink_to(victim)
        with self.assertRaises(sync.SyncError):
            sync.ensure_safe_target(target, self.vault.resolve())
        self.assertEqual(victim.read_text(encoding="utf-8"), "keep")

    def test_in_vault_symlinked_state_file_is_rejected(self) -> None:
        self.write_protocol()
        state_target = self.vault / "state-target.json"
        state_target.write_text('{"active_session": null}\n', encoding="utf-8")
        state = self.vault / "_study" / "state.json"
        state.symlink_to(state_target)
        with self.assertRaises(sync.SyncError):
            sync.resolve_vault(str(self.vault))
        self.assertEqual(state_target.read_text(encoding="utf-8"), '{"active_session": null}\n')

    def test_atomic_write_replaces_content_and_preserves_mode(self) -> None:
        target = self.vault / "STUDY-PROTOCOL.md"
        target.write_text("old", encoding="utf-8")
        target.chmod(0o640)
        sync.atomic_write_text(target, "new\n")
        self.assertEqual(target.read_text(encoding="utf-8"), "new\n")
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o640)
        self.assertEqual(list(self.vault.glob(".STUDY-PROTOCOL.md.*.tmp")), [])

    def test_state_warning_rejects_extra_keys(self) -> None:
        self.write_state(None, unexpected=True)
        warnings = sync.state_warnings(self.vault.resolve())
        self.assertEqual(len(warnings), 1)
        self.assertIn("exactly the active_session key", warnings[0])

    def test_state_warning_rejects_session_symlink_escape(self) -> None:
        outside = Path(self.temporary.name) / "outside.md"
        outside.write_text("outside", encoding="utf-8")
        session = self.vault / "_study" / "sessions" / "linked.md"
        session.symlink_to(outside)
        self.write_state("_study/sessions/linked.md")
        warnings = sync.state_warnings(self.vault.resolve())
        self.assertEqual(len(warnings), 1)
        self.assertIn("resolves outside", warnings[0])

    def test_removed_external_template_flag_is_rejected(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SYNC_PATH), str(self.vault), "--template", "x"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_invalid_utf8_protocol_fails_without_traceback(self) -> None:
        self.write_state(None)
        (self.vault / "STUDY-PROTOCOL.md").write_bytes(b"\xff\xfe")
        result = subprocess.run(
            [sys.executable, str(SYNC_PATH), str(self.vault), "--no-diff"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("ERROR:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


class ValidatorTests(VaultFixture):
    def make_valid_vault(self) -> None:
        self.write_protocol()
        session = self.write_valid_session()
        self.write_valid_note()
        self.write_state(str(session.relative_to(self.vault)))

    def errors(self) -> list[object]:
        return [
            issue
            for issue in validator.validate_vault(self.vault.resolve(), self.vault / "Notes")
            if issue.severity == "ERROR"
        ]

    def replace_quiz_and_assessment(
        self, quiz_blocks: str, assessment_blocks: str
    ) -> Path:
        session = self.vault / "_study" / "sessions" / "2026-07-09-topic.md"
        text = session.read_text(encoding="utf-8")
        quiz_start = text.index("## Quiz progress — 1.1")
        assessment_start = text.index("## Assessment — 1.1")
        notes_start = text.index("## Notes written — 1.1")
        session.write_text(
            text[:quiz_start]
            + quiz_blocks.rstrip()
            + "\n\n"
            + assessment_blocks.rstrip()
            + "\n\n"
            + text[notes_start:],
            encoding="utf-8",
        )
        return session

    def test_valid_vault_has_no_findings(self) -> None:
        self.make_valid_vault()
        issues = validator.validate_vault(self.vault.resolve(), self.vault / "Notes")
        self.assertEqual(issues, [])

    def test_valid_visual_artifact_has_no_findings(self) -> None:
        self.make_valid_vault()
        self.write_valid_visual()
        issues = validator.validate_vault(self.vault.resolve(), self.vault / "Notes")
        self.assertEqual(issues, [])

    def test_valid_markdown_visual_artifact_has_no_findings(self) -> None:
        self.make_valid_vault()
        self.write_valid_markdown_visual()
        issues = validator.validate_vault(self.vault.resolve(), self.vault / "Notes")
        self.assertEqual(issues, [])

    def test_undated_markdown_in_visuals_is_not_an_artifact(self) -> None:
        """A README or index note in `_study/visuals/` is not a generated artifact.

        Regression: dispatching every `.md` in the directory to the artifact
        contract made a pre-existing `_study/visuals/README.md` fail a live vault
        with five errors.
        """
        self.make_valid_vault()
        self.write_valid_markdown_visual()
        readme = self.vault / "_study" / "visuals" / "README.md"
        readme.write_text(
            "# Visual Review Artifacts\n\nCurrent-scope artifacts live here.\n",
            encoding="utf-8",
        )
        issues = validator.validate_vault(self.vault.resolve(), self.vault / "Notes")
        self.assertEqual(issues, [])

    def test_markdown_visual_rejects_unterminated_fence(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_markdown_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8").replace(
                '\n```\n\n## Retrieval prompt',
                "\n\n## Retrieval prompt",
            ),
            encoding="utf-8",
        )
        self.assertIn("unterminated fenced block", [i.message for i in self.errors()])

    def test_markdown_visual_rejects_empty_mermaid_block(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_markdown_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8").replace(
                'flowchart TD\n    A["Sender"] --> B["Recipient"]',
                "",
            ),
            encoding="utf-8",
        )
        self.assertIn("empty mermaid block", [i.message for i in self.errors()])

    def test_markdown_visual_rejects_unknown_mermaid_diagram_type(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_markdown_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8").replace(
                "flowchart TD",
                "networkDiagram TD",
            ),
            encoding="utf-8",
        )
        messages = [i.message for i in self.errors()]
        self.assertTrue(any("unknown Mermaid diagram type" in message for message in messages))
        self.assertTrue(any("flowchart, graph, sequenceDiagram" in message for message in messages))

    def test_markdown_visual_rejects_list_marker_mermaid_label(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_markdown_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8").replace(
                'A["Sender"]',
                'A["1. Sender"]',
            ),
            encoding="utf-8",
        )
        self.assertTrue(
            any(
                "quoted Mermaid label begins with a list marker" in i.message
                for i in self.errors()
            )
        )

    def test_markdown_visual_rejects_nested_fence_boundary(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_markdown_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8").replace(
                "flowchart TD",
                "```mermaid\nflowchart TD",
            ),
            encoding="utf-8",
        )
        self.assertIn(
            "malformed or nested fence boundary",
            [i.message for i in self.errors()],
        )

    def test_markdown_visual_rejects_remote_image(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_markdown_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8").replace(
                "## Relationship",
                "![Remote](https://example.invalid/diagram.png)\n\n## Relationship",
            ),
            encoding="utf-8",
        )
        self.assertTrue(
            any("external Markdown link destination" in i.message for i in self.errors())
        )

    def test_markdown_visual_rejects_remote_link(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_markdown_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8").replace(
                "## Relationship",
                "[Remote reference](https://example.invalid/topic)\n\n## Relationship",
            ),
            encoding="utf-8",
        )
        self.assertTrue(
            any("external Markdown link destination" in i.message for i in self.errors())
        )

    def test_markdown_visual_rejects_external_raw_html_url_attribute(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_markdown_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8").replace(
                "## Relationship",
                '<img src="//cdn.example.invalid/topic.png" alt="Remote">\n\n'
                "## Relationship",
            ),
            encoding="utf-8",
        )
        self.assertTrue(
            any("external raw HTML src destination" in i.message for i in self.errors())
        )

    def test_markdown_visual_rejects_quoted_frontmatter_value(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_markdown_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8").replace(
                "study-scope: 1.1 Topic",
                'study-scope: "1.1 Topic"',
            ),
            encoding="utf-8",
        )
        self.assertIn(
            "study-scope must be a bare one-line scalar",
            [i.message for i in self.errors()],
        )

    def test_markdown_visual_requires_version_two(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_markdown_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8").replace(
                "study-visual-version: 2",
                "study-visual-version: 1",
            ),
            encoding="utf-8",
        )
        self.assertIn(
            "study-visual-version must be 2 for .md artifacts",
            [i.message for i in self.errors()],
        )

    def test_legacy_html_visual_requires_version_one(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8").replace(
                '<meta name="study-visual-version" content="1">',
                '<meta name="study-visual-version" content="2">',
            ),
            encoding="utf-8",
        )
        self.assertIn(
            "study-visual-version must be 1 for .html artifacts",
            [i.message for i in self.errors()],
        )

    def test_markdown_visual_rejects_study_source_resolving_outside_vault(self) -> None:
        self.make_valid_vault()
        outside = Path(self.temporary.name) / "outside-markdown.md"
        outside.write_text("outside", encoding="utf-8")
        (self.vault / "Notes" / "OutsideMarkdown.md").symlink_to(outside)
        artifact = self.write_valid_markdown_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8").replace(
                "Notes/Topic.md",
                "Notes/OutsideMarkdown.md",
            ),
            encoding="utf-8",
        )
        self.assertTrue(
            any("study-source resolves outside vault" in i.message for i in self.errors())
        )

    def test_markdown_visual_requires_existing_study_source(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_markdown_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8").replace(
                "Notes/Topic.md",
                "Notes/Missing.md",
            ),
            encoding="utf-8",
        )
        self.assertTrue(
            any(
                "study-source is not an existing regular file" in i.message
                for i in self.errors()
            )
        )

    def test_markdown_visual_requires_exact_visible_label(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_markdown_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8").replace(
                "Visual review artifact - not an assessment",
                "Visual review",
            ),
            encoding="utf-8",
        )
        self.assertTrue(any("missing visible label" in i.message for i in self.errors()))

    def test_canvas_visual_file_is_ignored(self) -> None:
        self.make_valid_vault()
        (self.vault / "_study" / "visuals" / "manual-map.canvas").write_text(
            '{"nodes": "not validated by this lane"}',
            encoding="utf-8",
        )
        issues = validator.validate_vault(self.vault.resolve(), self.vault / "Notes")
        self.assertEqual(issues, [])

    def test_visual_artifact_rejects_remote_resource(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8").replace(
                '<svg id="flow" class="flow" aria-label="Topic relationship flow"></svg>',
                '<img src="https://example.invalid/diagram.png" alt="Diagram">',
            ),
            encoding="utf-8",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("non-local src reference" in message for message in messages))

    def test_visual_artifact_requires_disclaimer_and_metadata(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8")
            .replace("Visual review artifact - not an assessment", "Study page")
            .replace('<meta name="study-scope" content="1.1 Topic">\n', ""),
            encoding="utf-8",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("missing visible label" in message for message in messages))
        self.assertIn("missing study-scope metadata", messages)

    def test_visual_artifact_requires_existing_local_study_source(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_visual()
        original = artifact.read_text(encoding="utf-8")
        artifact.write_text(
            original.replace('<meta name="study-source" content="Notes/Topic.md">\n', ""),
            encoding="utf-8",
        )
        self.assertIn("missing study-source metadata", [i.message for i in self.errors()])

        artifact.write_text(
            original.replace("Notes/Topic.md", "Notes/Missing.md"), encoding="utf-8"
        )
        self.assertTrue(
            any("study-source is not an existing regular file" in i.message for i in self.errors())
        )

    def test_visual_artifact_rejects_study_source_resolving_outside_vault(self) -> None:
        self.make_valid_vault()
        outside = Path(self.temporary.name) / "outside.md"
        outside.write_text("outside", encoding="utf-8")
        (self.vault / "Notes" / "Outside.md").symlink_to(outside)
        artifact = self.write_valid_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8").replace(
                "Notes/Topic.md", "Notes/Outside.md"
            ),
            encoding="utf-8",
        )
        self.assertTrue(
            any("study-source resolves outside vault" in i.message for i in self.errors())
        )

    def test_visual_artifact_rejects_uri_study_source(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8").replace(
                "Notes/Topic.md", "https://example.invalid/Topic.md"
            ),
            encoding="utf-8",
        )
        self.assertTrue(any("unsafe study-source path" in i.message for i in self.errors()))

    def test_visuals_parent_symlink_outside_vault_is_rejected(self) -> None:
        self.make_valid_vault()
        visuals = self.vault / "_study" / "visuals"
        visuals.rmdir()
        outside = Path(self.temporary.name) / "outside-visuals"
        outside.mkdir()
        visuals.symlink_to(outside, target_is_directory=True)
        messages = [issue.message for issue in self.errors()]
        self.assertIn("visuals root resolves outside the vault", messages)

    def test_broken_visuals_symlink_is_rejected(self) -> None:
        self.make_valid_vault()
        visuals = self.vault / "_study" / "visuals"
        visuals.rmdir()
        visuals.symlink_to(self.vault / "missing-visuals", target_is_directory=True)
        messages = [issue.message for issue in self.errors()]
        self.assertIn("visuals root symlink target does not exist", messages)

    def test_visual_artifact_symlink_outside_visuals_is_rejected(self) -> None:
        self.make_valid_vault()
        outside = Path(self.temporary.name) / "outside.html"
        outside.write_text("<!doctype html><title>outside</title>", encoding="utf-8")
        (self.vault / "_study" / "visuals" / "linked.html").symlink_to(outside)
        messages = [issue.message for issue in self.errors()]
        self.assertIn("visual artifact resolves outside _study/visuals", messages)

    def test_visual_artifact_rejects_persistence_and_forms(self) -> None:
        self.make_valid_vault()
        artifact = self.write_valid_visual()
        artifact.write_text(
            artifact.read_text(encoding="utf-8")
            .replace("script-src 'none'", "script-src 'unsafe-inline'")
            .replace(
                "</main>",
                '<form><input name="answer"></form><script>localStorage.setItem("x", "y")</script></main>',
            ),
            encoding="utf-8",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertIn("forbidden element: form", messages)
        self.assertIn("forbidden element: input", messages)
        self.assertTrue(any("persistent storage API" in message for message in messages))

    def test_state_path_traversal_is_rejected(self) -> None:
        self.write_protocol()
        self.write_state("_study/sessions/../../outside.md")
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("active_session" in message for message in messages))

    def test_state_file_symlink_escape_is_rejected(self) -> None:
        self.write_protocol()
        outside = Path(self.temporary.name) / "outside-state.json"
        outside.write_text('{"active_session": null}', encoding="utf-8")
        (self.vault / "_study" / "state.json").symlink_to(outside)
        messages = [issue.message for issue in self.errors()]
        self.assertIn("state file symlink resolves outside the vault", messages)

    def test_session_heading_order_error(self) -> None:
        self.make_valid_vault()
        session = self.vault / "_study" / "sessions" / "2026-07-09-topic.md"
        text = session.read_text(encoding="utf-8")
        quiz_start = text.index("## Quiz progress — 1.1")
        assessment_start = text.index("## Assessment — 1.1")
        notes_start = text.index("## Notes written — 1.1")
        quiz = text[quiz_start:assessment_start]
        assessment = text[assessment_start:notes_start]
        session.write_text(
            text[:quiz_start] + assessment + quiz + text[notes_start:], encoding="utf-8"
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("canonical group order" in message for message in messages))

    def test_reviewed_note_with_pending_gap_is_rejected(self) -> None:
        self.make_valid_vault()
        note = self.vault / "Notes" / "Topic.md"
        note.write_text(
            """---
title: Topic
type: learning
status: reviewed
---

## Topic

> [!IMPORTANT]
> **RESEARCH NEEDED**

<!-- gap:topic -->
<!-- learner-edit:start id=gap-topic -->
Write here.
<!-- learner-edit:end id=gap-topic -->
""",
            encoding="utf-8",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertIn("reviewed note still contains a pending gap", messages)
        self.assertIn("reviewed note still says RESEARCH NEEDED", messages)

    def test_duplicate_study_check_ids_are_rejected(self) -> None:
        self.make_valid_vault()
        self.write_valid_note("Second.md", "1.1-fit")
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("duplicate study-check id 1.1-fit" in message for message in messages))

    def test_answered_unreviewed_check_warns_while_note_is_draft(self) -> None:
        self.make_valid_vault()
        note = self.vault / "Notes" / "Topic.md"
        text = note.read_text(encoding="utf-8")
        text = text.replace("status: reviewed", "status: draft").replace(
            "> [!TIP]\n> **Review — 2026-07-09 · Score 8/8 (solid)**\n"
            "> **What worked:** Correct.\n",
            "",
        )
        note.write_text(text, encoding="utf-8")
        issues = validator.validate_vault(self.vault.resolve(), self.vault / "Notes")
        self.assertFalse(any(issue.severity == "ERROR" for issue in issues))
        self.assertTrue(
            any(
                issue.severity == "WARN" and "answered study-check" in issue.message
                for issue in issues
            )
        )

    def test_distinct_attempts_for_same_scope_do_not_collide(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: completed — updated: 2026-07-09T12:10:00-0400
- Q1 [recall] — Topic — status: scored — prompt: Define Topic. — score: 2/2 applicable — assistance: none — learner confidence: High — evidence: Correct definition.
- Consumed by Assessment — 1.1 — attempt 2026-07-09-01 on 2026-07-09T12:10:00-0400

## Quiz progress — 1.1 — attempt 2026-07-09-02

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: completed — updated: 2026-07-09T12:15:00-0400
- Q1 [applied] — Topic — status: scored — prompt: Apply Topic. — score: 6/8 — assistance: none — learner confidence: Medium — evidence: Correct fit with a weak limitation.
- Consumed by Assessment — 1.1 — attempt 2026-07-09-02 on 2026-07-09T12:15:00-0400""",
            """## Assessment — 1.1 — attempt 2026-07-09-01

- Topic — mastery: solid (recall-only) — evidence question: Q1 — score: 2/2 applicable — assistance: none — evidence: Correct definition. — tutor confidence: medium — learner confidence: High — calibration: well-calibrated — review stage: 1 — next review: 2026-07-10

## Assessment — 1.1 — attempt 2026-07-09-02

- Topic — mastery: partial — evidence question: Q1 — score: 6/8 — assistance: none — evidence: Correct fit with a weak limitation. — tutor confidence: medium — learner confidence: Medium — calibration: well-calibrated — next action: remediation""",
        )
        issues = validator.validate_vault(self.vault.resolve(), self.vault / "Notes")
        self.assertEqual(issues, [])

    def test_asked_question_is_an_interruption_warning(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: active — updated: 2026-07-09T12:10:00-0400
- Q1 [recall] — Define Topic — status: asked — prompt: Define Topic.""",
            """## Assessment — 1.1

- Topic: solid (8)""",
        )
        issues = validator.validate_vault(self.vault.resolve(), self.vault / "Notes")
        self.assertFalse(any(issue.severity == "ERROR" for issue in issues))
        self.assertTrue(
            any("asked-but-unscored question: Q1" in issue.message for issue in issues)
        )

    def test_malformed_and_duplicate_attempt_ids_are_rejected(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt malformed

- Q1 [recall] — Define Topic — status: planned

## Quiz progress — 1.1 — attempt 2026-07-09-01

- Q1 [recall] — Define Topic — status: planned

## Quiz progress — 1.2 — attempt 2026-07-09-01

- Q1 [recall] — Define Other — status: planned""",
            """## Assessment — 1.1

- Topic: solid (8)""",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertIn("malformed quiz attempt id: malformed", messages)
        self.assertTrue(any("duplicate quiz attempt id 2026-07-09-01" in m for m in messages))

    def test_structured_scored_record_enforces_score_semantics(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Q1 [recall] — Define Topic — status: scored — score: 2/4 — assistance: none — learner confidence: High — evidence: Definition.
- Q2 [applied] — Apply Topic — status: scored — score: 9/8 — assistance: none — learner confidence: Medium — evidence: Application.
- Consumed by Assessment — 1.1 — attempt 2026-07-09-01 on 2026-07-09T12:10:00-0400""",
            """## Assessment — 1.1 — attempt 2026-07-09-01

- Topic: partial""",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("score below /8 must name" in message for message in messages))
        self.assertTrue(any("score is outside its denominator" in message for message in messages))

    def test_malformed_record_and_consumed_attempt_mismatch_are_rejected(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Q1 — Define Topic — status: planned
- Consumed by Assessment — 1.1 — attempt 2026-07-09-02 on 2026-07-09T12:10:00-0400""",
            """## Assessment — 1.1 — attempt 2026-07-09-01

- Topic: partial""",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("malformed question record" in message for message in messages))
        self.assertTrue(
            any("consumed record does not match its attempt" in message for message in messages)
        )

    def test_non_recall_evidence_accepts_applicable_denominator(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: completed — updated: 2026-07-09T12:10:00-0400
- Q1 [classification] — Topic — status: scored — prompt: Classify Topic. — score: 3/4 applicable — assistance: none — learner confidence: High — evidence: Correct class with incomplete reasoning.
- Consumed by Assessment — 1.1 — attempt 2026-07-09-01 on 2026-07-09T12:10:00-0400""",
            """## Assessment — 1.1 — attempt 2026-07-09-01

- Topic — mastery: partial — evidence question: Q1 — score: 3/4 applicable — assistance: none — evidence: Correct class with incomplete reasoning. — tutor confidence: medium — learner confidence: High — calibration: overconfident — next action: targeted reasoning practice""",
        )
        issues = validator.validate_vault(self.vault.resolve(), self.vault / "Notes")
        self.assertEqual(issues, [])

    def test_applicable_denominator_must_match_rubric_dimensions(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: active — updated: 2026-07-09T12:10:00-0400
- Q1 [classification] — Classify Topic — status: scored — prompt: Classify Topic. — score: 2/3 applicable — assistance: none — learner confidence: Medium — evidence: Partial classification.""",
            """## Assessment — 1.1

- Topic: partial""",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("score is outside its denominator" in m for m in messages))

    def test_mixed_assistance_can_select_unassisted_primary_evidence(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 1; target 2; maximum 2; mode adaptive
- Attempt status: completed — updated: 2026-07-09T12:10:00-0400
- Q1 [application] — Topic — status: scored — prompt: First application. — score: 7/8 — assistance: hint-3 — learner confidence: High — evidence: Correct after hints.
- Q2 [application] — Topic — status: scored — prompt: Fresh application. — score: 7/8 — assistance: none — learner confidence: High — evidence: Independent transfer.
- Consumed by Assessment — 1.1 — attempt 2026-07-09-01 on 2026-07-09T12:10:00-0400""",
            """## Assessment — 1.1 — attempt 2026-07-09-01

- Topic — mastery: solid — evidence question: Q2 — score: 7/8 — assistance: none — evidence: Independent transfer. — tutor confidence: medium — learner confidence: High — calibration: well-calibrated — review stage: 1 — next review: 2026-07-10""",
        )
        issues = validator.validate_vault(self.vault.resolve(), self.vault / "Notes")
        self.assertEqual(issues, [])

    def test_assessment_selected_evidence_must_match_quiz_record(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: completed — updated: 2026-07-09T12:10:00-0400
- Q1 [application] — Topic — status: scored — prompt: Apply Topic. — score: 5/8 — assistance: hint-2 — learner confidence: Medium — evidence: Partial application.
- Consumed by Assessment — 1.1 — attempt 2026-07-09-01 on 2026-07-09T12:10:00-0400""",
            """## Assessment — 1.1 — attempt 2026-07-09-01

- Topic — mastery: partial — evidence question: Q1 — score: 4/8 — assistance: none — evidence: Partial application. — tutor confidence: medium — learner confidence: High — calibration: overconfident — next action: remediation""",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("score must match Q1: 5/8" in m for m in messages))
        self.assertTrue(any("assistance must match Q1: hint-2" in m for m in messages))
        self.assertTrue(any("learner confidence must match Q1: Medium" in m for m in messages))

    def test_recall_only_question_kind_cannot_bypass_mastery_label(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: completed — updated: 2026-07-09T12:10:00-0400
- Q1 [free-recall] — Topic — status: scored — prompt: Produce the term. — score: 2/2 applicable — assistance: none — learner confidence: High — evidence: Correct term.
- Consumed by Assessment — 1.1 — attempt 2026-07-09-01 on 2026-07-09T12:10:00-0400""",
            """## Assessment — 1.1 — attempt 2026-07-09-01

- Topic — mastery: solid — evidence question: Q1 — score: 2/2 applicable — assistance: none — evidence: Correct term. — tutor confidence: high — learner confidence: High — calibration: well-calibrated — review stage: 1 — next review: 2026-07-10""",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("solid free-recall evidence must be recall-only" in m for m in messages))

    def test_applied_question_kind_cannot_claim_recall_only_mastery(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: completed — updated: 2026-07-09T12:10:00-0400
- Q1 [classification] — Topic — status: scored — prompt: Classify the case. — score: 4/4 applicable — assistance: none — learner confidence: High — evidence: Correct classification.
- Consumed by Assessment — 1.1 — attempt 2026-07-09-01 on 2026-07-09T12:10:00-0400""",
            """## Assessment — 1.1 — attempt 2026-07-09-01

- Topic — mastery: solid (recall-only) — evidence question: Q1 — score: 4/4 applicable — assistance: none — evidence: Correct classification. — tutor confidence: medium — learner confidence: High — calibration: well-calibrated — review stage: 1 — next review: 2026-07-10""",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("classification evidence cannot be recall-only" in m for m in messages))

    def test_unsupported_question_kind_is_rejected(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: active — updated: 2026-07-09T12:10:00-0400
- Q1 [mystery-kind] — Topic — status: planned""",
            """## Assessment — 1.1

- Topic: solid (8)""",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("unsupported question kind: mystery-kind" in m for m in messages))

    def test_hint_or_reveal_caps_numeric_solid_at_partial(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: completed — updated: 2026-07-09T12:10:00-0400
- Q1 [application] — Topic — status: scored — prompt: Apply Topic. — score: 7/8 — assistance: revealed — learner confidence: High — evidence: Pre-reveal production recorded.
- Consumed by Assessment — 1.1 — attempt 2026-07-09-01 on 2026-07-09T12:10:00-0400""",
            """## Assessment — 1.1 — attempt 2026-07-09-01

- Topic — mastery: solid — evidence question: Q1 — score: 7/8 — assistance: revealed — evidence: Pre-reveal production recorded. — tutor confidence: low — learner confidence: High — calibration: well-calibrated — review stage: 1 — next review: 2026-07-10""",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("mastery solid does not match score 7/8" in m for m in messages))

    def test_assessment_rejects_mastery_and_calibration_mismatch(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: completed — updated: 2026-07-09T12:10:00-0400
- Q1 [application] — Topic — status: scored — prompt: Apply Topic. — score: 7/8 — assistance: none — learner confidence: Low — evidence: Strong application.
- Consumed by Assessment — 1.1 — attempt 2026-07-09-01 on 2026-07-09T12:10:00-0400""",
            """## Assessment — 1.1 — attempt 2026-07-09-01

- Topic — mastery: partial — evidence question: Q1 — score: 7/8 — assistance: none — evidence: Strong application. — tutor confidence: medium — learner confidence: Low — calibration: well-calibrated — next action: remediation""",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("mastery partial does not match score 7/8" in m for m in messages))
        self.assertTrue(any("calibration must be underconfident" in m for m in messages))

    def test_assessment_requires_canonical_fields_and_recall_confidence_cap(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: completed — updated: 2026-07-09T12:10:00-0400
- Q1 [recall] — Define Topic — status: scored — prompt: Define Topic. — score: 2/2 applicable — assistance: none — learner confidence: High — evidence: Correct definition.
- Consumed by Assessment — 1.1 — attempt 2026-07-09-01 on 2026-07-09T12:10:00-0400""",
            """## Assessment — 1.1 — attempt 2026-07-09-01

- Topic — mastery: solid (recall-only) — evidence: Correct definition. — evidence question: Q1 — score: 2/2 applicable — assistance: none — tutor confidence: high — learner confidence: High — calibration: well-calibrated — review stage: 6 — next review: not-a-date""",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("out of order" in message for message in messages))
        self.assertTrue(any("recall-only tutor confidence exceeds medium" in m for m in messages))
        self.assertTrue(any("invalid review stage" in message for message in messages))
        self.assertTrue(any("invalid next review date" in message for message in messages))

    def test_attempt_and_assessment_must_link_one_to_one(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: completed — updated: 2026-07-09T12:10:00-0400
- Q1 [application] — Apply Topic — status: scored — prompt: Apply Topic. — score: 7/8 — assistance: none — learner confidence: High — evidence: Strong application.
- Consumed by Assessment — 1.1 — attempt 2026-07-09-01 on 2026-07-09T12:10:00-0400""",
            """## Assessment — 1.1 — attempt 2026-07-09-02

- Topic — mastery: solid — evidence question: Q1 — score: 7/8 — assistance: none — evidence: Strong application. — tutor confidence: medium — learner confidence: High — calibration: well-calibrated — review stage: 1 — next review: 2026-07-10""",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("must link to exactly one assessment" in m for m in messages))
        self.assertTrue(any("must link to exactly one quiz attempt" in m for m in messages))

    def test_consumed_attempt_must_be_completed(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: active — updated: 2026-07-09T12:10:00-0400
- Q1 [application] — Apply Topic — status: scored — prompt: Apply Topic. — score: 7/8 — assistance: none — learner confidence: High — evidence: Strong application.
- Consumed by Assessment — 1.1 — attempt 2026-07-09-01 on 2026-07-09T12:10:00-0400""",
            """## Assessment — 1.1 — attempt 2026-07-09-01

- Topic — mastery: solid — evidence question: Q1 — score: 7/8 — assistance: none — evidence: Strong application. — tutor confidence: medium — learner confidence: High — calibration: well-calibrated — review stage: 1 — next review: 2026-07-10""",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("active attempt must remain unconsumed" in m for m in messages))

    def test_stray_consumed_prose_does_not_consume_attempt(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: paused — updated: 2026-07-09T12:10:00-0400
- Q1 [recall] — Define Topic — status: asked — prompt: Define Topic.

Prose mentioning Consumed by Assessment — 1.1 — attempt 2026-07-09-01 is not a record.""",
            """## Assessment — 1.1

- Topic: solid (8)""",
        )
        issues = validator.validate_vault(self.vault.resolve(), self.vault / "Notes")
        self.assertFalse(any(issue.severity == "ERROR" for issue in issues))
        self.assertTrue(any("unconsumed Quiz progress" in issue.message for issue in issues))

    def test_scored_record_requires_preserved_prompt(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: active — updated: 2026-07-09T12:10:00-0400
- Q1 [recall] — Define Topic — status: scored — score: 2/2 applicable — assistance: none — learner confidence: High — evidence: Correct definition.""",
            """## Assessment — 1.1

- Topic: solid (8)""",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("status scored is missing: prompt" in m for m in messages))

    def test_budget_order_and_question_maximum_are_enforced(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 2; target 1; maximum 1; mode adaptive
- Attempt status: active — updated: 2026-07-09T12:10:00-0400
- Q1 [recall] — Define Topic — status: planned
- Q2 [application] — Apply Topic — status: planned""",
            """## Assessment — 1.1

- Topic: solid (8)""",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("Budget must satisfy" in message for message in messages))
        self.assertTrue(any("more question IDs than its maximum Budget" in m for m in messages))

    def test_question_count_must_reach_budget_minimum(self) -> None:
        self.make_valid_vault()
        self.replace_quiz_and_assessment(
            """## Quiz progress — 1.1 — attempt 2026-07-09-01

- Budget: minimum 2; target 2; maximum 3; mode adaptive
- Attempt status: active — updated: 2026-07-09T12:10:00-0400
- Q1 [recall] — Topic — status: planned""",
            """## Assessment — 1.1

- Topic: solid (8)""",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("fewer question IDs than its minimum Budget" in m for m in messages))

    def test_active_session_must_be_regular_file(self) -> None:
        self.write_protocol()
        session_dir = self.vault / "_study" / "sessions" / "directory.md"
        session_dir.mkdir()
        self.write_state("_study/sessions/directory.md")
        messages = [issue.message for issue in self.errors()]
        self.assertIn(
            "active session is not a regular file: _study/sessions/directory.md",
            messages,
        )

    def test_reviewed_answered_gap_accepts_structured_source(self) -> None:
        self.make_valid_vault()
        note = self.vault / "Notes" / "Topic.md"
        note.write_text(
            """---
title: Topic
type: learning
status: reviewed
---

## Topic

<!-- gap:topic -->
<!-- learner-edit:start id=gap-topic -->
<!-- learner-answer:gap-response -->
Topic is a defined concept.
<!-- learner-source:gap-topic -->
- **Source:** Course module 1.1
<!-- learner-edit:end id=gap-topic -->
""",
            encoding="utf-8",
        )
        issues = validator.validate_vault(self.vault.resolve(), self.vault / "Notes")
        self.assertEqual(issues, [])

    def test_reviewed_answered_gap_warns_for_missing_or_empty_source(self) -> None:
        self.make_valid_vault()
        note = self.vault / "Notes" / "Topic.md"
        note.write_text(
            """---
title: Topic
type: learning
status: reviewed
---

## Missing source

<!-- gap:missing -->
<!-- learner-edit:start id=gap-missing -->
<!-- learner-answer:gap-response -->
An answered gap.
<!-- learner-edit:end id=gap-missing -->

## Empty source

<!-- gap:empty -->
<!-- learner-edit:start id=gap-empty -->
<!-- learner-answer:gap-response -->
Another answered gap.
<!-- learner-source:gap-empty -->
- **Source:** Write here.
<!-- learner-edit:end id=gap-empty -->
""",
            encoding="utf-8",
        )
        issues = validator.validate_vault(self.vault.resolve(), self.vault / "Notes")
        self.assertFalse(any(issue.severity == "ERROR" for issue in issues))
        messages = [issue.message for issue in issues]
        self.assertTrue(any("missing learner source marker: gap-missing" in m for m in messages))
        self.assertTrue(any("no learner source value: gap-empty" in m for m in messages))

    def test_reviewed_gap_with_source_but_no_response_is_pending(self) -> None:
        self.make_valid_vault()
        note = self.vault / "Notes" / "Topic.md"
        note.write_text(
            """---
title: Topic
type: learning
status: reviewed
---

## Topic

<!-- gap:topic -->
<!-- learner-edit:start id=gap-topic -->
<!-- learner-answer:gap-response -->
Write here.
<!-- learner-source:gap-topic -->
- **Source:** Write here.
<!-- learner-edit:end id=gap-topic -->
""",
            encoding="utf-8",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertIn("reviewed note still contains a pending gap", messages)

    def test_draft_gap_without_source_still_warns(self) -> None:
        self.make_valid_vault()
        note = self.vault / "Notes" / "Topic.md"
        note.write_text(
            """---
title: Topic
type: learning
status: draft
---

## Topic

<!-- gap:topic -->
<!-- learner-edit:start id=gap-topic -->
Write here.
<!-- learner-edit:end id=gap-topic -->
""",
            encoding="utf-8",
        )
        issues = validator.validate_vault(self.vault.resolve(), self.vault / "Notes")
        self.assertFalse(any(issue.severity == "ERROR" for issue in issues))
        self.assertTrue(any("gap is missing learner source marker" in i.message for i in issues))

    def test_gap_rejects_duplicate_mismatched_and_orphan_sources(self) -> None:
        self.make_valid_vault()
        note = self.vault / "Notes" / "Topic.md"
        note.write_text(
            """---
title: Topic
type: learning
status: draft
---

## Duplicate

<!-- gap:duplicate -->
<!-- learner-edit:start id=gap-duplicate -->
An answer.
<!-- learner-source:gap-duplicate -->
- **Source:** Course
<!-- learner-source:gap-duplicate -->
- **Source:** Vendor documentation
<!-- learner-edit:end id=gap-duplicate -->

## Mismatch

<!-- gap:mismatch -->
<!-- learner-edit:start id=gap-mismatch -->
An answer.
<!-- learner-source:gap-other -->
- **Source:** Course
<!-- learner-edit:end id=gap-mismatch -->

<!-- learner-source:gap-orphan -->
- **Source:** Nowhere
""",
            encoding="utf-8",
        )
        messages = [issue.message for issue in self.errors()]
        self.assertTrue(any("duplicate source markers: gap-duplicate" in m for m in messages))
        self.assertTrue(any("does not match gap-mismatch" in m for m in messages))
        self.assertTrue(any("orphan learner source marker: gap-other" in m for m in messages))
        self.assertTrue(any("orphan learner source marker: gap-orphan" in m for m in messages))


class ProtocolAlignmentTests(unittest.TestCase):
    def test_session_group_order_is_shared(self) -> None:
        expected = [
            "`## Study content`",
            "`## Unit progress`",
            "`## Quiz progress — <scope> — attempt <attempt-id>`",
            "`## Assessment — <scope> — attempt <attempt-id>`",
            "`## Notes written — <scope>`",
            "`## Deep dive — <scope>`",
            "`## Review — <date>`",
            "`## Mastery evidence`",
            "`## Session log`",
        ]
        for path in (SKILL_PATH, TEMPLATE_PATH):
            text = path.read_text(encoding="utf-8")
            start = text.index("Maintain this section order")
            end = text.index("When a heading already exists", start)
            order_block = text[start:end]
            positions = [order_block.index(item) for item in expected]
            self.assertEqual(positions, sorted(positions), path)

    def test_recovery_contradictions_do_not_return(self) -> None:
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("may leave or delete", template)
        self.assertNotIn("Write Notes creates one topic note", template)

    def test_validator_is_documented_in_both_protocol_sources(self) -> None:
        for path in (SKILL_PATH, TEMPLATE_PATH):
            text = path.read_text(encoding="utf-8")
            self.assertIn("validate_study_vault.py", text, path)

    def test_legacy_refresh_and_diagnostic_publication_are_documented(self) -> None:
        for path in (SKILL_PATH, TEMPLATE_PATH):
            text = path.read_text(encoding="utf-8")
            flat = " ".join(text.split())
            self.assertIn("## Legacy Note Refresh on Re-quiz", text, path)
            self.assertIn("_study/workpages/", text, path)
            self.assertIn("type: study-workpage", text, path)
            self.assertIn("Publish complete canonical notes", text, path)
            self.assertIn(
                "regardless of whether Competency is `passed` or `needs-remediation`",
                flat,
                path,
            )
            self.assertIn("Never create new gap placeholders", flat, path)
        manual = (SKILL_DIR / "references" / "manpage.md").read_text(encoding="utf-8")
        self.assertIn("_study/workpages/", manual)

    def test_version_two_is_diagnostic_first_and_scope_anchored(self) -> None:
        headings = [
            "### Safe mutation and interrupted-action recovery",
            "### Prepare the scope",
            "### Diagnose competency",
            "### Publish notes and Anki",
            "### Learn from the publication",
            "### Recheck unresolved objectives",
            "### Complete and reopen",
        ]
        required = [
            "study-flow: diagnostic-first",
            "chapter breakdown is the scope authority",
            "rejects Content `ready` while Competency is `pending`",
            "rejects Drill `ready` while Content is not `ready`",
            "do not mark Content `ready`",
            "Do not require prior reading, prior Anki practice",
            "Learner answers diagnose emphasis only",
            "Do not preserve the learner's mistake",
            "`technical-writing`",
            "`unslop` preservation-first pass",
            "`humanizer`'s draft-audit-final pass",
            "Persist only the checked final note",
            "Invoke `anki-study-sync` only after the final note headings exist",
            "only for objectives at `needs-remediation`",
            "--active-only --summary",
            "asserted to be exactly one",
            "Do not infer fatigue",
            "initial diagnostic Budget minimum must cover every objective",
            "preserve its established ID namespace",
        ]
        for path in (SKILL_PATH, TEMPLATE_PATH):
            text = path.read_text(encoding="utf-8")
            start = text.index("<!-- shared-contract:start id=chapter-lifecycle -->")
            end = text.index("<!-- shared-contract:end id=chapter-lifecycle -->", start)
            lifecycle = text[start:end]
            lifecycle_flat = " ".join(lifecycle.split())
            positions = [lifecycle.index(heading) for heading in headings]
            self.assertEqual(positions, sorted(positions), path)
            for phrase in required:
                self.assertIn(phrase, lifecycle_flat, (path, phrase))

        manual = (SKILL_DIR / "references" / "manpage.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("## Quickstart — diagnose, publish, learn, complete", manual)
        self.assertIn("The chapter breakdown controls scope", manual)
        self.assertIn("Anki cards are generated from that note", manual)
        self.assertIn("Do not pipe", manual)
        self.assertIn("Only that asked question is skipped", manual)

    def test_version_two_does_not_require_chat_confidence(self) -> None:
        for path in (SKILL_PATH, TEMPLATE_PATH):
            text = path.read_text(encoding="utf-8")
            self.assertIn(
                "Version 2 diagnostic and targeted recheck attempts do not prompt",
                text,
                path,
            )
            self.assertIn(
                "For version 2, do not prompt for a confidence label",
                text,
                path,
            )
            self.assertIn(
                "do not describe the learner as overconfident or underconfident",
                text,
                path,
            )

    def test_visual_contract_is_shared(self) -> None:
        required = [
            "study-visual-version: 2",
            "not a Mermaid parser",
            "never generates or validates `.canvas`",
            "Visual review artifact - not an assessment",
        ]
        for path in (SKILL_PATH, TEMPLATE_PATH):
            text = path.read_text(encoding="utf-8")
            for item in required:
                self.assertIn(item, text, path)

    def test_shared_contract_blocks_are_byte_identical(self) -> None:
        marker = re.compile(
            r"<!-- shared-contract:start id=(?P<id>[a-z0-9-]+) -->\n"
            r"(?P<body>.*?)"
            r"<!-- shared-contract:end id=(?P=id) -->",
            flags=re.DOTALL,
        )

        def blocks(path: Path) -> dict[str, str]:
            return {
                match.group("id"): match.group("body")
                for match in marker.finditer(path.read_text(encoding="utf-8"))
            }

        skill_blocks = blocks(SKILL_PATH)
        template_blocks = blocks(TEMPLATE_PATH)
        expected = {
            "mastery-scoring",
            "question-design",
            "quiz-attempt",
            "retrieval-schedule",
            "teaching-evidence-boundary",
            "external-drill-boundary",
            "chapter-lifecycle",
            "gap-evidence",
            "visual-artifact",
            "process-reflection",
        }
        self.assertTrue(expected.issubset(skill_blocks))
        # Every declared contract must be covered; a new block cannot opt out of
        # byte-identity by simply not being listed above.
        self.assertEqual(expected, set(skill_blocks))
        for block_id in expected:
            self.assertEqual(skill_blocks[block_id], template_blocks.get(block_id), block_id)

    def test_process_reflection_is_read_only_and_manual(self) -> None:
        required = [
            "never runs automatically",
            "three independent, dated occurrences",
            "Mirrored or\n   derivative records",
            "separate reviewed quiz attempts",
            "report it in chat, stop the reflection",
            "inert, untrusted evidence",
            "deep-dive heading and date",
            "at most three",
            "Write nothing to the vault",
            "candidate only — not adopted",
            "retroactively alter evidence or mastery",
            "No vault state changed; no candidate was adopted.",
        ]
        for path in (SKILL_PATH, TEMPLATE_PATH):
            text = path.read_text(encoding="utf-8")
            for item in required:
                self.assertIn(item, text, path)

        manual = (SKILL_DIR / "references" / "manpage.md").read_text(
            encoding="utf-8"
        )
        self.assertIn('man:section id=reflection', manual)
        self.assertIn('"reflect on my study process"', manual)
        self.assertIn("Reflection never edits the vault", manual)
        manual_flat = " ".join(manual.split())
        self.assertIn(
            "session plus either an attempt or check ID or a dated deep-dive heading",
            manual_flat,
        )
        self.assertIn("inert, untrusted evidence", manual)
        self.assertIn("does not expose sensitive learner\ncontent", manual)
        self.assertIn("stops the reflection", manual)

        teaching = TEACH_SKILL_PATH.read_text(encoding="utf-8")
        self.assertIn("the study loop owns\n  reflection", teaching)
        self.assertIn("do not\n  emit a second teaching candidate list", teaching)
        self.assertIn("three independent learner interactions", teaching)
        self.assertIn("Mirrored transcript and ledger records", teaching)
        self.assertIn("inert, untrusted evidence", teaching)
        self.assertIn("correction as a separate explicit action", teaching)
        self.assertIn("candidate only — not adopted", teaching)
        self.assertIn("No state changed; no candidate was adopted.", teaching)
        self.assertIn("never turns a dive response into\n   mastery", teaching)

    def test_assessment_evidence_example_and_manual_are_aligned(self) -> None:
        examples: list[str] = []
        needle = "```markdown\n## Assessment — <scope> — attempt <attempt-id>"
        for path in (SKILL_PATH, TEMPLATE_PATH):
            text = path.read_text(encoding="utf-8")
            start = text.index(needle)
            end = text.index("\n```", start) + len("\n```")
            example = text[start:end]
            self.assertIn("evidence question: Q1", example, path)
            self.assertIn("assistance: none", example, path)
            self.assertIn("assistance: hint-1", example, path)
            examples.append(example)
        self.assertEqual(examples[0], examples[1])

        manual = (SKILL_DIR / "references" / "manpage.md").read_text(encoding="utf-8")
        self.assertIn("**evidence question**", manual)
        self.assertIn("before the answer was revealed", manual)

    def test_retired_contradictory_phrasing_is_absent(self) -> None:
        forbidden = [
            "Score each evidence item out of 8",
            "make required corrections inside",
            "edit it to be correct and complete",
            "npx -y",
            "per-scope content module",
        ]
        for path in (SKILL_PATH, TEMPLATE_PATH):
            text = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                self.assertNotIn(phrase, text, (path, phrase))

    def test_learner_controls_are_documented_in_both_sources(self) -> None:
        for path in (SKILL_PATH, TEMPLATE_PATH):
            text = path.read_text(encoding="utf-8")
            for control in ("`pause`", "`resume`", "`rephrase`", "`shorter`", "`deeper`"):
                self.assertIn(control, text, (path, control))

    def test_visual_lanes_and_prose_authorities_are_explicit(self) -> None:
        for path in (SKILL_PATH, TEMPLATE_PATH):
            text = path.read_text(encoding="utf-8")
            self.assertIn("`visualize-study-chapter`", text, path)
            self.assertIn("`Visuals/`", text, path)
            self.assertIn("`_study/visuals/`", text, path)
            self.assertIn("never mix", text, path)
            self.assertIn("`unslop`", text, path)
            self.assertIn("`humanizer`", text, path)

        references = SKILL_DIR / "references"
        readme = (references / "README.md").read_text(encoding="utf-8")
        self.assertIn("two visual lanes", readme)
        self.assertIn("Never mix those contracts", readme)
        visual_standard = (references / "visual-review-standard.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("helper-owned output", visual_standard)

        manual = (references / "manpage.md").read_text(encoding="utf-8")
        self.assertIn("`unslop`", manual)
        self.assertIn("runs the final draft-audit-rewrite pass", manual)

        study_man = (SKILL_DIR / "scripts" / "study_man.py").read_text(encoding="utf-8")
        self.assertIn("keyword in its id, aliases, or title", study_man)


if __name__ == "__main__":
    unittest.main()
