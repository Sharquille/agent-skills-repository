#!/usr/bin/env python3
"""Build a deterministic Anki TSV import from a study-loop manifest."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import tempfile
from pathlib import Path, PurePosixPath

from anki_quality import quality_errors


ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._:-]*$")
CARD_TYPES = {"basic", "typed", "mcq"}
CARD_STATUSES = {"active", "retired"}
CARD_FIELDS = {
    "id",
    "objective",
    "type",
    "prompt",
    "answer",
    "source",
    "revision",
    "status",
    "tags",
}


MCQ_NOTETYPE = "Study MCQ"
MCQ_CHOICES = 4
NOT_A_CHOICE = re.compile(r"(?i)\b(all|none|both|neither) of the (above|options|choices)\b")


class ManifestError(RuntimeError):
    """A user-facing manifest validation failure."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--vault", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def scalar(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{label} must be a non-empty string")
    if "\t" in value or "\r" in value or "\n" in value:
        raise ManifestError(f"{label} must not contain tabs or newlines")
    return value.strip()


def safe_source(value: object, label: str, vault: Path) -> str:
    source = scalar(value, label)
    if source.count("#") != 1:
        raise ManifestError(f"{label} must be a Markdown path plus one heading anchor")
    raw_path, heading = source.split("#", 1)
    relative = PurePosixPath(raw_path)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or relative.suffix.lower() != ".md"
        or not heading.strip()
    ):
        raise ManifestError(
            f"{label} must stay inside the vault and end in .md#Heading"
        )
    candidate = vault.joinpath(*relative.parts)
    try:
        resolved = candidate.resolve()
    except (OSError, RuntimeError) as exc:
        raise ManifestError(f"{label} cannot be resolved safely: {exc}") from exc
    if not resolved.is_relative_to(vault) or not resolved.is_file():
        raise ManifestError(f"{label} does not resolve to a vault-local note")
    try:
        note_text = resolved.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ManifestError(f"{label} note cannot be read: {exc}") from exc
    headings: list[str] = []
    fence_character = ""
    fence_length = 0
    for line in note_text.splitlines():
        stripped = line.lstrip()
        fence = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence:
            marker = fence.group(1)
            if not fence_character:
                fence_character = marker[0]
                fence_length = len(marker)
            elif marker[0] == fence_character and len(marker) >= fence_length:
                fence_character = ""
                fence_length = 0
            continue
        if fence_character:
            continue
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            headings.append(re.sub(r"\s+#+\s*$", "", match.group(1)).strip())
    occurrences = headings.count(heading.strip())
    if occurrences == 0:
        raise ManifestError(f"{label} heading does not exist: {heading.strip()}")
    if occurrences > 1:
        raise ManifestError(f"{label} heading is ambiguous: {heading.strip()}")
    return source


def html_field(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{label} must be a non-empty string")
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    if "\t" in normalized:
        raise ManifestError(f"{label} must not contain tabs")
    return html.escape(normalized.strip()).replace("\n", "<br>")


def load_manifest(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read manifest: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError("manifest root must be an object")
    expected = {
        "schema",
        "version",
        "chapter_id",
        "deck",
        "notetype",
        "objectives",
        "cards",
    }
    # Optional: objectives dropped from study on purpose; their cards must all be retired.
    if set(data) - {"retired_objectives"} != expected:
        raise ManifestError(
            "manifest fields must be exactly: " + ", ".join(sorted(expected))
            + " (plus optional retired_objectives)"
        )
    if data["schema"] != "anki-study-sync.manifest":
        raise ManifestError("schema must be anki-study-sync.manifest")
    if data["version"] != 1:
        raise ManifestError("version must be 1")
    chapter_id = scalar(data["chapter_id"], "chapter_id")
    if not ID_PATTERN.fullmatch(chapter_id):
        raise ManifestError("chapter_id must use lowercase letters, digits, . _ : or -")
    scalar(data["deck"], "deck")
    if scalar(data["notetype"], "notetype") != "Basic":
        raise ManifestError("notetype must be Basic")
    objectives = data["objectives"]
    if not isinstance(objectives, list) or not objectives:
        raise ManifestError("objectives must be a non-empty list")
    normalized_objectives = [
        scalar(objective, f"objectives[{index}]")
        for index, objective in enumerate(objectives)
    ]
    if len(set(normalized_objectives)) != len(normalized_objectives):
        raise ManifestError("objectives must be unique")
    data["objectives"] = normalized_objectives
    retired = data.get("retired_objectives", [])
    if not isinstance(retired, list):
        raise ManifestError("retired_objectives must be a list")
    data["retired_objectives"] = [
        scalar(objective, f"retired_objectives[{index}]")
        for index, objective in enumerate(retired)
    ]
    if set(data["retired_objectives"]) & set(normalized_objectives):
        raise ManifestError("an objective cannot be both active and retired")
    if not isinstance(data["cards"], list) or not data["cards"]:
        raise ManifestError("cards must be a non-empty list")
    return data


def validate_card(raw: object, index: int, vault: Path) -> dict[str, object]:
    label = f"cards[{index}]"
    expected = CARD_FIELDS | ({"choices"} if isinstance(raw, dict) and raw.get("type") == "mcq" else set())
    if not isinstance(raw, dict) or set(raw) != expected:
        raise ManifestError(
            f"{label} fields must be exactly: {', '.join(sorted(expected))}"
        )
    card_id = scalar(raw["id"], f"{label}.id")
    if not ID_PATTERN.fullmatch(card_id):
        raise ManifestError(
            f"{label}.id must use lowercase letters, digits, . _ : or -"
        )
    card_type = scalar(raw["type"], f"{label}.type")
    if card_type not in CARD_TYPES:
        raise ManifestError(f"{label}.type must be basic, typed, or mcq")
    status = scalar(raw["status"], f"{label}.status")
    if status not in CARD_STATUSES:
        raise ManifestError(f"{label}.status must be active or retired")
    revision = raw["revision"]
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise ManifestError(f"{label}.revision must be a positive integer")
    tags = raw["tags"]
    if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
        raise ManifestError(f"{label}.tags must be a list of strings")
    normalized_tags = []
    for tag_index, tag in enumerate(tags):
        normalized = scalar(tag, f"{label}.tags[{tag_index}]")
        if " " in normalized:
            raise ManifestError(f"{label}.tags[{tag_index}] must not contain spaces")
        normalized_tags.append(normalized)
    if status == "retired":
        normalized_tags.append("study-loop::retired")
    choices: list[str] = []
    if card_type == "mcq":
        raw_choices = raw["choices"]
        if not isinstance(raw_choices, list) or len(raw_choices) != MCQ_CHOICES:
            raise ManifestError(f"{label}.choices must list exactly {MCQ_CHOICES} options, the correct one first")
        choices = [html_field(choice, f"{label}.choices[{i}]") for i, choice in enumerate(raw_choices)]
        if len({c.lower() for c in choices}) != MCQ_CHOICES:
            raise ManifestError(f"{label}.choices must be four different options")
        if any(NOT_A_CHOICE.search(c) for c in choices):
            raise ManifestError(f"{label}.choices must not use all/none/both of the above; write a real alternative")
        if choices[0].lower() in html_field(raw["prompt"], f"{label}.prompt").lower():
            raise ManifestError(f"{label}: the question gives away the correct option ({raw_choices[0]!r})")
    return {
        "choices": choices,
        "id": card_id,
        "objective": html_field(raw["objective"], f"{label}.objective"),
        "type": card_type,
        "prompt": html_field(raw["prompt"], f"{label}.prompt"),
        "answer": html_field(raw["answer"], f"{label}.answer"),
        "source": safe_source(raw["source"], f"{label}.source", vault),
        "revision": revision,
        "status": status,
        "tags": sorted(set(normalized_tags)),
    }


def mcq_position(card_id: str) -> int:
    """Where the correct option is stored (stable per card); the card shuffles on screen anyway."""
    return sum(card_id.encode()) % MCQ_CHOICES


def render_quiz(data: dict[str, object], cards: list[dict[str, object]]) -> str | None:
    """Multiple-choice cards as a Study MCQ import.

    A quiz-only deck (no Basic cards at all) is the chapter deck itself; a mixed deck
    keeps its quiz cards in a ::Quiz subdeck so the two note types stay apart.
    """
    quiz = [card for card in cards if card["type"] == "mcq"]
    if not quiz:
        return None
    deck = scalar(data["deck"], "deck")
    if any(card["type"] != "mcq" for card in cards):
        deck = f"{deck}::Quiz"
    chapter_id = scalar(data["chapter_id"], "chapter_id")
    lines = [
        "#separator:tab",
        "#html:true",
        f"#deck:{deck}",
        f"#notetype:{MCQ_NOTETYPE}",
        f"#tags:study-loop::chapter::{chapter_id}",
        "#columns:Question\tA\tB\tC\tD\tCorrect\tWhy\tSource\tGUID\tTags",
        "#guid column:9",
        "#tags column:10",
    ]
    for card in sorted(quiz, key=lambda item: str(item["id"])):
        choices = list(card["choices"])
        position = mcq_position(str(card["id"]))
        options = choices[1:]
        options.insert(position, choices[0])
        tags = set(card["tags"]) | {"study-loop::mcq", f"study-loop::revision::{card['revision']}",
                                    f"study-loop::status::{card['status']}"}
        source = f"{card['objective']}"
        lines.append("\t".join((str(card["prompt"]), *options, "ABCD"[position], str(card["answer"]),
                                 source, str(card["id"]), " ".join(sorted(tags)))))
    return "\n".join(lines) + "\n"


def render(data: dict[str, object], vault: Path) -> str:
    basic, quiz = render_all(data, vault)
    return basic if basic is not None else quiz or ""


def render_all(data: dict[str, object], vault: Path) -> tuple[str, str | None]:
    """The Basic import and, when the manifest has mcq cards, the Study MCQ quiz import."""
    quality = quality_errors(data["cards"])
    if quality:
        raise ManifestError("mixed-review quality: " + "; ".join(quality))
    cards = [
        validate_card(raw, index, vault) for index, raw in enumerate(data["cards"])
    ]
    seen: set[str] = set()
    duplicates: set[str] = set()
    for card in cards:
        card_id = str(card["id"])
        if card_id in seen:
            duplicates.add(card_id)
        seen.add(card_id)
    if duplicates:
        raise ManifestError("duplicate card IDs: " + ", ".join(sorted(duplicates)))
    # Card objectives are HTML-escaped above; escape the declared list the same way so
    # an objective with quotes or an ampersand ("And" vs "or") still matches.
    objectives = {html_field(o, "objectives") for o in data["objectives"]}
    retired_objectives = {html_field(o, "retired_objectives") for o in data["retired_objectives"]}
    card_objectives = {str(card["objective"]) for card in cards}
    unknown = card_objectives - objectives - retired_objectives
    if unknown:
        raise ManifestError(
            "card objectives are not declared: " + ", ".join(sorted(unknown))
        )
    active_objectives = {
        str(card["objective"]) for card in cards if card["status"] == "active"
    }
    revived = active_objectives & retired_objectives
    if revived:
        raise ManifestError(
            "retired objectives with an active card: " + ", ".join(sorted(revived))
        )
    missing = objectives - active_objectives
    if missing:
        raise ManifestError(
            "objectives without an active card: " + ", ".join(sorted(missing))
        )
    deck = scalar(data["deck"], "deck")
    notetype = scalar(data["notetype"], "notetype")
    chapter_id = scalar(data["chapter_id"], "chapter_id")
    lines = [
        "#separator:tab",
        "#html:true",
        f"#deck:{deck}",
        f"#notetype:{notetype}",
        f"#tags:study-loop::chapter::{chapter_id}",
        "#columns:Front\tBack\tGUID\tTags",
        "#guid column:3",
        "#tags column:4",
    ]
    for card in sorted(cards, key=lambda item: str(item["id"])):
        if card["type"] == "mcq":
            continue
        card_tags = set(card["tags"])
        card_tags.add(f"study-loop::{card['type']}")
        card_tags.add(f"study-loop::revision::{card['revision']}")
        card_tags.add(f"study-loop::status::{card['status']}")
        back = (
            f"{card['answer']}<br><br>"
            f"<small><b>Objective:</b> {card['objective']}<br>"
            f"<b>Source:</b> {html.escape(str(card['source']))}</small>"
        )
        lines.append(
            "\t".join(
                (
                    str(card["prompt"]),
                    back,
                    str(card["id"]),
                    " ".join(sorted(card_tags)),
                )
            )
        )
    basic = "\n".join(lines) + "\n" if any(card["type"] != "mcq" for card in cards) else None
    return basic, render_quiz(data, cards)


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def main() -> int:
    args = parse_args()
    try:
        vault = args.vault.expanduser().resolve()
        if not vault.is_dir():
            raise ManifestError(f"vault is not a directory: {vault}")
        manifest = args.manifest.expanduser().resolve()
        handoff_root = (vault / "_study" / "anki").resolve()
        if not manifest.is_relative_to(handoff_root):
            raise ManifestError(
                "manifest must be inside the vault's _study/anki directory"
            )
        content, quiz = render_all(load_manifest(manifest), vault)
        if args.output is None:
            sys.stdout.write("\n".join(part for part in (content, quiz) if part))
        else:
            output = args.output.expanduser().resolve()
            if not output.is_relative_to(handoff_root):
                raise ManifestError(
                    "output must be inside the vault's _study/anki directory"
                )
            if content is not None:
                atomic_write(output, content)
            elif output.exists():
                print(f"note: {output.name} is stale (this deck is quiz-only now); delete it", file=sys.stderr)
            if quiz:
                atomic_write(output.with_name(output.stem + "-quiz.tsv"), quiz)
    except ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
