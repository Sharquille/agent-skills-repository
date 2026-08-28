from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "study_dive.py"


def build_vault(root: Path, version: str = "2", competencies: tuple[str, ...] = ("needs-remediation", "needs-remediation")) -> Path:
    vault = root / "Vault"
    (vault / "_study" / "dives").mkdir(parents=True)
    session_rel = "_study/sessions/2026-08-28-test-v2.md"
    session_path = vault / session_rel
    session_path.parent.mkdir(parents=True)
    rows = "".join(
        f"| 3.3.{index} Obj{index} | Notes/N.md#s{index} | ready | ready | {state} | reason {index} | next {index} |\n"
        for index, state in enumerate(competencies, start=1)
    )
    session_path.write_text(
        "---\n"
        "topic: 3.3 Hashing\n"
        "created: 2026-08-28T00:00:00-0400\n"
        "status: learning\n"
        f"study-loop-version: {version}\n"
        "objectives:\n"
        "  - 3.3.1 Obj1\n"
        "---\n"
        "\n"
        "## Objective status\n"
        "\n"
        "| Objective | Note | Content | Drill | Competency | Reason | Next action |\n"
        "|---|---|---|---|---|---|---|\n"
        f"{rows}\n"
        "## Session log\n"
        "\n"
        "- 2026-08-28T00:00:00-0400 - created\n"
    )
    (vault / "_study" / "state.json").write_text(
        json.dumps({"active_session": session_rel})
    )
    return vault


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *[str(a) for a in args]],
        capture_output=True,
        text=True,
    )


class StudyDiveScaffoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_scaffold_writes_handoff_with_gap_topics(self) -> None:
        vault = build_vault(self.root)
        result = run([vault])
        self.assertEqual(result.returncode, 0, result.stderr)
        handoffs = list((vault / "_study" / "dives").glob("*-handoff.md"))
        self.assertEqual(len(handoffs), 1)
        text = handoffs[0].read_text()
        for expected in (
            "type: dive-handoff",
            "# Dive handoff — 3.3 Hashing",
            "3.3.1 Obj1 — reason 1",
            "3.3.2 Obj2 — reason 2",
            "technical-writing",
            "unslop",
            "humanizer",
            "portable-markdown",
            "not an assessment",
            "## Deep dive — 3.3 Hashing",
        ):
            self.assertIn(expected, text)

    def test_scaffold_explicit_objective_without_gaps(self) -> None:
        vault = build_vault(self.root, competencies=("pending", "pending"))
        result = run([vault, "--objective", "key stretching"])
        self.assertEqual(result.returncode, 0, result.stderr)
        text = next((vault / "_study" / "dives").glob("*-handoff.md")).read_text()
        self.assertIn("key stretching — learner-requested topic", text)

    def test_scaffold_without_gaps_or_topics_fails(self) -> None:
        vault = build_vault(self.root, competencies=("pending",))
        result = run([vault])
        self.assertEqual(result.returncode, 2)
        self.assertIn("no needs-remediation", result.stderr)

    def test_scaffold_rejects_legacy_session(self) -> None:
        vault = build_vault(self.root, version="1")
        result = run([vault])
        self.assertEqual(result.returncode, 2)
        self.assertIn("version 2", result.stderr)

    def test_scaffold_leaves_rest_of_vault_untouched(self) -> None:
        vault = build_vault(self.root)
        before = {
            path: path.read_text()
            for path in vault.rglob("*")
            if path.is_file()
        }
        result = run([vault])
        self.assertEqual(result.returncode, 0, result.stderr)
        after = {
            path: path.read_text()
            for path in vault.rglob("*")
            if path.is_file()
        }
        added = set(after) - set(before)
        self.assertEqual(len(added), 1)
        self.assertTrue(added.pop().name.endswith("-handoff.md"))
        for path, content in before.items():
            self.assertEqual(after[path], content)


class StudyDiveCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.vault = build_vault(self.root)
        result = run([self.vault])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.handoff = next((self.vault / "_study" / "dives").glob("*-handoff.md"))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_check_fails_while_chain_unticked(self) -> None:
        result = run([self.vault, "--check", self.handoff])
        self.assertEqual(result.returncode, 1)
        self.assertIn("unticked", result.stdout)

    def test_check_passes_when_chain_complete(self) -> None:
        self.handoff.write_text(self.handoff.read_text().replace(CHECK := "- [ ] ", "- [x] "))
        result = run([self.vault, "--check", self.handoff])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_check_flags_obsidian_only_syntax(self) -> None:
        text = self.handoff.read_text().replace("- [ ] ", "- [x] ")
        text = text.replace("# Dive handoff", "%% hidden %%\n# Dive handoff")
        self.handoff.write_text(text)
        result = run([self.vault, "--check", self.handoff])
        self.assertEqual(result.returncode, 1)
        self.assertIn("%%", result.stdout)


if __name__ == "__main__":
    unittest.main()
