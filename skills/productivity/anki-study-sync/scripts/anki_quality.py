"""Mixed-review quality checks for Anki study-sync manifests."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence


DEICTIC_PROMPT = re.compile(
    r"(?i)\b("
    r"this section|this chapter|this note|this lab|this exercise|this course|"
    r"the course(?:'s)?|"
    r"listed in|described above|in this (?:scope|packet)|"
    r"from the (?:note|section|chapter|lab)"
    r")\b"
)
LAB_NUMBER_PROMPT = re.compile(
    r"(?i)(?:\b\d+\.\d+(?:\.\d+)?\b.{0,40}\b(?:exercise|lab)\b|"
    r"\b(?:exercise|lab)\b.{0,40}\b\d+\.\d+(?:\.\d+)?\b)"
)


def _normalize(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value.strip().lower())


def quality_errors(cards: Sequence[object]) -> list[str]:
    """Return mixed-review defects for active cards. Retired rows are ignored."""
    errors: list[str] = []
    active: list[tuple[str, Mapping[str, object]]] = []
    for index, raw in enumerate(cards):
        if not isinstance(raw, Mapping):
            continue
        card_id = str(raw.get("id") or f"cards[{index}]")
        if str(raw.get("status") or "").strip() != "active":
            continue
        prompt = raw.get("prompt")
        if isinstance(prompt, str):
            if DEICTIC_PROMPT.search(prompt):
                errors.append(
                    f"{card_id}: prompt depends on section or course context; "
                    "name the retrieval target so the card stands alone in mixed review"
                )
            if LAB_NUMBER_PROMPT.search(prompt):
                errors.append(
                    f"{card_id}: prompt depends on a numbered lab or exercise"
                )
        active.append((card_id, raw))

    seen_prompts: dict[str, str] = {}
    seen_answers: dict[str, str] = {}
    for card_id, raw in active:
        prompt_key = _normalize(raw.get("prompt"))
        answer_key = _normalize(raw.get("answer"))
        if prompt_key:
            previous = seen_prompts.get(prompt_key)
            if previous:
                errors.append(
                    f"{card_id}: duplicate active prompt of {previous}"
                )
            else:
                seen_prompts[prompt_key] = card_id
        if answer_key:
            previous = seen_answers.get(answer_key)
            if previous:
                errors.append(
                    f"{card_id}: duplicate active answer of {previous}; "
                    "retire one id or change the retrieval target"
                )
            else:
                seen_answers[answer_key] = card_id
    return errors
