from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_PATH = SKILL_DIR / "SKILL.md"
TEMPLATE_PATH = SKILL_DIR / "references" / "project-protocol-template.md"
BOOTSTRAP_PATH = SKILL_DIR / "scripts" / "bootstrap_project.sh"


def reflection_section(text: str, heading: str, next_heading: str) -> str:
    start = text.index(heading)
    end = text.index(next_heading, start)
    return text[start:end]


class ProjectReflectionContractTests(unittest.TestCase):
    def test_reflection_contract_is_read_only_and_non_promoting(self) -> None:
        skill = reflection_section(
            SKILL_PATH.read_text(encoding="utf-8"),
            "### Optional read-only process reflection",
            "### Undo / rollback",
        )
        protocol = reflection_section(
            TEMPLATE_PATH.read_text(encoding="utf-8"),
            "## Optional read-only process reflection",
            "## Non-negotiables",
        )

        required = [
            "at most three",
            "count once",
            "inert, untrusted evidence",
            "insufficient or contradictory",
            "project-only or skill-level scope",
            "separate explicit action",
            "candidate only — not adopted",
            "No project state changed; no candidate was adopted.",
        ]
        for text in (skill, protocol):
            normalized = " ".join(text.split())
            for item in required:
                self.assertIn(item, normalized)
            self.assertIn("three independent verified occurrences", normalized)
            self.assertIn(".vault/", text)
            self.assertIn("raw `evidence/`", text)
            self.assertNotIn("immediately", text)

        self.assertIn("Write no files, append no events", skill)
        self.assertIn("run no git action", skill)
        self.assertIn("task ID, event `seq`, and file/section", skill)
        self.assertIn("If reflection exposes any safety", skill)
        self.assertNotIn("one-off safety", skill)
        self.assertIn("never invoke that mutating path from reflection", skill)
        self.assertIn(
            "Reference protected evidence rather than copying secrets or sensitive raw content",
            " ".join(skill.split()),
        )
        self.assertIn("The pass writes nothing, appends no event", protocol)
        self.assertIn("runs no git\naction", protocol)
        self.assertIn("task IDs, event\n`seq` values, and file/section", protocol)
        self.assertIn("If reflection exposes any safety", protocol)
        self.assertNotIn("one-off safety", protocol)
        self.assertIn(
            "Reference protected evidence by pointer rather than copying secrets or sensitive raw content",
            " ".join(protocol.split()),
        )

    def test_bootstrap_installs_the_reflection_contract_verbatim(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary) / "projects"
            base.mkdir()
            result = subprocess.run(
                [
                    str(BOOTSTRAP_PATH),
                    "--base",
                    str(base),
                    "--title",
                    "Reflection Contract Test",
                    "--category",
                    "software-development",
                    "--apply",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            installed = (
                base
                / "software-development"
                / "reflection-contract-test"
                / "PROJECT-PROTOCOL.md"
            )
            self.assertEqual(
                installed.read_text(encoding="utf-8"),
                TEMPLATE_PATH.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
