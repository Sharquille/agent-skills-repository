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

from acronym_glossary import build_glossary, expand_answer, terms_line
from anki_quality import quality_errors


ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._:-]*$")
CARD_TYPES = {"basic", "typed", "mcq", "calc"}
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

# Calculation cards (assets/study-calc/calc.js solves them; keep these kinds in step with
# its KINDS table). Each kind lists the placeholders its prompt must use and its default
# range for r, where a negative bound counts back from n.
CALC_NOTETYPE = "Study Calc"
CALC_KINDS: dict[str, tuple[frozenset[str], tuple[int, int] | None]] = {
    "binom-order": (frozenset({"seq"}), None),
    "binom-count": (frozenset({"n", "r"}), (1, -1)),
    "binom-exact": (frozenset({"n", "r"}), (1, -1)),
    "binom-atmost": (frozenset({"n", "r"}), (1, -2)),
    "binom-atleast": (frozenset({"n", "r"}), (2, -1)),
    "binom-atleast1": (frozenset({"n"}), None),
    "binom-mean": (frozenset({"n"}), None),
    "binom-sd": (frozenset({"n"}), None),
}
CALC_PLACEHOLDERS = {"n", "p", "q", "r", "pct", "inv", "seq"}
PLACEHOLDER = re.compile(r"\{([a-z0-9]+)\}")

# Kinds that build their own data or table each review: the placeholders the prompt
# must use, and each param's type ("?" marks it optional). Every kind also takes an
# optional "d", the decimal places, to override its default.
_FREQ = {"k": "?pair", "width": "?pair", "start": "?pair", "f": "?pair"}
CALC_DATA_KINDS: dict[str, tuple[frozenset[str], dict[str, str]]] = {
    "class-width": (frozenset({"min", "max", "k"}), {"k": "?nums", "min": "?pair", "spread": "?pair"}),
    "class-midpoint": (frozenset({"lower", "upper"}), {"lower": "?pair", "width": "?pair"}),
    "rel-freq": (frozenset({"table", "cls"}), _FREQ),
    "cum-freq": (frozenset({"table", "cut"}), _FREQ),
    "grouped-mean": (frozenset({"table"}), _FREQ),
    "mean": (frozenset({"data"}), {"n": "?pair", "x": "?pair"}),
    "median": (frozenset({"data"}), {"n": "?pair", "x": "?pair"}),
    "middle-position": (frozenset({"n"}), {"n": "?pair"}),
    "weighted-avg": (frozenset({"table"}), {"items": "?strs", "x": "?pair"}),
    "trimmed-mean": (frozenset({"data"}), {"n": "?pair", "x": "?pair", "outlier": "?pair"}),
    "range": (frozenset({"data"}), {"n": "?pair", "x": "?pair"}),
    "sd": (frozenset({"data"}), {"n": "?pair", "x": "?pair", "ask": "?s|s2|sigma"}),
    "quartiles": (frozenset({"data"}), {"n": "?pair", "x": "?pair", "ask": "?q1|q3|iqr", "parity": "?odd|even"}),
    "prob-relfreq": (frozenset({"n", "f"}), {"n": "?pair", "share": "?pair"}),
    "prob-equal": (frozenset({"counts", "target"}), {"labels": "?strs", "c": "?pair", "ask": "?p|not"}),
    "mult-indep": (frozenset({"pa", "pb"}), {"pa": "?probs", "pb": "?probs"}),
    "mult-dep": (frozenset({"a", "b"}), {"a": "?pair", "b": "?pair"}),
    "conditional-table": (frozenset({"table", "given", "event"}), {"rows": "?strs", "cols": "?strs", "c": "?pair"}),
    "add-general": (frozenset({"pa", "pb", "pab"}), {"pa": "?probs", "pb": "?probs", "pab": "?probs"}),
    "add-exclusive": (frozenset({"table", "a", "b"}), {"labels": "?strs", "min": "?int", "head": "?str"}),
    "share-table": (frozenset({"table", "target"}), {"labels": "?strs", "c": "?pair", "head": "?str"}),
    "dist": (frozenset({"table"}), {"x": "?nums", "min": "?int", "ask": "?mean|sd"}),
    "linear": (frozenset({"expr"}), {"mu": "?nums", "sigma": "?nums", "a": "?nums", "b": "?nums", "ask": "?mean|sd"}),
    "combo": (frozenset({"expr"}), {"mu1": "?nums", "s1": "?nums", "mu2": "?nums", "s2": "?nums", "a": "?nums", "b": "?nums", "ask": "?mean|sd"}),
}
# Placeholders a data kind may show besides the required ones.
CALC_DATA_EXTRA = {"n", "total", "cut", "cls", "target", "given", "event", "mu", "sigma", "a", "b",
                   "mu1", "s1", "mu2", "s2", "f", "min", "max", "k", "lower", "upper", "pa", "pb", "pab", "counts"}
NON_BASIC = {"mcq", "calc"}


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
    extra = {"mcq": {"choices"}, "calc": {"kind", "params"}}
    expected = CARD_FIELDS | (extra.get(raw.get("type"), set()) if isinstance(raw, dict) else set())
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
        raise ManifestError(f"{label}.type must be basic, typed, mcq, or calc")
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
    kind, params = "", ""
    if card_type == "calc":
        kind, params = validate_calc(raw, label)
    return {
        "choices": choices,
        "kind": kind,
        "params": params,
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


def _int_pair(value: object, label: str) -> tuple[int, int]:
    if (not isinstance(value, list) or len(value) != 2
            or any(not isinstance(x, int) or isinstance(x, bool) for x in value)):
        raise ManifestError(f"{label} must be a [low, high] pair of whole numbers")
    return value[0], value[1]


def _check_param(value: object, kind: str, label: str) -> None:
    def number(x: object) -> bool:
        return isinstance(x, (int, float)) and not isinstance(x, bool)
    if kind == "pair":
        lo, hi = _int_pair(value, label)
        if lo > hi:
            raise ManifestError(f"{label} must have low <= high")
    elif kind in {"nums", "probs"}:
        if not isinstance(value, list) or not value or not all(number(x) for x in value):
            raise ManifestError(f"{label} must be a non-empty list of numbers")
        if kind == "probs" and not all(0 < x < 1 for x in value):
            raise ManifestError(f"{label} must hold probabilities strictly between 0 and 1")
    elif kind == "strs":
        if not isinstance(value, list) or len(value) < 2 or any(not isinstance(x, str) or not x.strip() for x in value):
            raise ManifestError(f"{label} must list at least two labels")
    elif kind == "int":
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ManifestError(f"{label} must be a whole number")
    elif kind == "str":
        if not isinstance(value, str) or not value.strip():
            raise ManifestError(f"{label} must be text")
    elif value not in kind.split("|"):
        raise ManifestError(f"{label} must be one of: {kind.replace('|', ', ')}")


def validate_data_calc(raw: dict, label: str, kind: str) -> tuple[str, str]:
    needed, spec = CALC_DATA_KINDS[kind]
    params = raw["params"]
    if not isinstance(params, dict):
        raise ManifestError(f"{label}.params must be an object")
    unknown = set(params) - set(spec) - {"d"}
    if unknown:
        raise ManifestError(f"{label}.params has unknown keys: {', '.join(sorted(unknown))}")
    for key, typ in spec.items():
        if key in params:
            _check_param(params[key], typ.lstrip("?"), f"{label}.params.{key}")
        elif not typ.startswith("?"):
            raise ManifestError(f"{label}.params.{key} is required")
    if "d" in params and (not isinstance(params["d"], int) or isinstance(params["d"], bool) or not 0 <= params["d"] <= 4):
        raise ManifestError(f"{label}.params.d must be 0 to 4 decimal places")
    used = set(PLACEHOLDER.findall(str(raw["prompt"])))
    if used - needed - CALC_DATA_EXTRA:
        raise ManifestError(f"{label}.prompt uses unknown placeholders: {', '.join(sorted(used - needed - CALC_DATA_EXTRA))}")
    if needed - used:
        raise ManifestError(f"{label}.prompt must show {', '.join('{' + x + '}' for x in sorted(needed - used))}")
    return kind, html.escape(json.dumps(params, separators=(",", ":"), sort_keys=True))


def validate_calc(raw: dict, label: str) -> tuple[str, str]:
    """Check a calc card's kind, params, and prompt placeholders; return (kind, params JSON)."""
    kind = scalar(raw["kind"], f"{label}.kind")
    if kind in CALC_DATA_KINDS:
        return validate_data_calc(raw, label, kind)
    if kind not in CALC_KINDS:
        raise ManifestError(f"{label}.kind must be one of: {', '.join(sorted(CALC_KINDS) + sorted(CALC_DATA_KINDS))}")
    needed, default_r = CALC_KINDS[kind]
    params = raw["params"]
    if not isinstance(params, dict) or not set(params) <= {"n", "p", "r", "labels"} or "n" not in params:
        raise ManifestError(f"{label}.params must have n, plus optional p, r, labels")
    lo_n, hi_n = _int_pair(params["n"], f"{label}.params.n")
    # P(r) kinds stay within the binomial table (n <= 20); a mean or SD has no table to match.
    top = 200 if kind in {"binom-mean", "binom-sd"} else 20
    if not 2 <= lo_n <= hi_n <= top:
        raise ManifestError(f"{label}.params.n must satisfy 2 <= low <= high <= {top}")
    probs = params.get("p", [0.5])
    if (not isinstance(probs, list) or not probs
            or any(not isinstance(x, (int, float)) or isinstance(x, bool) or not 0 < x < 1 for x in probs)):
        raise ManifestError(f"{label}.params.p must be a list of probabilities strictly between 0 and 1")
    spec = params.get("r", default_r)
    if "r" in params:
        spec = _int_pair(params["r"], f"{label}.params.r")
    if spec is not None:
        for n in (lo_n, hi_n):
            lo, hi = (b if b >= 0 else n + b for b in spec)
            if not 0 <= lo <= hi <= n:
                raise ManifestError(f"{label}.params.r gives an empty or out-of-range r for n = {n}")
    if kind == "binom-order":
        names = params.get("labels")
        if not isinstance(names, list) or len(names) != 2 or any(not isinstance(x, str) or not x.strip() for x in names):
            raise ManifestError(f"{label}.params.labels must name the success and the failure, such as [\"right\", \"wrong\"]")
    used = set(PLACEHOLDER.findall(str(raw["prompt"])))
    if used - CALC_PLACEHOLDERS:
        raise ManifestError(f"{label}.prompt uses unknown placeholders: {', '.join(sorted(used - CALC_PLACEHOLDERS))}")
    if needed - used:
        raise ManifestError(f"{label}.prompt must show {', '.join('{' + x + '}' for x in sorted(needed - used))}")
    if kind != "binom-count" and not used & {"p", "pct", "inv"}:
        raise ManifestError(f"{label}.prompt must give the probability as {{p}}, {{pct}}, or {{inv}}")
    return kind, html.escape(json.dumps(params, separators=(",", ":"), sort_keys=True))


def mcq_position(card_id: str) -> int:
    """Where the correct option is stored (stable per card); the card shuffles on screen anyway."""
    return sum(card_id.encode()) % MCQ_CHOICES


def render_quiz(data: dict[str, object], cards: list[dict[str, object]],
                glossary: dict[str, str] | None = None) -> str | None:
    """Multiple-choice cards as a Study MCQ import.

    A deck with no Basic cards at all is the chapter deck itself; a mixed deck keeps its
    quiz and calc cards in a ::Quiz subdeck so the note types stay apart.
    """
    quiz = [card for card in cards if card["type"] == "mcq"]
    if not quiz:
        return None
    deck = practice_deck(data, cards)
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
        prompt, answer = str(card["prompt"]), str(card["answer"])
        if glossary:
            front = prompt + " " + " ".join(choices)
            answer = expand_answer(answer, front, glossary)
            prompt += terms_line(prompt, choices, glossary)
        lines.append("\t".join((prompt, *options, "ABCD"[position], answer,
                                 source, str(card["id"]), " ".join(sorted(tags)))))
    return "\n".join(lines) + "\n"


def practice_deck(data: dict[str, object], cards: list[dict[str, object]]) -> str:
    deck = scalar(data["deck"], "deck")
    return f"{deck}::Quiz" if any(card["type"] not in NON_BASIC for card in cards) else deck


def render_calc(data: dict[str, object], cards: list[dict[str, object]]) -> str | None:
    """Calculation cards as a Study Calc import, in the same deck as the quiz cards."""
    calc = [card for card in cards if card["type"] == "calc"]
    if not calc:
        return None
    chapter_id = scalar(data["chapter_id"], "chapter_id")
    lines = [
        "#separator:tab",
        "#html:true",
        f"#deck:{practice_deck(data, cards)}",
        f"#notetype:{CALC_NOTETYPE}",
        f"#tags:study-loop::chapter::{chapter_id}",
        "#columns:Prompt\tKind\tParams\tMethod\tSource\tGUID\tTags",
        "#guid column:6",
        "#tags column:7",
    ]
    for card in sorted(calc, key=lambda item: str(item["id"])):
        tags = set(card["tags"]) | {"study-loop::calc", f"study-loop::revision::{card['revision']}",
                                    f"study-loop::status::{card['status']}"}
        lines.append("\t".join((str(card["prompt"]), str(card["kind"]), str(card["params"]), str(card["answer"]),
                                 str(card["objective"]), str(card["id"]), " ".join(sorted(tags)))))
    return "\n".join(lines) + "\n"


def render(data: dict[str, object], vault: Path) -> str:
    basic, quiz, calc = render_all(data, vault)
    return basic if basic is not None else quiz or calc or ""


def render_all(data: dict[str, object], vault: Path) -> tuple[str | None, str | None, str | None]:
    """The Basic, Study MCQ, and Study Calc imports; each is None when it has no cards."""
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
    glossary = build_glossary(vault)
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
        if card["type"] in NON_BASIC:
            continue
        card_tags = set(card["tags"])
        card_tags.add(f"study-loop::{card['type']}")
        card_tags.add(f"study-loop::revision::{card['revision']}")
        card_tags.add(f"study-loop::status::{card['status']}")
        prompt, answer = str(card["prompt"]), str(card["answer"])
        if glossary:
            answer = expand_answer(answer, prompt, glossary)
            prompt += terms_line(prompt, [], glossary)
        back = (
            f"{answer}<br><br>"
            f"<small><b>Objective:</b> {card['objective']}<br>"
            f"<b>Source:</b> {html.escape(str(card['source']))}</small>"
        )
        lines.append(
            "\t".join(
                (
                    prompt,
                    back,
                    str(card["id"]),
                    " ".join(sorted(card_tags)),
                )
            )
        )
    basic = "\n".join(lines) + "\n" if any(card["type"] not in NON_BASIC for card in cards) else None
    return basic, render_quiz(data, cards, glossary), render_calc(data, cards)


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
        content, quiz, calc = render_all(load_manifest(manifest), vault)
        if args.output is None:
            sys.stdout.write("\n".join(part for part in (content, quiz, calc) if part))
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
            if calc:
                atomic_write(output.with_name(output.stem + "-calc.tsv"), calc)
    except ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
