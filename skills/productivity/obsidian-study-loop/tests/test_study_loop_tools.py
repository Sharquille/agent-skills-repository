from __future__ import annotations

import importlib.util
import json
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


class SyncTests(VaultFixture):
    def test_relative_notes_dir_resolves_from_vault(self) -> None:
        resolved = sync.resolve_notes_dir(Path("Notes"), self.vault.resolve())
        self.assertEqual(resolved, (self.vault / "Notes").resolve())

    def test_cli_relative_notes_dir_is_independent_of_cwd(self) -> None:
        self.write_state(None)
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

    def test_symlinked_protocol_target_is_rejected(self) -> None:
        victim = Path(self.temporary.name) / "victim.md"
        victim.write_text("keep", encoding="utf-8")
        target = self.vault / "STUDY-PROTOCOL.md"
        target.symlink_to(victim)
        with self.assertRaises(sync.SyncError):
            sync.ensure_safe_target(target, self.vault.resolve())
        self.assertEqual(victim.read_text(encoding="utf-8"), "keep")

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

    def test_valid_vault_has_no_findings(self) -> None:
        self.make_valid_vault()
        issues = validator.validate_vault(self.vault.resolve(), self.vault / "Notes")
        self.assertEqual(issues, [])

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


class ProtocolAlignmentTests(unittest.TestCase):
    def test_session_group_order_is_shared(self) -> None:
        expected = [
            "`## Study content`",
            "`## Unit progress`",
            "`## Quiz progress — <scope>`",
            "`## Assessment — <scope>`",
            "`## Notes written — <scope>`",
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


if __name__ == "__main__":
    unittest.main()
