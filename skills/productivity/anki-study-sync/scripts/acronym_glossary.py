"""Spell out non-obvious acronyms on quiz cards, from the course's own notes.

The glossary comes only from the vault: the official ``Chapter-Kits/acronyms.md`` list,
each section's Abbreviations table, and margin definitions such as
``**LSASS**: Local Security Authority Subsystem Service``. Nothing is invented.

On the front, acronyms in the question and options get a small terms line under the
question. An acronym that appears only in the explanation is spelled out in brackets
at its first mention there. Expansions never give the answer away: no terms line on
"What does X stand for?" cards, none when the full name is already on the card, and no
option acronyms when the correct option's full name echoes the question.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

# Everyday acronyms a learner already reads as words; spelling them out is noise.
COMMON = {
    "AI", "AM", "ATM", "CD", "CEO", "CPU", "DVD", "FAQ", "GPS", "HR", "ID", "IP", "IT",
    "OK", "OS", "PC", "PDF", "PIN", "PM", "RAM", "SMS", "TV", "UK", "URL", "US", "USA",
    "USB", "WIFI", "WI-FI",
}
_TOKEN = re.compile(r"(?<![\w+-])([A-Z][A-Za-z0-9]*[A-Z0-9][A-Za-z0-9]*\+?)(s)?(?![\w+-])")
_ASKED = re.compile(r"(?i)\bwhat does (?:an? |the )?([A-Za-z0-9+-]{2,10}) stand for\b")
_TABLE_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|")
_INLINE = re.compile(r"([A-Za-z][A-Za-z' -]{2,80}?)\s*\(([A-Z][A-Za-z0-9]{1,6})\)")
_SMALL = {"of", "and", "the", "for", "to", "in", "on", "a", "an", "or", "with", "by"}
_MARGIN = re.compile(r"\*\*([A-Z][A-Za-z0-9+/-]{1,11})\*\*:\s*([^;.\n]+)")
_WORD = re.compile(r"[a-z]{5,}")
# More than this many expansions under one question is clutter, not help.
MAX_TERMS = 4


def _inline(text: str) -> list[tuple[str, str]]:
    """'exploratory data analysis (EDA)' pairs whose initials spell the acronym."""
    pairs = []
    for m in _INLINE.finditer(text):
        short = m.group(2)
        letters = [ch for ch in short.upper() if ch.isalpha()]
        words = re.findall(r"[A-Za-z]+", m.group(1))
        picked: list[str] = []
        need = list(letters)
        for word in reversed(words):
            if need and word[0].upper() == need[-1]:
                picked.append(word)
                need.pop()
            elif word.lower() in _SMALL and picked and need:
                picked.append(word)
            else:
                break
            if not need:
                break
        if not need and picked:
            pairs.append((short, " ".join(reversed(picked))))
    return pairs


def _caps(token: str) -> bool:
    return sum(ch.isupper() for ch in token) >= 2


def _add(found: dict[str, set[str]], short: str, long: str) -> None:
    short, long = short.strip(), re.sub(r"\s+", " ", long).strip()
    if not short or not long or "/" in short or " " in short or not _caps(short):
        return
    if long.lower() in {"short form", "stands for", "spelled out"} or len(long) > 80:
        return
    found.setdefault(short, set()).add(long)


def build_glossary(vault: Path) -> dict[str, str]:
    """Acronym -> full name, from the official list first, then section notes.

    An acronym with two different meanings in the notes is left out, because a wrong
    expansion is worse than none.
    """
    kits = vault / "Chapter-Kits"
    official: dict[str, set[str]] = {}
    notes: dict[str, set[str]] = {}
    inline: dict[str, set[str]] = {}  # fallback only: tables and margin notes win
    acronyms_md = kits / "acronyms.md"
    if acronyms_md.is_file():
        for line in acronyms_md.read_text(encoding="utf-8").splitlines():
            m = _TABLE_ROW.match(line)
            if m and not set(m.group(1)) <= set("-: "):
                _add(official, m.group(1), m.group(2))
    if kits.is_dir():
        for path in sorted(kits.rglob("*Study-Notes.md")):
            if "Archive" in path.parts:
                continue
            in_table = False
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip() == "**Abbreviations**":
                    in_table = True
                    continue
                if in_table:
                    m = _TABLE_ROW.match(line)
                    if m:
                        if not set(m.group(1)) <= set("-: "):
                            _add(notes, m.group(1), m.group(2))
                        continue
                    if line.strip():
                        in_table = False
                for m in _MARGIN.finditer(line):
                    _add(notes, m.group(1), m.group(2))
                for short, long in _inline(line):
                    _add(inline, short, long)
    for short, meanings in inline.items():
        if short not in notes and short not in official:
            notes[short] = meanings
    glossary: dict[str, str] = {}
    for short in set(official) | set(notes):
        if short.upper() in COMMON:
            continue
        meanings = official.get(short) or notes.get(short, set())
        distinct = {m.lower().rstrip(".") for m in meanings}
        if len(distinct) == 1:
            glossary[short] = sorted(meanings)[0]
    return glossary


def _acronyms(text: str, glossary: dict[str, str]) -> list[str]:
    seen: list[str] = []
    for m in _TOKEN.finditer(text):
        token = m.group(1)
        if token in glossary and token not in seen:
            seen.append(token)
    return seen


def _stems(text: str) -> set[str]:
    return {w[:5] for w in _WORD.findall(text.lower())}


def terms_line(prompt: str, choices: list[str], glossary: dict[str, str]) -> str:
    """The small 'NTLM: New Technology LAN Manager · ...' line for the front, or ''."""
    asked = _ASKED.search(prompt)
    if asked:
        return ""
    card_text = (prompt + " " + " ".join(choices)).lower()
    prompt_terms = _acronyms(prompt, glossary)
    option_terms = [t for c in choices for t in _acronyms(c, glossary) if t not in prompt_terms]
    option_terms = list(dict.fromkeys(option_terms))
    # A correct-option acronym whose full name echoes the question would point at it.
    prompt_stems = _stems(prompt) - {s for t in prompt_terms for s in _stems(glossary[t])}
    if choices and any(_stems(glossary[t]) & prompt_stems for t in _acronyms(choices[0], glossary)):
        option_terms = []
    def seq(text: str) -> list[str]:
        return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in {"and", "of", "the", "a"}]

    card_seq = " " + " ".join(seq(card_text)) + " "
    option_words = [set(seq(c)) for c in choices]

    def already_said(term: str) -> bool:
        words = seq(glossary[term])
        if not words or f"({term})" in prompt + " " + " ".join(choices):  # defined in brackets
            return True
        if " " + " ".join(words) + " " in card_seq:          # said as a phrase
            return True
        if any(set(words) <= o for o in option_words):        # one option spells it out
            return True
        single = [o for o in option_words if len(o) == 1 and o <= set(words)]
        return len(single) >= 2                               # options are its parts (AAA)

    prompt_terms = [t for t in prompt_terms if not already_said(t)]
    option_terms = [t for t in option_terms if not already_said(t)]
    # Options are expanded all together or not at all, so the line never singles one out.
    if len(prompt_terms) + len(option_terms) > MAX_TERMS:
        option_terms = []
    shown = (prompt_terms + option_terms)[:MAX_TERMS]
    if not shown:
        return ""
    body = " · ".join(f"<b>{html.escape(t)}</b>: {html.escape(glossary[t])}" for t in shown)
    return f'<div style="font-size:0.78em;color:#8a8f98;margin-top:0.5em">{body}</div>'


def expand_answer(answer: str, front_text: str, glossary: dict[str, str]) -> str:
    """Spell out, once, an acronym that appears only in the explanation."""
    front = set(_acronyms(front_text, glossary))
    done: set[str] = set()

    def repl(m: re.Match[str]) -> str:
        token = m.group(1)
        if token not in glossary or token in front or token in done:
            return m.group(0)
        done.add(token)
        full = glossary[token]
        if full.lower() in answer.lower():
            return m.group(0)
        return f"{m.group(0)} ({full})"

    return _TOKEN.sub(repl, answer)
