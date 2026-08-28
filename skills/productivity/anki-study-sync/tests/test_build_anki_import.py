from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "build_anki_import.py"


class BuildAnkiImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.vault = self.root / "Vault"
        (self.vault / "_study" / "anki").mkdir(parents=True)
        (self.vault / "Notes").mkdir()
        (self.vault / "Notes" / "Chapter 1.md").write_text(
            "# Chapter 1\n\n## First\n\nFirst.\n\n## Second\n\nSecond.\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def manifest(self) -> dict[str, object]:
        return {
            "schema": "anki-study-sync.manifest",
            "version": 1,
            "chapter_id": "chapter-1",
            "deck": "Course::Chapter 1",
            "notetype": "Basic",
            "objectives": ["First objective", "Second objective"],
            "cards": [
                {
                    "id": "course.ch1.second.typed",
                    "objective": "Second objective",
                    "type": "typed",
                    "prompt": "Second prompt",
                    "answer": "Second answer",
                    "source": "Notes/Chapter 1.md#Second",
                    "revision": 2,
                    "status": "active",
                    "tags": ["chapter-1", "course"],
                },
                {
                    "id": "course.ch1.first.basic",
                    "objective": "First objective",
                    "type": "basic",
                    "prompt": "First\nprompt",
                    "answer": "First & answer",
                    "source": "Notes/Chapter 1.md#First",
                    "revision": 1,
                    "status": "active",
                    "tags": ["course"],
                },
            ],
        }

    def run_script(
        self, manifest: dict[str, object]
    ) -> subprocess.CompletedProcess[str]:
        path = self.vault / "_study" / "anki" / "manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path), "--vault", str(self.vault)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_renders_deterministic_sorted_tsv(self) -> None:
        first = self.run_script(self.manifest())
        second = self.run_script(self.manifest())
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertIn("#notetype:Basic", first.stdout)
        self.assertIn("#columns:Front\tBack\tGUID\tTags", first.stdout)
        self.assertIn("#guid column:3", first.stdout)
        self.assertIn("#tags column:4", first.stdout)
        self.assertIn("#tags:study-loop::chapter::chapter-1", first.stdout)
        rows = [line for line in first.stdout.splitlines() if not line.startswith("#")]
        first_fields = rows[0].split("\t")
        second_fields = rows[1].split("\t")
        self.assertEqual(len(first_fields), 4)
        self.assertEqual(first_fields[0], "First<br>prompt")
        self.assertIn("First &amp; answer", first_fields[1])
        self.assertIn("<b>Objective:</b> First objective", first_fields[1])
        self.assertIn("Notes/Chapter 1.md#First", first_fields[1])
        self.assertEqual(first_fields[2], "course.ch1.first.basic")
        self.assertIn("study-loop::status::active", first_fields[3])
        self.assertEqual(second_fields[0], "Second prompt")
        self.assertEqual(second_fields[2], "course.ch1.second.typed")
        self.assertIn("study-loop::typed", second_fields[3])
        self.assertNotEqual(first_fields[0], first_fields[2])

    def test_rejects_duplicate_ids(self) -> None:
        manifest = self.manifest()
        manifest["cards"][1]["id"] = manifest["cards"][0]["id"]
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate card IDs", result.stderr)

    def test_retired_card_is_exported_and_tagged(self) -> None:
        manifest = self.manifest()
        retired = manifest["cards"][1]
        retired["status"] = "retired"
        replacement = dict(retired)
        replacement["id"] = "course.ch1.first-current.basic"
        replacement["status"] = "active"
        manifest["cards"].append(replacement)
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 0, result.stderr)
        retired_row = next(
            row
            for row in result.stdout.splitlines()
            if "\tcourse.ch1.first.basic\t" in row
        )
        self.assertIn("study-loop::retired", retired_row)

    def test_rejects_unsafe_source(self) -> None:
        manifest = self.manifest()
        manifest["cards"][0]["source"] = "../Private.md#Secrets"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("stay inside the vault", result.stderr)

    def test_rejects_unknown_card_type(self) -> None:
        manifest = self.manifest()
        manifest["cards"][0]["type"] = "image-occlusion"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("basic or typed", result.stderr)

    def test_rejects_missing_source_heading(self) -> None:
        manifest = self.manifest()
        manifest["cards"][0]["source"] = "Notes/Chapter 1.md#Missing"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("heading does not exist", result.stderr)

    def test_rejects_heading_found_only_inside_code_fence(self) -> None:
        note = self.vault / "Notes" / "Chapter 1.md"
        note.write_text(
            "# Chapter 1\n\n```markdown\n## Hidden\n```\n\n## First\n\nFirst.\n",
            encoding="utf-8",
        )
        manifest = self.manifest()
        manifest["cards"][0]["source"] = "Notes/Chapter 1.md#Hidden"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("heading does not exist", result.stderr)

    def test_rejects_ambiguous_source_heading(self) -> None:
        note = self.vault / "Notes" / "Chapter 1.md"
        note.write_text(
            "# Chapter 1\n\n## First\n\nOne.\n\n## First\n\nTwo.\n\n## Second\n\nSecond.\n",
            encoding="utf-8",
        )
        result = self.run_script(self.manifest())
        self.assertEqual(result.returncode, 1)
        self.assertIn("heading is ambiguous", result.stderr)

    def test_rejects_tab_inside_visible_field(self) -> None:
        manifest = self.manifest()
        manifest["cards"][0]["prompt"] = "Broken\tprompt"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("must not contain tabs", result.stderr)

    def test_rejects_undeclared_card_objective(self) -> None:
        manifest = self.manifest()
        manifest["cards"][0]["objective"] = "Unknown objective"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("card objectives are not declared", result.stderr)

    def test_rejects_objective_without_active_card(self) -> None:
        manifest = self.manifest()
        manifest["cards"][0]["status"] = "retired"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("objectives without an active card", result.stderr)

    def test_rejects_custom_note_type(self) -> None:
        manifest = self.manifest()
        manifest["notetype"] = "Study Loop"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("notetype must be Basic", result.stderr)

    def test_atomic_output_replaces_existing_file(self) -> None:
        manifest_path = self.vault / "_study" / "anki" / "manifest.json"
        manifest_path.write_text(json.dumps(self.manifest()), encoding="utf-8")
        output = self.vault / "_study" / "anki" / "chapter.tsv"
        output.write_text("old\n", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(manifest_path),
                "--vault",
                str(self.vault),
                "--output",
                str(output),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(output.read_text(encoding="utf-8").startswith("#separator:tab"))


if __name__ == "__main__":
    unittest.main()
