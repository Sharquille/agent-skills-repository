from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
BOARD = SKILL_DIR / "scripts" / "study_board.py"
VALIDATOR = SKILL_DIR / "scripts" / "validate_study_vault.py"


class StudyBoardV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.vault = Path(self.temporary.name) / "Vault"
        (self.vault / "_study" / "sessions").mkdir(parents=True)
        (self.vault / "_study" / "anki").mkdir()
        (self.vault / "Notes").mkdir()
        (self.vault / ".obsidian").mkdir()
        (self.vault / "STUDY-PROTOCOL.md").write_text(
            f"# Study Protocol\n\n- `NOTES_DIR`: `{self.vault / 'Notes'}`\n",
            encoding="utf-8",
        )
        (self.vault / "_study" / "anki" / "topic.json").write_text(
            "{}\n", encoding="utf-8"
        )
        (self.vault / "_study" / "anki" / "topic.tsv").write_text(
            "#separator:tab\n", encoding="utf-8"
        )
        self.session = self.vault / "_study" / "sessions" / "2026-08-27-topic.md"
        self.write_session("learning")
        (self.vault / "_study" / "state.json").write_text(
            json.dumps({"active_session": "_study/sessions/2026-08-27-topic.md"}),
            encoding="utf-8",
        )
        (self.vault / "Notes" / "Topic.md").write_text(
            """---
title: Topic
type: learning
status: ready
study-loop-version: 2
---

# Topic

## Objective A

Complete explanation.
""",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_session(
        self, status: str, competency: str = "needs-remediation"
    ) -> None:
        applied_evidence = ""
        if competency in {"passed", "needs-remediation"}:
            mastery = "solid" if competency == "passed" else "partial"
            score = "8/8" if competency == "passed" else "4/8"
            evidence = (
                "Correct application and reasoning."
                if competency == "passed"
                else "Application exposed a bounded gap for publication."
            )
            applied_evidence = """
## Quiz progress — Topic — attempt 2026-08-27-01

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: completed — updated: 2026-08-27T10:10:00-0400
- Q1 [application] — Objective A — status: scored — prompt: Apply Objective A. — score: {score} — assistance: none — learner confidence: unknown — evidence: {evidence}
- Consumed by Assessment — Topic — attempt 2026-08-27-01 on 2026-08-27T10:11:00-0400

## Assessment — Topic — attempt 2026-08-27-01

- Objective A — mastery: {mastery} — evidence question: Q1 — score: {score} — assistance: none — evidence: {evidence} — tutor confidence: medium — learner confidence: unknown — calibration: unknown

""".format(mastery=mastery, score=score, evidence=evidence)
        self.session.write_text(
            f"""---
topic: Topic
created: 2026-08-27T10:00:00-0400
status: {status}
study-loop-version: 2
study-flow: diagnostic-first
objectives:
  - Objective A
---

## Study content

Source outline.

## Objective status

| Objective | Note | Content | Drill | Competency | Reason | Next action |
|---|---|---|---|---|---|---|
| Objective A | Notes/Topic.md#Objective A | ready | ready | {competency} | Ready | Run applied check |

## Anki handoff

- Manifest: `_study/anki/topic.json`
- Import: `_study/anki/topic.tsv`
- Status: ready

{applied_evidence}
## Mastery evidence

| Date | Scope | Objective | Evidence | Score | Mastery | Confidence | Notes |
|---|---|---|---|---:|---|---|---|

## Session log

- 2026-08-27T10:00:00-0400 - Chapter prepared. Status: {status}.
""",
            encoding="utf-8",
        )

    def run_cli(self, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), str(self.vault), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_board_renders_from_session_without_creating_board_file(self) -> None:
        result = self.run_cli(BOARD)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Topic — review board", result.stdout)
        self.assertIn(
            "Objective A | Notes/Topic.md#Objective A | ready | ready | needs-remediation",
            result.stdout,
        )
        self.assertFalse((self.vault / "_study" / "review-board.md").exists())

    def test_version_two_vault_is_valid(self) -> None:
        result = self.run_cli(VALIDATOR)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_ready_content_requires_completed_diagnostic_state(self) -> None:
        self.write_session("learning", "pending")
        result = self.run_cli(VALIDATOR)
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "ready content requires a completed diagnostic state", result.stdout
        )

    def test_older_version_two_session_without_flow_marker_is_preserved(self) -> None:
        self.write_session("learning", "pending")
        text = self.session.read_text(encoding="utf-8").replace(
            "study-flow: diagnostic-first\n", ""
        )
        self.session.write_text(text, encoding="utf-8")
        result = self.run_cli(VALIDATOR)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_version_two_rejects_unknown_flow_marker(self) -> None:
        text = self.session.read_text(encoding="utf-8").replace(
            "study-flow: diagnostic-first", "study-flow: notes-first"
        )
        self.session.write_text(text, encoding="utf-8")
        result = self.run_cli(VALIDATOR)
        self.assertEqual(result.returncode, 1)
        self.assertIn("unsupported study-flow: notes-first", result.stdout)

    def test_ready_drill_requires_ready_content(self) -> None:
        text = self.session.read_text(encoding="utf-8").replace(
            "| Objective A | Notes/Topic.md#Objective A | ready | ready | needs-remediation |",
            "| Objective A | pending | pending | ready | needs-remediation |",
        )
        self.session.write_text(text, encoding="utf-8")
        result = self.run_cli(VALIDATOR)
        self.assertEqual(result.returncode, 1)
        self.assertIn("ready drill requires ready content", result.stdout)

    def test_drill_ready_requires_ready_handoff(self) -> None:
        text = self.session.read_text(encoding="utf-8")
        before_handoff = text.split("## Anki handoff", 1)[0]
        after_handoff = text.split("## Mastery evidence", 1)[1]
        self.session.write_text(
            before_handoff + "## Mastery evidence" + after_handoff,
            encoding="utf-8",
        )
        result = self.run_cli(VALIDATOR)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Drill ready requires a ready Anki handoff", result.stdout)

    def test_complete_requires_all_competency_gates(self) -> None:
        self.write_session("complete", "pending")
        result = self.run_cli(VALIDATOR)
        self.assertEqual(result.returncode, 1)
        self.assertIn("complete session has an open gate", result.stdout)

    def test_complete_accepts_passed_competency(self) -> None:
        self.write_session("complete", "passed")
        text = self.session.read_text(encoding="utf-8").replace(
            "| Objective A | Notes/Topic.md#Objective A | ready | ready | passed | Ready | Run applied check |",
            "| Objective A | Notes/Topic.md#Objective A | ready | ready | passed | Complete | none |",
        )
        self.session.write_text(text, encoding="utf-8")
        result = self.run_cli(VALIDATOR)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_complete_rejects_passed_competency_without_applied_evidence(self) -> None:
        self.write_session("complete", "passed")
        text = self.session.read_text(encoding="utf-8")
        before_attempt = text.split("## Quiz progress", 1)[0]
        after_attempt = text.split("## Mastery evidence", 1)[1]
        self.session.write_text(
            before_attempt + "## Mastery evidence" + after_attempt,
            encoding="utf-8",
        )
        result = self.run_cli(VALIDATOR)
        self.assertEqual(result.returncode, 1)
        self.assertIn("no unassisted applied evidence", result.stdout)

    def test_complete_uses_latest_applied_evidence(self) -> None:
        self.write_session("complete", "passed")
        later_miss = """
## Quiz progress — Topic — attempt 2026-08-27-02

- Budget: minimum 1; target 1; maximum 1; mode adaptive
- Attempt status: completed — updated: 2026-08-27T11:10:00-0400
- Q1 [application] — Objective A — status: scored — prompt: Apply Objective A in a fresh case. — score: 2/8 — assistance: none — learner confidence: High — evidence: Materially incorrect application.
- Consumed by Assessment — Topic — attempt 2026-08-27-02 on 2026-08-27T11:11:00-0400

## Assessment — Topic — attempt 2026-08-27-02

- Objective A — mastery: gap — evidence question: Q1 — score: 2/8 — assistance: none — evidence: Materially incorrect application. — tutor confidence: high — learner confidence: High — calibration: overconfident

"""
        text = self.session.read_text(encoding="utf-8").replace(
            "## Mastery evidence", later_miss + "## Mastery evidence"
        )
        self.session.write_text(text, encoding="utf-8")
        result = self.run_cli(VALIDATOR)
        self.assertEqual(result.returncode, 1)
        self.assertIn("no unassisted applied evidence", result.stdout)

    def test_version_two_note_rejects_legacy_work_fields(self) -> None:
        note = self.vault / "Notes" / "Topic.md"
        note.write_text(
            note.read_text(encoding="utf-8")
            + "\n<!-- learner-edit:start id=legacy-gap -->\n"
            + "Learner work.\n<!-- learner-edit:end id=legacy-gap -->\n",
            encoding="utf-8",
        )
        result = self.run_cli(VALIDATOR)
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "version 2 note contains legacy learner-work scaffolding", result.stdout
        )


if __name__ == "__main__":
    unittest.main()
