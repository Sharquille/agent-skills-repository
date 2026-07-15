#!/usr/bin/env python3
"""Read-only structural audit for course websites and learning platforms."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "coverage",
    "node_modules",
    "playwright-report",
    "public/data",
    "test-results",
    "vendor",
}
TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mdx",
    ".mjs",
    ".py",
    ".scss",
    ".ts",
    ".tsx",
    ".vue",
}
TEST_NAME_PARTS = (".spec.", ".test.", "test_", "_test.")
BUILD_OUTPUTS = ("dist/index.html", "build/index.html", "out/index.html")


@dataclass(frozen=True)
class Finding:
    code: str
    status: str
    message: str
    detail: str = ""


@dataclass(frozen=True)
class AuditReport:
    root: str
    release: bool
    findings: list[Finding]
    suggested_commands: list[str]

    @property
    def failures(self) -> int:
        return sum(finding.status == "fail" for finding in self.findings)

    @property
    def warnings(self) -> int:
        return sum(finding.status == "warn" for finding in self.findings)


def _is_skipped(path: Path, root: Path) -> bool:
    relative = path.relative_to(root).as_posix()
    parts = relative.split("/")
    return any(
        skipped == part or relative == skipped or relative.startswith(f"{skipped}/")
        for skipped in SKIP_DIRS
        for part in parts
    )


def _text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or _is_skipped(path, root):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            if path.stat().st_size <= 2_000_000:
                files.append(path)
        except OSError:
            continue
    return files


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _joined_text(files: Iterable[Path]) -> str:
    return "\n".join(_read(path).lower() for path in files)


def _test_files(files: Iterable[Path], root: Path) -> list[Path]:
    tests: list[Path] = []
    for path in files:
        relative = path.relative_to(root).as_posix().lower()
        name = path.name.lower()
        if (
            relative.startswith("tests/")
            or "/tests/" in relative
            or "/__tests__/" in relative
            or any(part in name for part in TEST_NAME_PARTS)
        ):
            tests.append(path)
    return tests


def _has_content_surface(root: Path, files: Iterable[Path]) -> bool:
    for directory in ("content", "curriculum", "lessons", "modules"):
        path = root / directory
        if path.is_dir() and any(child.is_file() for child in path.rglob("*")):
            return True
    for path in files:
        relative = path.relative_to(root).as_posix().lower()
        if relative.startswith(("src/content/", "src/curriculum/", "src/lessons/")):
            return True
    return False


def _load_package(root: Path) -> tuple[dict | None, str | None]:
    package_path = root / "package.json"
    if not package_path.exists():
        return None, None
    try:
        value = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, str(exc)
    if not isinstance(value, dict):
        return None, "package.json must contain an object"
    return value, None


def _finding(code: str, status: str, message: str, detail: str = "") -> Finding:
    return Finding(code=code, status=status, message=message, detail=detail)


def audit(root: Path, *, release: bool = False) -> AuditReport:
    root = root.resolve()
    findings: list[Finding] = []
    suggested: list[str] = []

    if not root.is_dir():
        return AuditReport(
            root=str(root),
            release=release,
            findings=[_finding("root", "fail", "Project root does not exist or is not a directory.")],
            suggested_commands=[],
        )

    files = _text_files(root)
    all_text = _joined_text(files)
    tests = _test_files(files, root)
    test_text = _joined_text(tests)
    readme = next(
        (path for path in (root / "README.md", root / "README.markdown", root / "README.txt") if path.exists()),
        None,
    )
    readme_text = _read(readme).lower() if readme else ""
    package, package_error = _load_package(root)

    has_index = (root / "index.html").is_file()
    has_package = (root / "package.json").is_file()
    findings.append(
        _finding(
            "entrypoint",
            "pass" if has_index or has_package else "fail",
            "Course entrypoint is present." if has_index or has_package else "No index.html or package.json entrypoint was found.",
        )
    )

    findings.append(
        _finding(
            "readme",
            "pass" if readme else "fail",
            "Project README is present." if readme else "Project README is missing.",
        )
    )

    contract = root / "COURSE_CONTRACT.md"
    readme_contract = all(term in readme_text for term in ("learner", "scope", "artifact"))
    findings.append(
        _finding(
            "course-contract",
            "pass" if contract.exists() or readme_contract else "warn",
            "Learner, scope, and artifact contract is documented."
            if contract.exists() or readme_contract
            else "Add COURSE_CONTRACT.md or document the learner, scope, and artifacts in the README.",
        )
    )

    content_surface = _has_content_surface(root, files)
    findings.append(
        _finding(
            "content-separation",
            "pass" if content_surface else "warn",
            "Authored course content has a decoupled content surface."
            if content_surface
            else "No content/curriculum/lesson surface was detected; avoid welding substantial course prose into view markup.",
        )
    )

    findings.append(
        _finding(
            "automated-tests",
            "pass" if tests else "fail",
            f"Detected {len(tests)} automated test file(s)."
            if tests
            else "No automated test files were detected.",
        )
    )

    if package_error:
        findings.append(_finding("package-json", "fail", "package.json is invalid.", package_error))
    elif package is not None:
        scripts = package.get("scripts", {})
        if not isinstance(scripts, dict):
            scripts = {}
            findings.append(_finding("package-scripts", "fail", "package.json scripts must be an object."))
        else:
            has_dev = any(key in scripts for key in ("dev", "start", "serve"))
            has_build = "build" in scripts
            has_test = any(key == "test" or key.startswith("test:") for key in scripts)
            has_e2e = any(key in scripts for key in ("e2e", "test:e2e", "test:browser"))
            has_static = any(key in scripts for key in ("typecheck", "lint", "lint:terms", "check"))
            checks = (
                ("dev-script", has_dev, "Development/serve script"),
                ("build-script", has_build, "Production build script"),
                ("test-script", has_test, "Automated test script"),
            )
            for code, present, label in checks:
                findings.append(
                    _finding(
                        code,
                        "pass" if present else "fail",
                        f"{label} is present." if present else f"{label} is missing from package.json.",
                    )
                )
            findings.append(
                _finding(
                    "browser-script",
                    "pass" if has_e2e else "warn",
                    "Browser regression script is present."
                    if has_e2e
                    else "Add a browser regression script for primary learner journeys.",
                )
            )
            findings.append(
                _finding(
                    "static-script",
                    "pass" if has_static else "warn",
                    "Type, lint, or static quality script is present."
                    if has_static
                    else "Add a type, lint, or static quality command.",
                )
            )

            if (root / "package-lock.json").exists():
                suggested.append("npm ci")
            elif (root / "pnpm-lock.yaml").exists():
                suggested.append("pnpm install --frozen-lockfile")
            elif (root / "yarn.lock").exists():
                suggested.append("yarn install --frozen-lockfile")

            preferred_order = (
                "test:all",
                "test",
                "typecheck",
                "lint",
                "lint:terms",
                "e2e",
                "build",
                "preview",
            )
            for key in preferred_order:
                if key in scripts:
                    suggested.append(f"npm run {key}")

    deploy_documented = bool(readme and "deploy" in readme_text and ("build" in readme_text or not has_package))
    findings.append(
        _finding(
            "deployment-docs",
            "pass" if deploy_documented else "fail",
            "Deployment instructions are documented."
            if deploy_documented
            else "README must document how the course is built and deployed.",
        )
    )

    terminal_detected = any(marker in all_text for marker in ("terminal", "project shell", "browser-isolated"))
    terminal_tested = any(marker in test_text for marker in ("terminal", "shell", "command"))
    if terminal_detected:
        findings.append(
            _finding(
                "terminal-tests",
                "pass" if terminal_tested else "fail",
                "Terminal/tool behavior has automated coverage."
                if terminal_tested
                else "A terminal/tool surface exists without detected command-behavior tests.",
            )
        )

    persistence_detected = any(
        marker in all_text for marker in ("indexeddb", "dexie", "localstorage", "persist")
    )
    persistence_tested = any(
        marker in test_text for marker in ("reload", "persist", "indexeddb", "dexie", "localstorage")
    )
    if persistence_detected:
        findings.append(
            _finding(
                "persistence-tests",
                "pass" if persistence_tested else "fail",
                "Persistence/reload behavior has automated coverage."
                if persistence_tested
                else "Persistence is present without a detected reload or persistence test.",
            )
        )

    runbook_detected = "runbook" in all_text
    findings.append(
        _finding(
            "operational-handoff",
            "pass" if runbook_detected else "warn",
            "Runbook or operational handoff surface is present."
            if runbook_detected
            else "No runbook or operational handoff surface was detected.",
        )
    )

    if release:
        if package is None and has_index:
            artifact = root / "index.html"
        else:
            artifact = next((root / relative for relative in BUILD_OUTPUTS if (root / relative).is_file()), None)
        findings.append(
            _finding(
                "release-artifact",
                "pass" if artifact else "fail",
                f"Production entry artifact is present at {artifact.relative_to(root)}."
                if artifact
                else "No built production entry was found in dist/, build/, or out/.",
            )
        )

    return AuditReport(
        root=str(root),
        release=release,
        findings=findings,
        suggested_commands=list(dict.fromkeys(suggested)),
    )


def _print_human(report: AuditReport) -> None:
    print(f"Course baseline audit: {report.root}")
    print(f"Mode: {'release' if report.release else 'draft'}")
    print()
    for finding in report.findings:
        label = finding.status.upper().ljust(4)
        print(f"{label} [{finding.code}] {finding.message}")
        if finding.detail:
            print(f"     {finding.detail}")
    print()
    passes = sum(finding.status == "pass" for finding in report.findings)
    print(f"Summary: {passes} pass, {report.warnings} warning, {report.failures} fail")
    if report.suggested_commands:
        print("Suggested repository commands (not executed):")
        for command in report.suggested_commands:
            print(f"  {command}")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only structural audit for a course website or learning platform."
    )
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--release", action="store_true", help="Require a production entry artifact.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as a failing audit.")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    report = audit(args.project_root, release=args.release)
    if args.as_json:
        payload = asdict(report)
        payload["summary"] = {
            "failures": report.failures,
            "warnings": report.warnings,
            "passes": sum(finding.status == "pass" for finding in report.findings),
        }
        print(json.dumps(payload, indent=2))
    else:
        _print_human(report)
    return 1 if report.failures or (args.strict and report.warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
