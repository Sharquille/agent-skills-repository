from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
INSTALL_PATH = SKILL_DIR / "scripts" / "install_study_loop.py"


def load_installer():
    spec = importlib.util.spec_from_file_location("study_loop_installer", INSTALL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {INSTALL_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


installer = load_installer()


class InstallStudyLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.vault = Path(self.temporary.name) / "Vault"
        self.vault.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(INSTALL_PATH), str(self.vault), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_dry_run_changes_nothing(self) -> None:
        result = self.run_cli()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("DRY RUN", result.stdout)
        self.assertEqual(list(self.vault.iterdir()), [])

    def test_apply_creates_complete_scaffold(self) -> None:
        result = self.run_cli("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.vault / "STUDY-PROTOCOL.md").is_file())
        self.assertTrue((self.vault / "STUDY-MANUAL.md").is_file())
        self.assertEqual(
            json.loads((self.vault / "_study" / "state.json").read_text()),
            {"active_session": None},
        )
        workpages = self.vault / "_study" / "workpages"
        self.assertTrue(workpages.is_dir(), "workpages scaffold directory missing")
        self.assertTrue((workpages / ".gitkeep").is_file(), "workpages .gitkeep missing")
        anki = self.vault / "_study" / "anki"
        self.assertTrue(anki.is_dir(), "anki scaffold directory missing")
        self.assertTrue((anki / ".gitkeep").is_file(), "anki .gitkeep missing")
        study_readme = (self.vault / "_study" / "README.md").read_text(encoding="utf-8")
        self.assertIn("Markdown and Mermaid review artifacts", study_readme)
        self.assertIn("optional `anki-study-sync` handoff", study_readme)
        for name in installer.POINTER_FILES:
            text = (self.vault / name).read_text(encoding="utf-8")
            self.assertEqual(text.count("## Study sessions"), 1)

    def test_reapply_is_idempotent_and_preserves_active_state(self) -> None:
        first = self.run_cli("--apply")
        self.assertEqual(first.returncode, 0, first.stderr)
        session = self.vault / "_study" / "sessions" / "active.md"
        session.write_text("session evidence\n", encoding="utf-8")
        state = {"active_session": "_study/sessions/active.md"}
        (self.vault / "_study" / "state.json").write_text(
            json.dumps(state), encoding="utf-8"
        )
        protocol = self.vault / "STUDY-PROTOCOL.md"
        protocol.write_text("custom protocol\n", encoding="utf-8")

        second = self.run_cli("--apply")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads((self.vault / "_study" / "state.json").read_text()), state)
        self.assertEqual(protocol.read_text(encoding="utf-8"), "custom protocol\n")
        self.assertEqual(session.read_text(encoding="utf-8"), "session evidence\n")
        for name in installer.POINTER_FILES:
            text = (self.vault / name).read_text(encoding="utf-8")
            self.assertEqual(text.count("## Study sessions"), 1)

    def test_existing_pointer_file_is_appended_once(self) -> None:
        agents = self.vault / "AGENTS.md"
        agents.write_text("# Existing rules\n", encoding="utf-8")
        result = self.run_cli("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        text = agents.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Existing rules"))
        self.assertEqual(text.count("## Study sessions"), 1)

    def test_existing_study_heading_is_extended_without_duplication(self) -> None:
        agents = self.vault / "AGENTS.md"
        agents.write_text(
            "# Existing rules\n\n## Study sessions\nKeep sessions short.\n\n## Other\nKeep.\n",
            encoding="utf-8",
        )
        result = self.run_cli("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        text = agents.read_text(encoding="utf-8")
        self.assertEqual(text.count("## Study sessions"), 1)
        self.assertEqual(text.count("STUDY-PROTOCOL.md"), 1)
        self.assertIn("Keep sessions short.", text)
        self.assertIn("## Other\nKeep.", text)

    def test_invalid_existing_state_blocks_all_changes(self) -> None:
        state_dir = self.vault / "_study"
        state_dir.mkdir()
        (state_dir / "state.json").write_text('{"wrong": true}', encoding="utf-8")
        result = self.run_cli("--apply")
        self.assertEqual(result.returncode, 1)
        self.assertIn("ERROR:", result.stderr)
        self.assertFalse((self.vault / "STUDY-PROTOCOL.md").exists())

    def test_missing_active_session_blocks_all_changes(self) -> None:
        state_dir = self.vault / "_study"
        state_dir.mkdir()
        (state_dir / "state.json").write_text(
            '{"active_session": "_study/sessions/missing.md"}', encoding="utf-8"
        )
        result = self.run_cli("--apply")
        self.assertEqual(result.returncode, 1)
        self.assertIn("regular file", result.stderr)
        self.assertFalse((self.vault / "STUDY-PROTOCOL.md").exists())

    def test_directory_active_session_blocks_all_changes(self) -> None:
        state_dir = self.vault / "_study"
        session_dir = state_dir / "sessions" / "not-a-file.md"
        session_dir.mkdir(parents=True)
        (state_dir / "state.json").write_text(
            '{"active_session": "_study/sessions/not-a-file.md"}', encoding="utf-8"
        )
        result = self.run_cli("--apply")
        self.assertEqual(result.returncode, 1)
        self.assertIn("regular file", result.stderr)
        self.assertFalse((self.vault / "STUDY-PROTOCOL.md").exists())

    def test_directory_at_manual_path_blocks_all_changes(self) -> None:
        (self.vault / "STUDY-MANUAL.md").mkdir()
        result = self.run_cli("--apply")
        self.assertEqual(result.returncode, 1)
        self.assertIn("regular scaffold file", result.stderr)
        self.assertFalse((self.vault / "STUDY-PROTOCOL.md").exists())
        self.assertFalse((self.vault / "_study").exists())

    def test_notes_directory_cannot_escape_vault(self) -> None:
        result = self.run_cli("--notes-dir", "../Outside")
        self.assertEqual(result.returncode, 1)
        self.assertIn("outside the vault", result.stderr)

    def test_existing_custom_protocol_does_not_create_default_notes(self) -> None:
        custom = self.vault / "Course Notes"
        custom.mkdir()
        (self.vault / "STUDY-PROTOCOL.md").write_text(
            f"# Study Protocol\n\n- `NOTES_DIR`: `{custom}`\n", encoding="utf-8"
        )
        result = self.run_cli("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.vault / "Notes").exists())
        self.assertTrue(custom.is_dir())

    def test_symlinked_scaffold_directory_is_rejected(self) -> None:
        real_study = self.vault / "real-study"
        real_study.mkdir()
        (self.vault / "_study").symlink_to(real_study, target_is_directory=True)
        result = self.run_cli("--apply")
        self.assertEqual(result.returncode, 1)
        self.assertIn("symlink", result.stderr.lower())
        self.assertFalse((real_study / "state.json").exists())

    def test_symlinked_pointer_target_is_rejected(self) -> None:
        outside = Path(self.temporary.name) / "outside.md"
        outside.write_text("keep\n", encoding="utf-8")
        (self.vault / "AGENTS.md").symlink_to(outside)
        result = self.run_cli("--apply")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(outside.read_text(encoding="utf-8"), "keep\n")


if __name__ == "__main__":
    unittest.main()
