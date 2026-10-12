#!/usr/bin/env python3
"""List a chapter-study-kit chapter's Core topics and emit an Anki manifest skeleton. Read-only.

    kit_scaffold.py --course <course dir> --chapter 05 [--output scaffold.json]

The course folder is the generator's vault: manifests go in <course>/_study/anki/.
Each topic carries its exact source anchor, objective, ID prefix, tags, and body
text, so a drafting brief can be built from this output alone.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Same heading rule as chapter-competency-loop's core_concepts(): numbered ## or ### headings.
TOPIC = re.compile(r"^#{2,3}\s+(\d+)\.\s+(.+?)\s*$")
ANY_HEADING = re.compile(r"^#{1,3}\s+")
CORE_START = re.compile(r"^#\s+\S+\s+Core\s*$")
CORE_END = re.compile(r"^#\s.*(Quiz why|Retrieval)", re.I)
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


class ScaffoldError(RuntimeError):
    """A user-facing scaffold failure."""


def section_key(name: str) -> tuple[int, ...]:
    return tuple(int(p) for p in re.findall(r"\d+", name))


def notes_file(section: Path) -> Path:
    notes = sorted(section.glob("*Study-Notes.md"))
    if not notes:
        raise ScaffoldError(f"{section} has no *Study-Notes.md")
    return notes[0]


def core_topics(text: str) -> list[dict[str, object]]:
    """Numbered topics between '# X.Y Core' and '# X.Y Retrieval', with their body text."""
    topics: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    started = False
    in_fence = False
    for line in text.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
        if not in_fence:
            if CORE_START.match(line):
                started = True
                continue
            if started and CORE_END.match(line):
                break
            m = TOPIC.match(line)
            if m:
                current = {"core": int(m.group(1)), "heading": f"{m.group(1)}. {re.sub(r'\s+#+$', '', m.group(2)).strip()}", "body": []}
                topics.append(current)
                continue
            if ANY_HEADING.match(line):
                current = None  # a group heading ("## B. …") ends the topic's body
                continue
        if current is not None:
            current["body"].append(line)  # type: ignore[union-attr]
    for t in topics:
        t["body"] = "\n".join(t["body"]).strip()  # type: ignore[arg-type]
    return topics


def scaffold(course: Path, chapter: str) -> dict[str, object]:
    course = course.expanduser().resolve()
    code = course.name
    slug = code.lower()
    chapter = f"{int(chapter):02d}"
    chapter_dir = course / "Chapter-Kits" / f"Chapter-{chapter}"
    if not chapter_dir.is_dir():
        raise ScaffoldError(f"no chapter folder: {chapter_dir}")
    sections = sorted((d for d in chapter_dir.iterdir() if d.is_dir() and re.fullmatch(r"\d+\.\d+", d.name)), key=lambda d: section_key(d.name))
    if not sections:
        raise ScaffoldError(f"no sections in {chapter_dir}")
    out_sections = []
    objectives: list[str] = []
    for sec in sections:
        notes = notes_file(sec)
        rel = notes.relative_to(course).as_posix()
        sec_slug = sec.name.replace(".", "-")
        topics = []
        for t in core_topics(notes.read_text(encoding="utf-8")):
            title = str(t["heading"]).split(". ", 1)[1]
            objective = f"{sec.name} Core {t['core']} · {title}"
            topics.append(
                {
                    "core": t["core"],
                    "heading": t["heading"],
                    "objective": objective,
                    "source": f"{rel}#{t['heading']}",
                    "id_prefix": f"{slug}.{sec_slug}.core-{t['core']}",
                    "tags": [slug, f"ch{chapter}", f"sec-{sec_slug}", f"core-{t['core']}"],
                    "body": t["body"],
                }
            )
            objectives.append(objective)
        if not topics:
            raise ScaffoldError(f"{rel} has no numbered Core topics")
        out_sections.append({"section": sec.name, "notes": rel, "topics": topics})
    chapter_id = f"{slug}-ch{chapter}"
    return {
        "course": code,
        "chapter": chapter,
        "manifest_path": f"_study/anki/{chapter_id}.json",
        "sections": out_sections,
        "skeleton": {
            "schema": "anki-study-sync.manifest",
            "version": 1,
            "chapter_id": chapter_id,
            "deck": f"{code}::Chapter {chapter}",
            "notetype": "Basic",
            "objectives": objectives,
            "cards": [],
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--course", type=Path, required=True, help="course folder that holds Chapter-Kits/")
    ap.add_argument("--chapter", required=True, help="chapter number, e.g. 5 or 05")
    ap.add_argument("--output", type=Path, help="write JSON here instead of stdout")
    args = ap.parse_args()
    try:
        data = json.dumps(scaffold(args.course, args.chapter), ensure_ascii=False, indent=2) + "\n"
    except (ScaffoldError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.output:
        args.output.write_text(data, encoding="utf-8")
    else:
        sys.stdout.write(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
