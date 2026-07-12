#!/usr/bin/env python3
"""Read-only integrity checks for an Obsidian study-loop vault."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath


PROTOCOL_NAME = "STUDY-PROTOCOL.md"
SESSION_STATUSES = {"studying", "quizzed", "notes-written", "reviewed"}
HEADING_PATTERN = re.compile(r"^## (.+)$", flags=re.MULTILINE)
STUDY_CHECK_START = re.compile(
    r"<!-- study-check:start\s+id=([^\s>]+)[^>]*-->", flags=re.MULTILINE
)
STUDY_CHECK_END = re.compile(
    r"<!-- study-check:end\s+id=([^\s>]+)\s*-->", flags=re.MULTILINE
)
LEARNER_EDIT_START = re.compile(
    r"<!-- learner-edit:start\s+id=([^\s>]+)\s*-->", flags=re.MULTILINE
)
LEARNER_EDIT_END = re.compile(
    r"<!-- learner-edit:end\s+id=([^\s>]+)\s*-->", flags=re.MULTILINE
)
LEARNER_SOURCE = re.compile(
    r"<!-- learner-source:([^\s>]+)\s*-->", flags=re.MULTILINE
)
QUIZ_ATTEMPT_ID = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{2}$")
QUIZ_HEADING = re.compile(
    r"^Quiz progress — (?P<scope>.+?) — attempt (?P<attempt>[^\s]+)$"
)
ASSESSMENT_HEADING = re.compile(
    r"^Assessment — (?P<scope>.+?) — attempt (?P<attempt>[^\s]+)$"
)
QUIZ_RECORD = re.compile(
    r"^- (?P<question>Q[1-9]\d*) \[(?P<kind>[a-z][a-z0-9-]*)\] — "
    r"(?P<objective>.+?) — status: "
    r"(?P<status>planned|asked|scored|deferred)(?P<fields>.*)$",
    flags=re.MULTILINE,
)
QUIZ_FIELD = re.compile(
    r" — (?P<name>prompt|score|assistance|learner confidence|evidence|reason): "
)
CONSUMED_ATTEMPT = re.compile(
    r"^- Consumed by Assessment — (?P<scope>.+?) — attempt "
    r"(?P<attempt>[^\s]+) on (?P<timestamp>\S+)\s*$"
)
CONSUMED_LEGACY = re.compile(
    r"^- Consumed by Assessment — (?P<scope>.+?) on (?P<timestamp>\S+)\s*$"
)
ATTEMPT_STATUS = re.compile(
    r"^- Attempt status: (?P<status>active|paused|completed) — updated: "
    r"(?P<timestamp>\S+)\s*$"
)
BUDGET_RECORD = re.compile(
    r"^- Budget: minimum (?P<minimum>\d+); target (?P<target>\d+); "
    r"maximum (?P<maximum>\d+); mode adaptive\s*$"
)
ASSESSMENT_RECORD = re.compile(
    r"^- (?P<objective>.+?) — mastery: "
    r"(?P<mastery>solid \(recall-only\)|solid|partial|gap)(?P<fields>.*)$",
    flags=re.MULTILINE,
)
ASSESSMENT_FIELD = re.compile(
    r" — (?P<name>evidence question|score|assistance|evidence|tutor confidence|"
    r"learner confidence|calibration|review stage|next review|next action): "
)
SCORE_NOTATION = re.compile(
    r"^(?P<score>\d+)/(?P<denominator>\d+)(?P<applicable> applicable)?$"
)
LOCAL_ISO_DATETIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4}$"
)
RECALL_ONLY_KINDS = {
    "definition",
    "fill-in-the-blank",
    "free-production",
    "free-recall",
    "recall",
    "recognition",
    "term-definition",
}
APPLIED_KINDS = {
    "application",
    "applied",
    "classification",
    "compare-contrast",
    "discrimination",
    "lab",
    "scenario",
    "transfer",
}
QUESTION_KINDS = RECALL_ONLY_KINDS | APPLIED_KINDS
VISUAL_LABEL = "Visual review artifact - not an assessment"
FORBIDDEN_VISUAL_ELEMENTS = {
    "base",
    "embed",
    "form",
    "iframe",
    "input",
    "object",
    "select",
    "textarea",
}
URL_ATTRIBUTES = {"action", "cite", "formaction", "href", "poster", "src", "srcset"}
FORBIDDEN_SCRIPT_PATTERNS = {
    "network API": re.compile(
        r"\b(?:fetch|XMLHttpRequest|WebSocket|EventSource|sendBeacon)\b",
        flags=re.IGNORECASE,
    ),
    "persistent storage API": re.compile(
        r"\b(?:localStorage|sessionStorage|indexedDB|caches|document\.cookie)\b",
        flags=re.IGNORECASE,
    ),
    "device or clipboard API": re.compile(
        r"\b(?:geolocation|mediaDevices|clipboard\.write)\b",
        flags=re.IGNORECASE,
    ),
    "dynamic code execution": re.compile(
        r"\b(?:eval\s*\(|new\s+Function\s*\(|Function\s*\()",
        flags=re.IGNORECASE,
    ),
    "dynamic import": re.compile(r"\bimport\s*\(", flags=re.IGNORECASE),
}


class ValidationError(RuntimeError):
    """Expected user-facing validation failure."""


@dataclass(frozen=True)
class Issue:
    severity: str
    path: Path
    message: str


class VisualArtifactParser(HTMLParser):
    """Collect the small static surface needed for visual-artifact validation."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[tuple[str, dict[str, str | None]]] = []
        self.visible_text: list[str] = []
        self.script_text: list[str] = []
        self.style_text: list[str] = []
        self.ids: set[str] = set()
        self.fragments: list[str] = []
        self._script_depth = 0
        self._style_depth = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        normalized_tag = tag.lower()
        normalized_attrs = {name.lower(): value for name, value in attrs}
        self.elements.append((normalized_tag, normalized_attrs))
        element_id = normalized_attrs.get("id")
        if element_id:
            self.ids.add(element_id)
        href = normalized_attrs.get("href")
        if href and href.startswith("#") and len(href) > 1:
            self.fragments.append(href[1:])
        if normalized_tag == "script":
            self._script_depth += 1
        elif normalized_tag == "style":
            self._style_depth += 1

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() == "script":
            self._script_depth -= 1
        elif tag.lower() == "style":
            self._style_depth -= 1

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        if normalized_tag == "script" and self._script_depth:
            self._script_depth -= 1
        elif normalized_tag == "style" and self._style_depth:
            self._style_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._script_depth:
            self.script_text.append(data)
        elif self._style_depth:
            self.style_text.append(data)
        elif data.strip():
            self.visible_text.append(data.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate an Obsidian study-loop vault without modifying it."
    )
    parser.add_argument(
        "vault_path",
        nargs="?",
        default=".",
        help="Obsidian vault path. Defaults to the current directory.",
    )
    parser.add_argument(
        "--notes-dir",
        type=Path,
        help=(
            "Override the notes directory. Relative paths are resolved from the "
            "vault and must stay inside it."
        ),
    )
    return parser.parse_args()


def resolve_vault(path: str) -> Path:
    vault = Path(path).expanduser().resolve()
    if not vault.is_dir():
        raise ValidationError(f"Vault path is not a directory: {vault}")
    markers = [
        vault / PROTOCOL_NAME,
        vault / "_study" / "state.json",
        vault / ".obsidian",
    ]
    if not any(marker.exists() for marker in markers):
        raise ValidationError(
            "Target does not look like a study vault. Expected STUDY-PROTOCOL.md, "
            "_study/state.json, or .obsidian/."
        )
    return vault


def resolve_inside_vault(path: Path, vault: Path, label: str) -> Path:
    expanded = path.expanduser()
    if not expanded.is_absolute():
        expanded = vault / expanded
    resolved = expanded.resolve()
    if not resolved.is_relative_to(vault):
        raise ValidationError(f"{label} is outside the vault: {resolved}")
    return resolved


def display_path(path: Path, vault: Path) -> Path:
    try:
        return path.relative_to(vault)
    except ValueError:
        return path


def read_utf8(path: Path, issues: list[Issue]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        issues.append(Issue("ERROR", path, f"cannot read UTF-8 text: {exc}"))
        return None


def frontmatter(text: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    return text[4:end]


def frontmatter_value(block: str | None, key: str) -> str | None:
    if block is None:
        return None
    match = re.search(rf"^{re.escape(key)}:\s*(.*?)\s*$", block, flags=re.MULTILINE)
    return match.group(1) if match else None


def heading_group(title: str) -> int | None:
    if title == "Study content":
        return 1
    if title == "Unit progress":
        return 2
    if title.startswith("Quiz progress — "):
        return 3
    if title.startswith("Assessment — "):
        return 4
    if title.startswith("Notes written — "):
        return 5
    if title.startswith("Deep dive — "):
        return 6
    if title.startswith("Review — "):
        return 7
    if title == "Mastery evidence":
        return 8
    if title == "Session log":
        return 9
    return None


def heading_blocks(text: str) -> list[tuple[str, int, int]]:
    matches = list(HEADING_PATTERN.finditer(text))
    return [
        (
            match.group(1).strip(),
            match.start(),
            matches[index + 1].start() if index + 1 < len(matches) else len(text),
        )
        for index, match in enumerate(matches)
    ]


def quiz_heading_parts(title: str) -> tuple[str, str | None] | None:
    prefix = "Quiz progress — "
    if not title.startswith(prefix):
        return None
    match = QUIZ_HEADING.fullmatch(title)
    if match:
        return match.group("scope"), match.group("attempt")
    return title.removeprefix(prefix), None


def assessment_heading_parts(title: str) -> tuple[str, str | None] | None:
    prefix = "Assessment — "
    if not title.startswith(prefix):
        return None
    match = ASSESSMENT_HEADING.fullmatch(title)
    if match:
        return match.group("scope"), match.group("attempt")
    return title.removeprefix(prefix), None


def quiz_fields(raw: str) -> tuple[dict[str, str], str | None]:
    if not raw:
        return {}, None
    matches = list(QUIZ_FIELD.finditer(raw))
    if not matches or matches[0].start() != 0:
        return {}, "fields must use ` — <name>: <value>`"
    fields: dict[str, str] = {}
    for index, match in enumerate(matches):
        name = match.group("name")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
        value = raw[match.end() : end].strip()
        if name in fields:
            return {}, f"duplicate field: {name}"
        if not value:
            return {}, f"empty field: {name}"
        fields[name] = value
    return fields, None


def assessment_fields(
    raw: str,
) -> tuple[dict[str, str], list[str], str | None]:
    matches = list(ASSESSMENT_FIELD.finditer(raw))
    if not matches or matches[0].start() != 0:
        return {}, [], "fields must use ` — <name>: <value>`"
    fields: dict[str, str] = {}
    order: list[str] = []
    for index, match in enumerate(matches):
        name = match.group("name")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
        value = raw[match.end() : end].strip()
        if name in fields:
            return {}, [], f"duplicate field: {name}"
        if not value:
            return {}, [], f"empty field: {name}"
        fields[name] = value
        order.append(name)
    return fields, order, None


def validate_score_notation(
    path: Path,
    label: str,
    score_text: str,
    issues: list[Issue],
) -> tuple[int, int] | None:
    match = SCORE_NOTATION.fullmatch(score_text)
    if not match:
        issues.append(
            Issue(
                "ERROR",
                path,
                f"{label} has malformed score notation: {score_text}",
            )
        )
        return None
    score = int(match.group("score"))
    denominator = int(match.group("denominator"))
    applicable = match.group("applicable") is not None
    valid = True
    if denominator not in {2, 4, 6, 8} or score > denominator:
        issues.append(
            Issue("ERROR", path, f"{label} score is outside its denominator: {score_text}")
        )
        valid = False
    if denominator < 8 and not applicable:
        issues.append(
            Issue(
                "ERROR",
                path,
                f"{label} score below /8 must name its applicable denominator",
            )
        )
        valid = False
    if denominator == 8 and applicable:
        issues.append(
            Issue("ERROR", path, f"{label} full /8 score must not say applicable")
        )
        valid = False
    return (score, denominator) if valid else None


def validate_quiz_attempt(
    path: Path,
    title: str,
    scope: str,
    attempt_id: str,
    section: str,
    issues: list[Issue],
) -> tuple[bool, str | None, dict[str, tuple[str, str, str, str, str]]]:
    budget_lines = [line for line in section.splitlines() if line.startswith("- Budget:")]
    minimum_questions: int | None = None
    maximum_questions: int | None = None
    if len(budget_lines) != 1:
        issues.append(Issue("ERROR", path, f"{title} must have exactly one Budget record"))
    else:
        budget_match = BUDGET_RECORD.fullmatch(budget_lines[0])
        if budget_match is None:
            issues.append(Issue("ERROR", path, f"{title} has a malformed Budget record"))
        else:
            minimum_questions = int(budget_match.group("minimum"))
            target = int(budget_match.group("target"))
            maximum_questions = int(budget_match.group("maximum"))
            if not 1 <= minimum_questions <= target <= maximum_questions:
                issues.append(
                    Issue(
                        "ERROR",
                        path,
                        f"{title} Budget must satisfy 1 <= minimum <= target <= maximum",
                    )
                )

    status_lines = [
        line for line in section.splitlines() if line.startswith("- Attempt status:")
    ]
    attempt_status: str | None = None
    if len(status_lines) != 1:
        issues.append(
            Issue("ERROR", path, f"{title} must have exactly one Attempt status record")
        )
    else:
        status_match = ATTEMPT_STATUS.fullmatch(status_lines[0])
        if status_match is None:
            issues.append(Issue("ERROR", path, f"{title} has a malformed Attempt status"))
        else:
            attempt_status = status_match.group("status")
            if not LOCAL_ISO_DATETIME.fullmatch(status_match.group("timestamp")):
                issues.append(
                    Issue("ERROR", path, f"{title} Attempt status has a malformed timestamp")
                )

    record_matches = list(QUIZ_RECORD.finditer(section))
    record_lines = [line for line in section.splitlines() if line.startswith("- Q")]
    if not record_matches:
        issues.append(Issue("ERROR", path, f"{title} has no structured question records"))
    if len(record_lines) != len(record_matches):
        issues.append(Issue("ERROR", path, f"{title} has a malformed question record"))

    question_counts = Counter(match.group("question") for match in record_matches)
    for question, count in sorted(question_counts.items()):
        if count > 1:
            issues.append(
                Issue("ERROR", path, f"{title} has duplicate question record: {question}")
            )
    if maximum_questions is not None and len(question_counts) > maximum_questions:
        issues.append(
            Issue("ERROR", path, f"{title} has more question IDs than its maximum Budget")
        )
    if minimum_questions is not None and len(question_counts) < minimum_questions:
        issues.append(
            Issue("ERROR", path, f"{title} has fewer question IDs than its minimum Budget")
        )

    required_fields = {
        "planned": set(),
        "asked": {"prompt"},
        "scored": {"prompt", "score", "assistance", "learner confidence", "evidence"},
        "deferred": {"reason"},
    }
    allowed_fields = {
        "planned": set(),
        "asked": {"prompt"},
        "scored": {
            "prompt",
            "score",
            "assistance",
            "learner confidence",
            "evidence",
        },
        "deferred": {"prompt", "reason"},
    }
    question_evidence: dict[str, tuple[str, str, str, str, str]] = {}
    unresolved_questions: list[str] = []
    for match in record_matches:
        question = match.group("question")
        question_kind = match.group("kind")
        status = match.group("status")
        if question_kind not in QUESTION_KINDS:
            issues.append(
                Issue("ERROR", path, f"{question} has unsupported question kind: {question_kind}")
            )
        fields, field_error = quiz_fields(match.group("fields"))
        if field_error:
            issues.append(Issue("ERROR", path, f"{question} has malformed fields: {field_error}"))
            continue
        missing = required_fields[status] - set(fields)
        unexpected = set(fields) - allowed_fields[status]
        if missing:
            issues.append(
                Issue(
                    "ERROR",
                    path,
                    f"{question} status {status} is missing: {', '.join(sorted(missing))}",
                )
            )
        if unexpected:
            issues.append(
                Issue(
                    "ERROR",
                    path,
                    f"{question} status {status} has unexpected fields: "
                    f"{', '.join(sorted(unexpected))}",
                )
            )
        if status == "asked":
            issues.append(
                Issue("WARN", path, f"{title} has an asked-but-unscored question: {question}")
            )
        if status in {"planned", "asked"}:
            unresolved_questions.append(question)
        if status == "scored" and "score" in fields:
            validate_score_notation(path, question, fields["score"], issues)
            assistance = fields.get("assistance")
            if assistance not in {
                "none",
                "hint-1",
                "hint-2",
                "hint-3",
                "revealed",
            }:
                issues.append(
                    Issue("ERROR", path, f"{question} has unsupported assistance value")
                )
            elif "score" in fields:
                question_evidence[question] = (
                    match.group("objective"),
                    fields["score"],
                    assistance,
                    fields.get("learner confidence", ""),
                    question_kind,
                )
            if fields.get("learner confidence") not in {
                "Low",
                "Medium",
                "High",
                "unknown",
            }:
                issues.append(
                    Issue("ERROR", path, f"{question} has unsupported learner confidence")
                )

    consumed_lines = [
        line
        for line in section.splitlines()
        if line.startswith("- Consumed by Assessment —")
    ]
    if len(consumed_lines) > 1:
        issues.append(Issue("ERROR", path, f"{title} has multiple consumed records"))
    valid_consumed = False
    if consumed_lines:
        consumed = CONSUMED_ATTEMPT.fullmatch(consumed_lines[0])
        if consumed is None:
            issues.append(Issue("ERROR", path, f"{title} has a malformed consumed record"))
        else:
            valid_consumed = True
            if consumed.group("scope") != scope or consumed.group("attempt") != attempt_id:
                issues.append(
                    Issue("ERROR", path, f"{title} consumed record does not match its attempt")
                )
            if not LOCAL_ISO_DATETIME.fullmatch(consumed.group("timestamp")):
                issues.append(
                    Issue("ERROR", path, f"{title} consumed record has a malformed timestamp")
                )
        if unresolved_questions:
            issues.append(
                Issue(
                    "ERROR",
                    path,
                    f"{title} is consumed with unresolved questions: "
                    f"{', '.join(unresolved_questions)}",
                )
            )
    if valid_consumed and attempt_status != "completed":
        message = (
            f"{title} {attempt_status} attempt must remain unconsumed"
            if attempt_status in {"active", "paused"}
            else f"{title} is consumed but Attempt status is not completed"
        )
        issues.append(Issue("ERROR", path, message))
    return valid_consumed, attempt_status, question_evidence


def mastery_band(score: int, denominator: int) -> str:
    if score * 8 >= denominator * 7:
        return "solid"
    if score * 2 >= denominator:
        return "partial"
    return "gap"


def expected_calibration(mastery: str, learner_confidence: str) -> str:
    if learner_confidence == "unknown":
        return "unknown"
    expected_confidence = {
        "solid": "High",
        "solid (recall-only)": "High",
        "partial": "Medium",
        "gap": "Low",
    }[mastery]
    ranks = {"Low": 0, "Medium": 1, "High": 2}
    if ranks[learner_confidence] == ranks[expected_confidence]:
        return "well-calibrated"
    if ranks[learner_confidence] > ranks[expected_confidence]:
        return "overconfident"
    return "underconfident"


def validate_assessment_attempt(
    path: Path,
    title: str,
    section: str,
    quiz_evidence: dict[str, tuple[str, str, str, str, str]] | None,
    issues: list[Issue],
) -> None:
    matches = list(ASSESSMENT_RECORD.finditer(section))
    record_lines = [line for line in section.splitlines() if line.startswith("- ")]
    if not matches:
        issues.append(Issue("ERROR", path, f"{title} has no structured assessment records"))
    if len(matches) != len(record_lines):
        issues.append(Issue("ERROR", path, f"{title} has a malformed assessment record"))

    objective_counts = Counter(match.group("objective") for match in matches)
    for objective, count in sorted(objective_counts.items()):
        if count > 1:
            issues.append(
                Issue("ERROR", path, f"{title} has duplicate objective record: {objective}")
            )

    shared_order = [
        "evidence question",
        "score",
        "assistance",
        "evidence",
        "tutor confidence",
        "learner confidence",
        "calibration",
    ]
    for match in matches:
        objective = match.group("objective")
        mastery = match.group("mastery")
        fields, order, field_error = assessment_fields(match.group("fields"))
        if field_error:
            issues.append(
                Issue("ERROR", path, f"{objective} has malformed assessment fields: {field_error}")
            )
            continue
        expected_order = shared_order + (
            ["review stage", "next review"]
            if mastery.startswith("solid")
            else ["next action"]
        )
        if order != expected_order:
            issues.append(
                Issue(
                    "ERROR",
                    path,
                    f"{objective} assessment fields are missing, unexpected, or out of order",
                )
            )

        assistance = fields.get("assistance")
        assistance_values = {"none", "hint-1", "hint-2", "hint-3", "revealed"}
        if assistance not in assistance_values:
            issues.append(Issue("ERROR", path, f"{objective} has unsupported assistance"))
        if quiz_evidence is not None:
            evidence_question = fields.get("evidence question", "")
            selected_evidence = quiz_evidence.get(evidence_question)
            if selected_evidence is None:
                issues.append(
                    Issue(
                        "ERROR",
                        path,
                        f"{objective} evidence question is not a scored quiz record: "
                        f"{evidence_question or '<missing>'}",
                    )
                )
            else:
                (
                    quiz_objective,
                    quiz_score,
                    quiz_assistance,
                    quiz_learner_confidence,
                    quiz_kind,
                ) = selected_evidence
                if quiz_objective != objective:
                    issues.append(
                        Issue(
                            "ERROR",
                            path,
                            f"{objective} evidence question belongs to {quiz_objective}",
                        )
                    )
                if fields.get("score") != quiz_score:
                    issues.append(
                        Issue(
                            "ERROR",
                            path,
                            f"{objective} score must match {evidence_question}: {quiz_score}",
                        )
                    )
                if assistance != quiz_assistance:
                    issues.append(
                        Issue(
                            "ERROR",
                            path,
                            f"{objective} assistance must match {evidence_question}: "
                            f"{quiz_assistance}",
                        )
                    )
                if fields.get("learner confidence") != quiz_learner_confidence:
                    issues.append(
                        Issue(
                            "ERROR",
                            path,
                            f"{objective} learner confidence must match "
                            f"{evidence_question}: {quiz_learner_confidence}",
                        )
                    )
                if mastery == "solid" and quiz_kind in RECALL_ONLY_KINDS:
                    issues.append(
                        Issue(
                            "ERROR",
                            path,
                            f"{objective} solid {quiz_kind} evidence must be recall-only",
                        )
                    )
                if mastery == "solid (recall-only)" and quiz_kind not in RECALL_ONLY_KINDS:
                    issues.append(
                        Issue(
                            "ERROR",
                            path,
                            f"{objective} {quiz_kind} evidence cannot be recall-only",
                        )
                    )

        parsed_score = None
        if "score" in fields:
            parsed_score = validate_score_notation(
                path, objective, fields["score"], issues
            )
        if parsed_score is not None:
            score, denominator = parsed_score
            numeric_mastery = mastery_band(score, denominator)
            expected_mastery = (
                "partial"
                if assistance in assistance_values - {"none"} and numeric_mastery == "solid"
                else numeric_mastery
            )
            recorded_band = "solid" if mastery.startswith("solid") else mastery
            if recorded_band != expected_mastery:
                issues.append(
                    Issue(
                        "ERROR",
                        path,
                        f"{objective} mastery {mastery} does not match score {fields['score']}",
                    )
                )
            if mastery == "solid (recall-only)" and denominator == 8:
                issues.append(
                    Issue(
                        "ERROR",
                        path,
                        f"{objective} recall-only mastery must use an applicable denominator",
                    )
                )

        tutor_confidence = fields.get("tutor confidence")
        if tutor_confidence not in {"low", "medium", "high"}:
            issues.append(
                Issue("ERROR", path, f"{objective} has unsupported tutor confidence")
            )
        if mastery == "solid (recall-only)" and tutor_confidence == "high":
            issues.append(
                Issue("ERROR", path, f"{objective} recall-only tutor confidence exceeds medium")
            )

        learner_confidence = fields.get("learner confidence")
        if learner_confidence not in {"Low", "Medium", "High", "unknown"}:
            issues.append(
                Issue("ERROR", path, f"{objective} has unsupported learner confidence")
            )
        calibration = fields.get("calibration")
        if calibration not in {
            "well-calibrated",
            "overconfident",
            "underconfident",
            "unknown",
        }:
            issues.append(Issue("ERROR", path, f"{objective} has unsupported calibration"))
        if learner_confidence in {"Low", "Medium", "High", "unknown"}:
            expected = expected_calibration(mastery, learner_confidence)
            if calibration != expected:
                issues.append(
                    Issue(
                        "ERROR",
                        path,
                        f"{objective} calibration must be {expected}, not {calibration}",
                    )
                )

        if mastery.startswith("solid"):
            if fields.get("review stage") not in {"1", "2", "3", "4", "5"}:
                issues.append(Issue("ERROR", path, f"{objective} has invalid review stage"))
            next_review = fields.get("next review", "")
            try:
                date.fromisoformat(next_review)
            except ValueError:
                issues.append(Issue("ERROR", path, f"{objective} has invalid next review date"))


def validate_session(path: Path, vault: Path, issues: list[Issue]) -> None:
    if path.is_symlink():
        try:
            if not path.resolve().is_relative_to(vault / "_study" / "sessions"):
                issues.append(Issue("ERROR", path, "session symlink resolves outside the vault"))
                return
        except (OSError, RuntimeError) as exc:
            issues.append(Issue("ERROR", path, f"session symlink is unsafe: {exc}"))
            return
    text = read_utf8(path, issues)
    if text is None:
        return
    block = frontmatter(text)
    if block is None:
        issues.append(Issue("ERROR", path, "missing or unterminated frontmatter"))
    else:
        for key in ("topic", "created", "status", "objectives"):
            if not re.search(rf"^{key}:\s*", block, flags=re.MULTILINE):
                issues.append(Issue("ERROR", path, f"frontmatter is missing {key}"))
        status = frontmatter_value(block, "status")
        if status is not None and status not in SESSION_STATUSES:
            issues.append(Issue("ERROR", path, f"unsupported session status: {status}"))

    headings = heading_blocks(text)
    titles = [title for title, _, _ in headings]
    for title, count in Counter(titles).items():
        if count > 1:
            issues.append(Issue("ERROR", path, f"duplicate H2 heading: {title}"))

    if titles.count("Session log") != 1:
        issues.append(Issue("ERROR", path, "must contain exactly one ## Session log"))
    elif titles[-1] != "Session log":
        issues.append(Issue("ERROR", path, "## Session log must be the final H2"))

    previous_group = 0
    for title in titles:
        group = heading_group(title)
        if group is None:
            issues.append(Issue("WARN", path, f"unrecognized session H2: {title}"))
            continue
        if group < previous_group:
            issues.append(
                Issue("ERROR", path, f"heading is outside canonical group order: {title}")
            )
        previous_group = max(previous_group, group)

    quiz_attempts: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    assessment_attempts: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    quiz_id_locations: dict[str, list[str]] = defaultdict(list)
    assessment_id_locations: dict[str, list[str]] = defaultdict(list)
    legacy_quizzes: list[tuple[str, str, str]] = []
    for title, start, end in headings:
        section = text[start:end]
        quiz_parts = quiz_heading_parts(title)
        if quiz_parts is not None:
            scope, attempt_id = quiz_parts
            malformed = (
                re.search(r" — attempt(?:\s|$)", title) is not None
                and attempt_id is None
            )
            if malformed:
                issues.append(
                    Issue("ERROR", path, f"malformed quiz attempt heading: {title}")
                )
            elif attempt_id is None:
                legacy_quizzes.append((title, scope, section))
            else:
                quiz_attempts[(scope, attempt_id)].append((title, section))
                quiz_id_locations[attempt_id].append(title)
                if not QUIZ_ATTEMPT_ID.fullmatch(attempt_id):
                    issues.append(
                        Issue("ERROR", path, f"malformed quiz attempt id: {attempt_id}")
                    )
            continue

        assessment_parts = assessment_heading_parts(title)
        if assessment_parts is not None:
            scope, attempt_id = assessment_parts
            malformed = (
                re.search(r" — attempt(?:\s|$)", title) is not None
                and attempt_id is None
            )
            if malformed:
                issues.append(
                    Issue("ERROR", path, f"malformed assessment attempt heading: {title}")
                )
            elif attempt_id is not None:
                assessment_attempts[(scope, attempt_id)].append((title, section))
                assessment_id_locations[attempt_id].append(title)
                if not QUIZ_ATTEMPT_ID.fullmatch(attempt_id):
                    issues.append(
                        Issue(
                            "ERROR", path, f"malformed assessment attempt id: {attempt_id}"
                        )
                    )

    quiz_results: dict[
        tuple[str, str],
        list[tuple[bool, str | None, dict[str, tuple[str, str, str, str, str]]]],
    ] = defaultdict(list)
    for key, attempts in quiz_attempts.items():
        scope, attempt_id = key
        for title, section in attempts:
            consumed, attempt_status, question_evidence = validate_quiz_attempt(
                path, title, scope, attempt_id, section, issues
            )
            quiz_results[key].append(
                (consumed, attempt_status, question_evidence)
            )
            if not consumed:
                status_label = attempt_status or "unknown"
                issues.append(
                    Issue(
                        "WARN",
                        path,
                        f"unconsumed {title} (Attempt status: {status_label})",
                    )
                )

    for title, scope, section in legacy_quizzes:
        consumed_lines = [
            line
            for line in section.splitlines()
            if line.startswith("- Consumed by Assessment —")
        ]
        valid = [
            match
            for line in consumed_lines
            if (match := CONSUMED_LEGACY.fullmatch(line)) is not None
            and match.group("scope") == scope
        ]
        if len(consumed_lines) > 1:
            issues.append(Issue("ERROR", path, f"{title} has multiple consumed records"))
        if consumed_lines and not valid:
            issues.append(Issue("ERROR", path, f"{title} has a malformed consumed record"))
        if not valid:
            issues.append(Issue("WARN", path, f"unconsumed {title}"))

    for key, assessments in assessment_attempts.items():
        matching_quizzes = quiz_results.get(key, [])
        quiz_evidence = matching_quizzes[0][2] if len(matching_quizzes) == 1 else None
        for title, section in assessments:
            validate_assessment_attempt(
                path, title, section, quiz_evidence, issues
            )
        if len(matching_quizzes) != 1:
            issues.append(
                Issue(
                    "ERROR",
                    path,
                    f"{assessments[0][0]} must link to exactly one quiz attempt",
                )
            )
        elif not matching_quizzes[0][0]:
            issues.append(
                Issue("ERROR", path, f"{assessments[0][0]} links to an unconsumed quiz attempt")
            )

    for key, results in quiz_results.items():
        for consumed, _, _ in results:
            if consumed and len(assessment_attempts.get(key, [])) != 1:
                title = quiz_attempts[key][0][0]
                issues.append(
                    Issue("ERROR", path, f"{title} must link to exactly one assessment")
                )

    for attempt_id, attempt_titles in sorted(quiz_id_locations.items()):
        if len(attempt_titles) > 1:
            issues.append(
                Issue(
                    "ERROR",
                    path,
                    f"duplicate quiz attempt id {attempt_id}: {', '.join(attempt_titles)}",
                )
            )
    for attempt_id, attempt_titles in sorted(assessment_id_locations.items()):
        if len(attempt_titles) > 1:
            issues.append(
                Issue(
                    "ERROR",
                    path,
                    f"duplicate assessment attempt id {attempt_id}: "
                    f"{', '.join(attempt_titles)}",
                )
            )

    for logged in re.findall(r"Wrote `([^`]+\.md)`", text):
        relative = PurePosixPath(logged)
        if relative.is_absolute() or ".." in relative.parts:
            issues.append(Issue("ERROR", path, f"unsafe logged note path: {logged}"))
            continue
        note_path = vault.joinpath(*relative.parts)
        if not note_path.exists():
            issues.append(Issue("ERROR", path, f"logged note does not exist: {logged}"))
        else:
            try:
                resolved_note = note_path.resolve()
            except (OSError, RuntimeError) as exc:
                issues.append(Issue("ERROR", path, f"logged note path is unsafe: {exc}"))
                continue
            if not resolved_note.is_relative_to(vault):
                issues.append(
                    Issue("ERROR", path, f"logged note resolves outside vault: {logged}")
                )


def marker_counts(
    path: Path,
    starts: re.Pattern[str],
    ends: re.Pattern[str],
    text: str,
    label: str,
    issues: list[Issue],
) -> None:
    start_counts = Counter(starts.findall(text))
    end_counts = Counter(ends.findall(text))
    for marker_id in sorted(set(start_counts) | set(end_counts)):
        if start_counts[marker_id] != 1 or end_counts[marker_id] != 1:
            issues.append(
                Issue(
                    "ERROR",
                    path,
                    f"{label} {marker_id} must have exactly one start and one end marker",
                )
            )
            continue
        matching_start = next(
            match for match in starts.finditer(text) if match.group(1) == marker_id
        )
        matching_end = next(match for match in ends.finditer(text) if match.group(1) == marker_id)
        if matching_end.start() < matching_start.end():
            issues.append(Issue("ERROR", path, f"{label} {marker_id} ends before it starts"))


def study_check_blocks(text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    for start in STUDY_CHECK_START.finditer(text):
        marker_id = start.group(1)
        closing = next(
            (
                match
                for match in STUDY_CHECK_END.finditer(text, start.end())
                if match.group(1) == marker_id
            ),
            None,
        )
        if closing is not None:
            blocks.append((marker_id, text[start.start() : closing.end()]))
    return blocks


def learner_edit_blocks(text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    for start in LEARNER_EDIT_START.finditer(text):
        marker_id = start.group(1)
        closing = next(
            (
                match
                for match in LEARNER_EDIT_END.finditer(text, start.end())
                if match.group(1) == marker_id
            ),
            None,
        )
        if closing is not None:
            blocks.append((marker_id, text[start.start() : closing.end()]))
    return blocks


def gap_response(block: str) -> str:
    structured = re.search(
        r"<!-- learner-answer:gap-response\s*-->\s*\n(.*?)"
        r"(?=\n<!-- learner-source:|\n<!-- learner-edit:end)",
        block,
        flags=re.DOTALL,
    )
    if structured:
        return structured.group(1).strip()
    body = LEARNER_EDIT_START.sub("", block)
    body = LEARNER_EDIT_END.sub("", body)
    body = re.sub(
        r"<!-- learner-source:[^>]+-->\s*\n- \*\*Source:\*\*[^\n]*",
        "",
        body,
    )
    body = re.sub(r"<!-- learner-answer:[^>]+-->", "", body)
    return body.strip()


def validate_gap_sources(
    path: Path,
    status: str | None,
    text: str,
    issues: list[Issue],
) -> None:
    local_source_counts: Counter[str] = Counter()
    gap_ids: set[str] = set()
    for marker_id, edit_block in learner_edit_blocks(text):
        if not marker_id.startswith("gap-"):
            continue
        gap_ids.add(marker_id)
        source_markers = LEARNER_SOURCE.findall(edit_block)
        local_source_counts.update(source_markers)
        if not source_markers:
            issues.append(
                Issue("WARN", path, f"gap is missing learner source marker: {marker_id}")
            )
        elif len(source_markers) > 1:
            issues.append(
                Issue("ERROR", path, f"gap has duplicate source markers: {marker_id}")
            )
        elif source_markers[0] != marker_id:
            issues.append(
                Issue(
                    "ERROR",
                    path,
                    f"learner source marker {source_markers[0]} does not match {marker_id}",
                )
            )
        else:
            source = re.search(
                rf"<!-- learner-source:{re.escape(marker_id)}\s*-->\s*\n"
                r"- \*\*Source:\*\*\s*(.*)$",
                edit_block,
                flags=re.MULTILINE,
            )
            if source is None or source.group(1).strip() in {"", "Write here."}:
                issues.append(
                    Issue("WARN", path, f"gap has no learner source value: {marker_id}")
                )

        response = gap_response(edit_block)
        answered = bool(response and response != "Write here.")
        if status == "reviewed" and not answered:
            issues.append(Issue("ERROR", path, "reviewed note still contains a pending gap"))

    global_source_counts = Counter(LEARNER_SOURCE.findall(text))
    for source_id, count in sorted(global_source_counts.items()):
        if count > 1:
            issues.append(
                Issue("ERROR", path, f"duplicate learner source marker: {source_id}")
            )
        orphaned = count - local_source_counts[source_id]
        if source_id not in gap_ids or orphaned > 0:
            issues.append(
                Issue("ERROR", path, f"orphan learner source marker: {source_id}")
            )


def check_is_answered(block: str) -> bool:
    if re.search(r"^- \[[xX]\] ", block, flags=re.MULTILINE):
        return True
    answer_lines = re.findall(
        r"<!-- learner-answer:[^>]+ -->\s*\n([^\n]+)", block, flags=re.MULTILINE
    )
    return any("Write here." not in line for line in answer_lines)


def validate_note(
    path: Path,
    vault: Path,
    issues: list[Issue],
    check_locations: dict[str, list[Path]],
) -> None:
    if path.is_symlink():
        try:
            if not path.resolve().is_relative_to(vault):
                issues.append(Issue("ERROR", path, "note symlink resolves outside the vault"))
                return
        except (OSError, RuntimeError) as exc:
            issues.append(Issue("ERROR", path, f"note symlink is unsafe: {exc}"))
            return
    text = read_utf8(path, issues)
    if text is None:
        return
    block = frontmatter(text)
    status = frontmatter_value(block, "status")
    marker_counts(path, STUDY_CHECK_START, STUDY_CHECK_END, text, "study-check", issues)
    marker_counts(path, LEARNER_EDIT_START, LEARNER_EDIT_END, text, "learner-edit", issues)

    fence_lines = sum(
        1 for line in text.splitlines() if line.lstrip().startswith("```")
    )
    if fence_lines % 2 == 1:
        issues.append(Issue("ERROR", path, "unbalanced code fences"))

    for marker_id, check_block in study_check_blocks(text):
        check_locations[marker_id].append(path)
        answered = check_is_answered(check_block)
        reviewed = "**Review —" in check_block
        if answered and not reviewed:
            severity = "ERROR" if status == "reviewed" else "WARN"
            issues.append(
                Issue(severity, path, f"answered study-check has no review: {marker_id}")
            )

    validate_gap_sources(path, status, text, issues)
    if status == "reviewed" and "RESEARCH NEEDED" in text:
        issues.append(Issue("ERROR", path, "reviewed note still says RESEARCH NEEDED"))


def visual_meta(
    elements: list[tuple[str, dict[str, str | None]]], name: str
) -> str | None:
    for tag, attrs in elements:
        if tag != "meta":
            continue
        if (attrs.get("name") or "").lower() == name.lower():
            return attrs.get("content")
    return None


def visual_csp(
    elements: list[tuple[str, dict[str, str | None]]]
) -> str | None:
    for tag, attrs in elements:
        if tag != "meta":
            continue
        if (attrs.get("http-equiv") or "").lower() == "content-security-policy":
            return attrs.get("content")
    return None


def allowed_local_url(value: str) -> bool:
    stripped = value.strip()
    return (
        not stripped
        or stripped == "#"
        or stripped.startswith("#")
        or stripped.lower().startswith("data:image/")
    )


def validate_visual_artifact(
    path: Path,
    vault: Path,
    issues: list[Issue],
    visuals_root: Path | None = None,
) -> None:
    configured_root = visuals_root or vault / "_study" / "visuals"
    try:
        resolved_vault = vault.resolve()
        resolved_root = configured_root.resolve()
        resolved_path = path.resolve()
    except (OSError, RuntimeError) as exc:
        issues.append(Issue("ERROR", path, f"visual artifact path is unsafe: {exc}"))
        return
    if not resolved_root.is_relative_to(resolved_vault):
        issues.append(Issue("ERROR", configured_root, "visuals root resolves outside the vault"))
        return
    if not resolved_path.is_relative_to(resolved_root):
        issues.append(Issue("ERROR", path, "visual artifact resolves outside _study/visuals"))
        return

    text = read_utf8(path, issues)
    if text is None:
        return
    parser = VisualArtifactParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception as exc:  # HTMLParser surfaces malformed entities as ValueError.
        issues.append(Issue("ERROR", path, f"cannot parse HTML: {exc}"))
        return

    elements = parser.elements
    visible_text = " ".join(parser.visible_text)
    tags = [tag for tag, _ in elements]
    if VISUAL_LABEL not in visible_text:
        issues.append(Issue("ERROR", path, f"missing visible label: {VISUAL_LABEL}"))

    html_attrs = next((attrs for tag, attrs in elements if tag == "html"), {})
    if not html_attrs.get("lang"):
        issues.append(Issue("ERROR", path, "html element is missing lang"))
    if "main" not in tags:
        issues.append(Issue("ERROR", path, "missing main landmark"))
    if tags.count("h1") != 1:
        issues.append(Issue("ERROR", path, "must contain exactly one h1"))

    charset_present = any(
        tag == "meta" and bool(attrs.get("charset")) for tag, attrs in elements
    )
    if not charset_present:
        issues.append(Issue("ERROR", path, "missing meta charset"))
    if not visual_meta(elements, "viewport"):
        issues.append(Issue("ERROR", path, "missing viewport metadata"))
    if (visual_meta(elements, "referrer") or "").lower() != "no-referrer":
        issues.append(Issue("ERROR", path, "referrer policy must be no-referrer"))
    for field in ("study-source", "study-scope", "study-generated", "study-visual-version"):
        if not visual_meta(elements, field):
            issues.append(Issue("ERROR", path, f"missing {field} metadata"))

    source = visual_meta(elements, "study-source")
    if source:
        relative_source = PurePosixPath(source)
        raw_parts = source.split("/")
        unsafe_source = (
            source != source.strip()
            or relative_source.is_absolute()
            or any(part in {"", ".", ".."} for part in raw_parts)
            or "\\" in source
            or "://" in source
            or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", source) is not None
        )
        if unsafe_source:
            issues.append(Issue("ERROR", path, f"unsafe study-source path: {source}"))
        else:
            source_path = resolved_vault.joinpath(*relative_source.parts)
            try:
                resolved_source = source_path.resolve()
            except (OSError, RuntimeError) as exc:
                issues.append(Issue("ERROR", path, f"study-source path is unsafe: {exc}"))
            else:
                if not resolved_source.is_relative_to(resolved_vault):
                    issues.append(
                        Issue("ERROR", path, f"study-source resolves outside vault: {source}")
                    )
                elif not source_path.is_file():
                    issues.append(
                        Issue(
                            "ERROR",
                            path,
                            f"study-source is not an existing regular file: {source}",
                        )
                    )

    csp = visual_csp(elements)
    required_csp = (
        "default-src 'none'",
        "connect-src 'none'",
        "form-action 'none'",
        "base-uri 'none'",
    )
    if csp is None:
        issues.append(Issue("ERROR", path, "missing Content-Security-Policy metadata"))
    else:
        csp_normalized = " ".join(csp.split()).lower()
        for directive in required_csp:
            if directive not in csp_normalized:
                issues.append(Issue("ERROR", path, f"CSP is missing {directive}"))
        if "*" in csp:
            issues.append(Issue("ERROR", path, "CSP must not contain a wildcard source"))

    for tag, attrs in elements:
        if tag in FORBIDDEN_VISUAL_ELEMENTS:
            issues.append(Issue("ERROR", path, f"forbidden element: {tag}"))
        if tag == "script" and attrs.get("src"):
            issues.append(Issue("ERROR", path, "external script source is forbidden"))
        if tag == "script" and (attrs.get("type") or "").lower() == "module":
            issues.append(Issue("ERROR", path, "module scripts are not file-URL portable"))
        for name, value in attrs.items():
            if name.startswith("on"):
                issues.append(Issue("ERROR", path, f"inline event handler is forbidden: {name}"))
            if name in URL_ATTRIBUTES and value is not None:
                values = value.split(",") if name == "srcset" else [value]
                if any(not allowed_local_url(item.strip().split()[0]) for item in values if item.strip()):
                    issues.append(Issue("ERROR", path, f"non-local {name} reference: {value}"))
        if tag == "svg":
            has_name = bool(attrs.get("aria-label") or attrs.get("aria-labelledby"))
            decorative = (attrs.get("aria-hidden") or "").lower() == "true"
            if not has_name and not decorative:
                issues.append(
                    Issue(
                        "ERROR",
                        path,
                        "svg must have an accessible name or aria-hidden=true",
                    )
                )

    for fragment in parser.fragments:
        if fragment not in parser.ids:
            issues.append(Issue("ERROR", path, f"fragment target does not exist: #{fragment}"))

    scripts = "\n".join(parser.script_text)
    for label, pattern in FORBIDDEN_SCRIPT_PATTERNS.items():
        if pattern.search(scripts):
            issues.append(Issue("ERROR", path, f"forbidden {label} in inline script"))

    styles = "\n".join(parser.style_text)
    if re.search(r"@import\b", styles, flags=re.IGNORECASE):
        issues.append(Issue("ERROR", path, "CSS @import is forbidden"))
    for match in re.finditer(r"url\(([^)]+)\)", styles, flags=re.IGNORECASE):
        target = match.group(1).strip(" \t\r\n\"'")
        if not allowed_local_url(target):
            issues.append(Issue("ERROR", path, f"non-local CSS url reference: {target}"))
    if ("animation" in styles or "transition" in styles) and not re.search(
        r"prefers-reduced-motion\s*:\s*reduce", styles, flags=re.IGNORECASE
    ):
        issues.append(Issue("ERROR", path, "motion is present without a reduced-motion override"))
    if any(tag in {"a", "button", "details", "summary"} for tag in tags) and ":focus-visible" not in styles:
        issues.append(Issue("ERROR", path, "interactive content lacks a focus-visible style"))


def validate_state(vault: Path, issues: list[Issue]) -> None:
    path = vault / "_study" / "state.json"
    if not path.exists():
        issues.append(Issue("ERROR", path, "missing study state file"))
        return
    if path.is_symlink():
        try:
            if not path.resolve().is_relative_to(vault):
                issues.append(
                    Issue("ERROR", path, "state file symlink resolves outside the vault")
                )
                return
        except (OSError, RuntimeError) as exc:
            issues.append(Issue("ERROR", path, f"state file symlink is unsafe: {exc}"))
            return
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        issues.append(Issue("ERROR", path, f"invalid UTF-8 JSON: {exc}"))
        return
    if not isinstance(state, dict) or set(state) != {"active_session"}:
        issues.append(Issue("ERROR", path, "must contain exactly the active_session key"))
        return
    active = state["active_session"]
    if active is None:
        return
    if not isinstance(active, str) or not active:
        issues.append(Issue("ERROR", path, "active_session must be a string or null"))
        return
    relative = PurePosixPath(active)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or relative.parts[:2] != ("_study", "sessions")
        or relative.suffix != ".md"
    ):
        issues.append(
            Issue(
                "ERROR",
                path,
                "active_session must be a vault-relative Markdown path under _study/sessions/",
            )
        )
        return
    session = vault.joinpath(*relative.parts)
    if not session.exists():
        issues.append(Issue("ERROR", path, f"active session does not exist: {active}"))
    elif not session.is_file():
        issues.append(Issue("ERROR", path, f"active session is not a regular file: {active}"))
    else:
        try:
            resolved_session = session.resolve()
        except (OSError, RuntimeError) as exc:
            issues.append(Issue("ERROR", path, f"active session is unsafe: {exc}"))
            return
        if not resolved_session.is_relative_to(vault / "_study" / "sessions"):
            issues.append(Issue("ERROR", path, "active session resolves outside _study/sessions/"))


def notes_dir_from_protocol(vault: Path, override: Path | None) -> Path:
    if override is not None:
        return resolve_inside_vault(override, vault, "Notes directory")
    protocol = vault / PROTOCOL_NAME
    if protocol.exists():
        if protocol.is_symlink():
            try:
                if not protocol.resolve().is_relative_to(vault):
                    raise ValidationError("STUDY-PROTOCOL.md is a symlink outside the vault")
            except (OSError, RuntimeError) as exc:
                raise ValidationError(f"STUDY-PROTOCOL.md symlink is unsafe: {exc}") from exc
        text = protocol.read_text(encoding="utf-8")
        match = re.search(r"^- `NOTES_DIR`: `([^`]+)`", text, flags=re.MULTILINE)
        if match:
            return resolve_inside_vault(Path(match.group(1)), vault, "NOTES_DIR")
    return (vault / "Notes").resolve()


def validate_vault(vault: Path, notes_dir: Path) -> list[Issue]:
    issues: list[Issue] = []
    validate_state(vault, issues)

    sessions_dir = vault / "_study" / "sessions"
    if not sessions_dir.is_dir():
        issues.append(Issue("ERROR", sessions_dir, "missing sessions directory"))
    else:
        for session in sorted(sessions_dir.glob("*.md")):
            validate_session(session, vault, issues)

    check_locations: dict[str, list[Path]] = defaultdict(list)
    if not notes_dir.is_dir():
        issues.append(Issue("WARN", notes_dir, "notes directory does not exist"))
    else:
        for note in sorted(notes_dir.rglob("*.md")):
            validate_note(note, vault, issues, check_locations)
    for marker_id, paths in sorted(check_locations.items()):
        unique = sorted(set(paths))
        if len(unique) > 1:
            locations = ", ".join(str(display_path(path, vault)) for path in unique)
            issues.append(
                Issue("ERROR", vault, f"duplicate study-check id {marker_id}: {locations}")
            )

    visuals_dir = vault / "_study" / "visuals"
    try:
        resolved_vault = vault.resolve()
        resolved_visuals = visuals_dir.resolve()
    except (OSError, RuntimeError) as exc:
        issues.append(Issue("ERROR", visuals_dir, f"visuals path is unsafe: {exc}"))
        return issues
    if (visuals_dir.exists() or visuals_dir.is_symlink()) and not resolved_visuals.is_relative_to(
        resolved_vault
    ):
        issues.append(Issue("ERROR", visuals_dir, "visuals root resolves outside the vault"))
    elif visuals_dir.is_symlink() and not visuals_dir.exists():
        issues.append(Issue("ERROR", visuals_dir, "visuals root symlink target does not exist"))
    elif visuals_dir.exists() and not visuals_dir.is_dir():
        issues.append(Issue("ERROR", visuals_dir, "visuals path is not a directory"))
    elif visuals_dir.is_dir():
        for artifact in sorted(visuals_dir.glob("*.html")):
            validate_visual_artifact(artifact, vault, issues, resolved_visuals)
    return issues


def main() -> int:
    args = parse_args()
    try:
        vault = resolve_vault(args.vault_path)
        notes_dir = notes_dir_from_protocol(vault, args.notes_dir)
        issues = validate_vault(vault, notes_dir)
    except (ValidationError, OSError, UnicodeDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    for issue in issues:
        print(f"{issue.severity}: {display_path(issue.path, vault)}: {issue.message}")
    errors = sum(issue.severity == "ERROR" for issue in issues)
    warnings = sum(issue.severity == "WARN" for issue in issues)
    if errors:
        print(f"FAILED: {errors} error(s), {warnings} warning(s).")
        return 1
    print(f"OK: no integrity errors; {warnings} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
