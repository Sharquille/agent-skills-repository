from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
SURFACE_DIR = SKILL_DIR / "references" / "tactile-study-surface"
ASSEMBLER_PATH = SURFACE_DIR / "assemble.py"
EXAMPLE_PATH = SURFACE_DIR / "example-content.json"
VALIDATOR_PATH = SKILL_DIR / "scripts" / "validate_study_vault.py"


def load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


assembler = load_script("obsidian_study_loop_tactile_assembler", ASSEMBLER_PATH)
validator = load_script("obsidian_study_loop_tactile_validator", VALIDATOR_PATH)


class TactileAssemblerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))

    def validated(self, manifest: dict | None = None):
        return assembler.validate_manifest(manifest or copy.deepcopy(self.manifest))

    def prepare_vault(self, root: Path, *, source: bool = True) -> tuple[Path, Path]:
        vault = root / "Vault"
        visuals = vault / "_study" / "visuals"
        visuals.mkdir(parents=True)
        if source:
            note = vault / self.manifest["meta"]["source"]
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text("# Traceable source\n", encoding="utf-8")
        return vault, visuals

    def test_valid_manifest_assembles_generic_self_contained_surface(self) -> None:
        artifact = assembler.render_artifact(self.validated())
        self.assertIn("<span class=\"brand\">Study review</span>", artifact)
        self.assertIn("study visual v1 · tactile surface v2", artifact)
        self.assertIn("default-src 'none'", artifact)
        self.assertIn("<script>", artifact)
        self.assertIn("<div class=\"grid-3\">", artifact)
        self.assertNotIn("Sec+ field unit", artifact)
        self.assertNotIn("TS7-built", artifact)
        self.assertNotIn("https://", artifact)

    def test_generated_surface_passes_visual_artifact_validator(self) -> None:
        artifact = assembler.render_artifact(self.validated())
        with tempfile.TemporaryDirectory() as temporary:
            vault, visuals = self.prepare_vault(Path(temporary))
            path = visuals / "example.html"
            path.write_text(artifact, encoding="utf-8")
            issues = []
            validator.validate_visual_artifact(path, vault, issues)
            self.assertEqual(issues, [])

    def test_empty_cues_produce_an_honest_script_free_static_page(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["cues"] = []
        artifact = assembler.render_artifact(self.validated(manifest))
        self.assertNotIn("<h2>Retrieval deck</h2>", artifact)
        self.assertNotIn('href="#retrieval"', artifact)
        self.assertNotIn("data-theme-toggle", artifact)
        self.assertNotIn("<script>", artifact)
        self.assertIn("script-src 'none'", artifact)

    def test_metadata_and_plain_text_are_escaped(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["meta"]["title"] = '</title><script id="meta-pwn">alert(1)</script>'
        manifest["meta"]["scope_name"] = 'A & B <img src="x">'
        manifest["sections"][0]["title"] = "Choose < deny & allow >"
        manifest["cues"][0]["question"] = "What does <script> mean?"
        artifact = assembler.render_artifact(self.validated(manifest))
        self.assertNotIn('<script id="meta-pwn">', artifact)
        self.assertNotIn('<img src="x">', artifact)
        self.assertIn("&lt;/title&gt;&lt;script id=&quot;meta-pwn&quot;&gt;", artifact)
        self.assertIn("A &amp; B &lt;img src=&quot;x&quot;&gt;", artifact)
        self.assertIn("Choose &lt; deny &amp; allow &gt;", artifact)
        self.assertIn("What does &lt;script&gt; mean?", artifact)

    def test_body_text_is_escaped_while_allowlisted_markup_is_preserved(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["sections"][0]["body_html"] = (
            '<div class="contrast"><h3>A &amp; B</h3><p>One &lt; two</p></div>'
        )
        artifact = assembler.render_artifact(self.validated(manifest))
        self.assertIn(
            '<div class="contrast"><h3>A &amp; B</h3><p>One &lt; two</p></div>',
            artifact,
        )

    def test_script_style_and_unknown_elements_are_rejected(self) -> None:
        payloads = [
            "<script>alert(1)</script>",
            "<style>body{display:none}</style>",
            "<svg><script>alert(1)</script></svg>",
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                manifest = copy.deepcopy(self.manifest)
                manifest["sections"][0]["body_html"] = payload
                with self.assertRaisesRegex(assembler.ManifestError, "not allowed"):
                    self.validated(manifest)

    def test_event_url_and_unknown_attributes_are_rejected(self) -> None:
        payloads = [
            '<article class="card" onmouseover="alert(1)"><p>x</p></article>',
            '<p href="https://example.invalid">x</p>',
            '<div class="card" style="display:none"><p>x</p></div>',
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                manifest = copy.deepcopy(self.manifest)
                manifest["sections"][0]["body_html"] = payload
                with self.assertRaises(assembler.ManifestError):
                    self.validated(manifest)

    def test_unknown_or_invalid_primitive_classes_are_rejected(self) -> None:
        payloads = [
            '<article class="card remote"><p>x</p></article>',
            '<div class="cols-3"><p>x</p></div>',
            '<span class="warn">x</span>',
            '<div class="grid-2 grid-3"><p>x</p></div>',
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                manifest = copy.deepcopy(self.manifest)
                manifest["sections"][0]["body_html"] = payload
                with self.assertRaises(assembler.ManifestError):
                    self.validated(manifest)

    def test_body_ids_and_duplicate_or_unsafe_section_ids_are_rejected(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["sections"][0]["body_html"] = '<div id="owned"><p>x</p></div>'
        with self.assertRaisesRegex(assembler.ManifestError, "body ids"):
            self.validated(manifest)

        for first, second in [("same", "same"), ("retrieval", "other"), ("Unsafe ID", "other")]:
            with self.subTest(first=first, second=second):
                manifest = copy.deepcopy(self.manifest)
                manifest["sections"] = manifest["sections"][:2]
                manifest["sections"][0]["id"] = first
                manifest["sections"][1]["id"] = second
                with self.assertRaises(assembler.ManifestError):
                    self.validated(manifest)

    def test_css_injection_through_accent_is_rejected(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["meta"]["accent"] = "red; } body { display: none"
        with self.assertRaisesRegex(assembler.ManifestError, "oklch"):
            self.validated(manifest)

    def test_remote_source_and_utc_z_timestamp_are_rejected(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["meta"]["source"] = "https://example.invalid/note"
        with self.assertRaisesRegex(assembler.ManifestError, "vault-local"):
            self.validated(manifest)

        manifest = copy.deepcopy(self.manifest)
        manifest["meta"]["generated"] = "2026-07-12T18:30:00Z"
        with self.assertRaisesRegex(assembler.ManifestError, "numeric offset"):
            self.validated(manifest)

    def test_cli_reports_invalid_json_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault, visuals = self.prepare_vault(root)
            manifest = root / "bad.json"
            output = visuals / "out.html"
            manifest.write_text('{"meta":', encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ASSEMBLER_PATH),
                    "--vault",
                    str(vault),
                    str(manifest),
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("invalid JSON", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(output.exists())

    def test_cli_rejects_invalid_utf8_and_duplicate_json_keys(self) -> None:
        payloads = [
            b"\xff\xfe",
            b'{"meta": {}, "meta": {}, "sections": [], "cues": []}',
        ]
        for payload in payloads:
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                vault, visuals = self.prepare_vault(root)
                manifest = root / "bad.json"
                output = visuals / "out.html"
                manifest.write_bytes(payload)
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ASSEMBLER_PATH),
                        "--vault",
                        str(vault),
                        str(manifest),
                        str(output),
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse(output.exists())

    def test_cli_assembles_example_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault, visuals = self.prepare_vault(Path(temporary))
            output = visuals / "artifact.html"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ASSEMBLER_PATH),
                    "--vault",
                    str(vault),
                    str(EXAMPLE_PATH),
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            artifact = output.read_text(encoding="utf-8")
            self.assertIn("Visual review artifact - not an assessment", artifact)
            self.assertIn("<meta name=\"study-source\"", artifact)

    def test_cli_rejects_missing_traceability_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault, visuals = self.prepare_vault(Path(temporary), source=False)
            output = visuals / "artifact.html"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ASSEMBLER_PATH),
                    "--vault",
                    str(vault),
                    str(EXAMPLE_PATH),
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("meta.source does not resolve", result.stderr)
            self.assertFalse(output.exists())

    def test_cli_rejects_output_parent_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault, _ = self.prepare_vault(root)
            outside = root / "Outside"
            outside.mkdir()
            escaped_parent = vault / "_study" / "escaped-visuals"
            escaped_parent.symlink_to(outside, target_is_directory=True)
            output = escaped_parent / "artifact.html"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ASSEMBLER_PATH),
                    "--vault",
                    str(vault),
                    str(EXAMPLE_PATH),
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("directly inside", result.stderr)
            self.assertFalse((outside / "artifact.html").exists())

    def test_cli_rejects_symlinked_visuals_root_outside_vault(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = root / "Vault"
            (vault / "_study").mkdir(parents=True)
            note = vault / self.manifest["meta"]["source"]
            note.parent.mkdir(parents=True)
            note.write_text("# Traceable source\n", encoding="utf-8")
            outside = root / "Outside"
            outside.mkdir()
            (vault / "_study" / "visuals").symlink_to(
                outside, target_is_directory=True
            )
            output = vault / "_study" / "visuals" / "artifact.html"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ASSEMBLER_PATH),
                    "--vault",
                    str(vault),
                    str(EXAMPLE_PATH),
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("inside the vault", result.stderr)
            self.assertFalse((outside / "artifact.html").exists())


if __name__ == "__main__":
    unittest.main()
