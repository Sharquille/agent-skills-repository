#!/usr/bin/env python3
"""Contract tests for audit_course.py."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from audit_course import audit


class AuditCourseTests(unittest.TestCase):
    def _write(self, root: Path, relative: str, content: str) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_release_ready_course_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = {
                "scripts": {
                    "dev": "vite",
                    "build": "vite build",
                    "test": "vitest run",
                    "typecheck": "tsc --noEmit",
                    "e2e": "playwright test",
                    "preview": "vite preview",
                }
            }
            self._write(root, "package.json", json.dumps(package))
            self._write(root, "package-lock.json", "{}")
            self._write(
                root,
                "README.md",
                "# Course\n\nOne learner. Scope and artifact.\n\n## Deploy\nRun the build and publish dist.",
            )
            self._write(root, "COURSE_CONTRACT.md", "# Course Contract\n")
            self._write(root, "content/m0.mdx", "# Module 0\n")
            self._write(
                root,
                "src/Terminal.tsx",
                "export const label = 'browser-isolated terminal with persisted runbook';",
            )
            self._write(
                root,
                "tests/e2e/course.spec.ts",
                "test('terminal command persists after reload', () => {});",
            )
            self._write(root, "dist/index.html", "<!doctype html><title>Course</title>")

            report = audit(root, release=True)

            self.assertEqual(report.failures, 0)
            self.assertEqual(report.warnings, 0)
            self.assertIn("npm ci", report.suggested_commands)
            self.assertIn("npm run build", report.suggested_commands)

    def test_missing_tests_and_deploy_docs_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(root, "index.html", "<!doctype html><title>Course</title>")
            self._write(root, "README.md", "# Course\n")

            report = audit(root)
            failed_codes = {
                finding.code for finding in report.findings if finding.status == "fail"
            }

            self.assertIn("automated-tests", failed_codes)
            self.assertIn("deployment-docs", failed_codes)

    def test_terminal_without_command_test_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(root, "index.html", "<!doctype html><title>Terminal course</title>")
            self._write(
                root,
                "README.md",
                "# Course\nLearner scope artifact.\n## Deploy\nPublish index.html.",
            )
            self._write(root, "content/m0.md", "# Lesson\n")
            self._write(root, "tests/course_test.py", "def test_page(): assert True\n")

            report = audit(root)
            failed_codes = {
                finding.code for finding in report.findings if finding.status == "fail"
            }

            self.assertIn("terminal-tests", failed_codes)


if __name__ == "__main__":
    unittest.main()
