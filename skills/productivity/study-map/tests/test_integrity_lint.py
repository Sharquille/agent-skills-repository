from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "integrity-lint.sh"


class IntegrityLintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.vault = Path(self.temporary.name) / "Vault"
        (self.vault / "Notes").mkdir(parents=True)
        (self.vault / "Maps").mkdir()
        (self.vault / "Notes" / "Topic.md").write_text(
            "---\ntags:\n  - study\n---\n\n# Topic\n\n## Exact heading\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_lint(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(SCRIPT), str(self.vault)],
            text=True,
            capture_output=True,
            check=False,
        )

    def write_canvas(self, *, subpath: str = "#Exact heading", node_id: str = "topic") -> None:
        data = {
            "nodes": [
                {
                    "id": node_id,
                    "type": "file",
                    "x": 0,
                    "y": 0,
                    "width": 240,
                    "height": 80,
                    "file": "Notes/Topic.md",
                    "subpath": subpath,
                }
            ],
            "edges": [],
        }
        (self.vault / "Maps" / "Topic.canvas").write_text(
            json.dumps(data), encoding="utf-8"
        )

    def test_valid_canvas_subpath_and_markdown_heading_link_pass(self) -> None:
        self.write_canvas()
        (self.vault / "Maps" / "Home.md").write_text(
            "# Home\n\n- [[Notes/Topic#Exact heading|Topic section]]\n",
            encoding="utf-8",
        )
        result = self.run_lint()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_canvas_subpath_fails(self) -> None:
        self.write_canvas(subpath="#Renamed heading")
        result = self.run_lint()
        self.assertEqual(result.returncode, 1)
        self.assertIn("subpath '#Renamed heading' -> missing heading", result.stdout)

    def test_missing_markdown_heading_anchor_fails(self) -> None:
        (self.vault / "Maps" / "Home.md").write_text(
            "# Home\n\n- [[Topic#Renamed heading]]\n", encoding="utf-8"
        )
        result = self.run_lint()
        self.assertEqual(result.returncode, 1)
        self.assertIn("subpath '#Renamed heading' -> missing heading", result.stdout)

    def test_duplicate_canvas_node_id_fails(self) -> None:
        data = {
            "nodes": [
                {"id": "same", "type": "text", "x": 0, "y": 0, "width": 1, "height": 1, "text": "A"},
                {"id": "same", "type": "text", "x": 2, "y": 2, "width": 1, "height": 1, "text": "B"},
            ],
            "edges": [],
        }
        (self.vault / "Maps" / "Duplicate.canvas").write_text(
            json.dumps(data), encoding="utf-8"
        )
        result = self.run_lint()
        self.assertEqual(result.returncode, 1)
        self.assertIn("node id must be non-empty and unique ('same')", result.stdout)

    def test_invalid_canvas_shape_fails_without_traceback(self) -> None:
        (self.vault / "Maps" / "Invalid.canvas").write_text(
            json.dumps({"nodes": "not-an-array", "edges": []}), encoding="utf-8"
        )
        result = self.run_lint()
        self.assertEqual(result.returncode, 1)
        self.assertIn("nodes must be an array of objects", result.stdout)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
