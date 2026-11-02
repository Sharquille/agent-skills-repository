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
SOURCE_TAG_PROMPT = re.compile(
    r"(?i)\b(?:module \d+|the lecture(?:'s)?|lecture's|figure \d+[-.]?\d*|fig\. ?\d+|"
    r"the textbook|the slides?|the deck|[A-Z]{2,3}-\d{3}\b)"
)
LAB_NUMBER_PROMPT = re.compile(
    r"(?i)(?:\b\d+\.\d+(?:\.\d+)?\b.{0,40}\b(?:exercise|lab)\b|"
    r"\b(?:exercise|lab)\b.{0,40}\b\d+\.\d+(?:\.\d+)?\b)"
)


# Explanation noise: "X wins because ..." and a closing clause about the wrong options.
# A contrast with one named option ("while a time bomb waits for a date") is a lesson
# and stays; only generic commentary on the other options is rejected.
WINS_FORMULA = re.compile(r"(?i)^[^.]{1,120}?\bwins because\b")
DISTRACTOR_TAIL = re.compile(
    r"(?i)[,;] (?:while|whereas|unlike)\b[^.;]*\b(?:the others?|other (?:options?|choices|answers|items|sets|pairs)"
    r"|near[- ]?miss(?:es)?|the rest|distractors?)\b[^;]*\.?\s*$"
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
            if SOURCE_TAG_PROMPT.search(prompt):
                errors.append(
                    f"{card_id}: prompt names where the idea was taught (module, lecture, "
                    "figure, slides, or course code); ask about the idea itself"
                )
            if LAB_NUMBER_PROMPT.search(prompt):
                errors.append(
                    f"{card_id}: prompt depends on a numbered lab or exercise"
                )
        answer = raw.get("answer")
        if isinstance(answer, str):
            if WINS_FORMULA.search(answer):
                errors.append(
                    f"{card_id}: answer uses the 'X wins because' formula; "
                    "write 'Answer: reason' instead"
                )
            if DISTRACTOR_TAIL.search(answer):
                errors.append(
                    f"{card_id}: answer ends by commenting on the other options "
                    "('while the others / near misses ...'); end on the reason"
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


# Answer leakage: the front already contains the answer's key term ("regulate" on a
# card whose answer is "Regulatory"). Word matching cannot be precise, so this is a
# warning for review, never a build failure. Choice fronts ("X or Y?", "How does X
# differ from Y?") and multi-part fronts name their options on purpose and are skipped;
# a synonym pair ("control or regulate") is skipped too, so Sol review still owns leaks.
# Tag a reviewed false positive "leak-ok" to silence it.
_LEAK_STOP = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "by", "with", "its", "it",
    "is", "are", "vs", "as", "at", "from", "into", "yes", "no", "not", "only",
}
_LEAK_GENERIC = {
    "theory", "approach", "attack", "attacks", "control", "controls", "software", "function",
    "license", "model", "rule", "rules", "distance", "touch", "type", "types", "irony",
    "conflict", "character", "setting", "point", "view", "communication", "system", "systems",
    "file", "files", "app", "apps", "data", "network", "person", "first", "third", "second",
}
_CHOICE = re.compile(
    r"(?i)\b(or|vs\.?|versus|between|differ|differs|difference|compare|contrast|which of|"
    r"of [^?]*,[^?]* and)\b|/"
)
_MULTI = re.compile(
    r"(?i)\band which\b|\bname (one|two|three|four|five|\d)\b|, and (its|what|where|which)\b|"
    r"\bwhat goes\b"
)
_WORD = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)*")


def _stem(word: str) -> str:
    return word[:5] if len(word) > 5 else word


def leaked_term(prompt: str, answer: str) -> str | None:
    """Return the answer's head phrase when every key word of it already appears on the front."""
    if _CHOICE.search(prompt) or _MULTI.search(prompt):
        return None
    head = re.split(r"[.:;(,\n]|\s[-\u2013\u2014]\s", answer.strip(), maxsplit=1)[0]
    if re.search(r"[=<>\u00f7\u00d7\u221a\u03a3^]", head):
        return None  # a formula answer repeats the front's symbols by design
    words = _WORD.findall(head.lower())
    if not 1 <= len(words) <= 4:
        return None
    keys = [w for w in words if w not in _LEAK_STOP and w not in _LEAK_GENERIC and len(w) >= 5]
    front = _WORD.findall(prompt.lower())
    if keys and all(any(f.startswith(_stem(k)) for f in front) for k in keys):
        return head.strip()
    return None


def leak_warnings(cards: Sequence[object]) -> list[str]:
    """Active cards whose front appears to give away the answer. Advisory only."""
    warnings: list[str] = []
    for index, raw in enumerate(cards):
        if not isinstance(raw, Mapping) or str(raw.get("status") or "").strip() != "active":
            continue
        tags = raw.get("tags") if isinstance(raw.get("tags"), list) else []
        prompt, answer = raw.get("prompt"), raw.get("answer")
        choices = raw.get("choices")
        if raw.get("type") == "calc":
            continue  # the answer is computed per review; "answer" holds the method line
        if raw.get("type") == "mcq" and isinstance(choices, list) and choices:
            answer = choices[0]  # the correct option, not the explanation
        if "leak-ok" in tags or not isinstance(prompt, str) or not isinstance(answer, str):
            continue
        term = leaked_term(prompt, answer)
        if term:
            card_id = str(raw.get("id") or f"cards[{index}]")
            warnings.append(f"{card_id}: front may give away the answer ({term!r}); "
                            "reword it, or tag leak-ok after review")
    return warnings


# Course-wide overlap: one card per idea across every chapter manifest. Advisory, like
# leak warnings: word matching can't judge meaning, so each hit is a candidate to merge,
# retire, or tag "overlap-ok" after review (a deliberate contrast pair such as GET vs POST).
_DEFINE = re.compile(
    r"(?i)^\s*(?:in [^,?]+, )?what (?:is|are|was|were) (?:an? |the )?(?P<term>[^?]{2,60}?)\??\s*$"
    r"|^\s*what does (?:an? |the )?(?P<term2>[^?]{1,40}?) (?:stand for|do|mean|measure|identify|describe|hold)\b"
)
_ACRONYM = re.compile(r"(?i)^\s*what does (?:an? |the )?(?P<acr>[A-Z][A-Za-z0-9]{1,7}) stand for\??\s*$")
_OVERLAP_STOP = _LEAK_STOP | {
    "what", "which", "how", "does", "do", "why", "when", "where", "who", "can", "you", "your",
    "that", "this", "these", "be", "has", "have", "one", "two", "three", "four", "five", "name",
    "use", "used", "using", "than", "more", "most", "less", "each", "any", "other", "instead",
}
OVERLAP_SIMILARITY = 0.75


def _term_key(term: str) -> str:
    words = [w for w in _WORD.findall(term.lower()) if w not in _LEAK_STOP]
    return " ".join(w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w for w in words)


def _content(text: str) -> set[str]:
    return {_stem(w) for w in _WORD.findall(text.lower()) if w not in _OVERLAP_STOP and len(w) > 2}


def official_acronyms(text: str) -> frozenset[str]:
    """Acronyms from a kit's acronyms.md table (first column), e.g. an exam's official list."""
    found, in_body = set(), False
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not line.lstrip().startswith("|"):
            in_body = False
            continue
        if re.fullmatch(r"[\s|:-]+", line):
            in_body = True  # the divider: rows above it are the header
            continue
        if in_body and cells and re.fullmatch(r"[A-Z][A-Za-z0-9&/.-]{1,14}", cells[0]):
            found.add(cells[0])
            found.update(part for part in cells[0].split("/") if len(part) > 1)
    return frozenset(found)


def overlap_warnings(decks: Mapping[str, Sequence[object]], official: frozenset[str] = frozenset()) -> list[str]:
    """Pairs of active cards, in one manifest or across manifests, that likely test the same idea.

    An expansion card ("What does ARP stand for?") for an acronym on an official list is
    tested content in its own right, so it is not flagged for repeating a concept card;
    two cards that both define the same acronym still are.
    """
    cards = []
    for deck, rows in decks.items():
        for index, raw in enumerate(rows):
            if not isinstance(raw, Mapping) or str(raw.get("status") or "").strip() != "active":
                continue
            prompt, answer = raw.get("prompt"), raw.get("answer")
            if not isinstance(prompt, str) or not isinstance(answer, str):
                continue
            tags = raw.get("tags") if isinstance(raw.get("tags"), list) else []
            m = _DEFINE.search(prompt)
            term = _term_key((m.group("term") or m.group("term2"))) if m else ""
            acr = _ACRONYM.search(prompt)
            choices = raw.get("choices") if isinstance(raw.get("choices"), list) else []
            cards.append({
                "choices": [_term_key(str(c)) for c in choices],
                "label": f"{raw.get('id') or f'cards[{index}]'} ({deck})", "prompt": prompt,
                "answer": answer, "ok": "overlap-ok" in tags, "term": term,
                "acronym": acr.group("acr") if acr else "", "words": _content(prompt + " " + answer),
            })
    warnings: list[str] = []
    for i, a in enumerate(cards):
        for b in cards[i + 1:]:
            if a["ok"] and b["ok"]:
                continue
            reason = ""
            if a["term"] and a["term"] == b["term"]:
                reason = f"both define {a['term']!r}"
            elif (a["choices"] and b["choices"] and a["choices"][0] == b["choices"][0]
                  and len(set(a["choices"]) & set(b["choices"])) >= 3):
                reason = "same correct option and at least three shared options (a reworded repeat?)"
            else:
                for x, y in ((a, b), (b, a)):
                    if x["acronym"] and x["acronym"].upper() not in {o.upper() for o in official} and re.search(rf"\b{re.escape(x['acronym'])}\b", y["prompt"] + " " + y["answer"]):
                        reason = f"{x['acronym']} expansion card repeats a card that uses {x['acronym']}"
                        break
                if not reason and a["words"] and b["words"]:
                    shared = len(a["words"] & b["words"]) / min(len(a["words"]), len(b["words"]))
                    if shared >= OVERLAP_SIMILARITY:
                        reason = f"{shared:.0%} of content words shared"
            if reason:
                warnings.append(f"overlap: {a['label']} ~ {b['label']}: {reason}; "
                                "keep one card, or tag both overlap-ok after review")
    return warnings
