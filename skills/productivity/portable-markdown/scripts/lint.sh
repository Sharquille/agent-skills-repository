#!/usr/bin/env bash
# lint.sh — flag non-portable Markdown syntax.
#
# Usage:   lint.sh <file-or-dir> [more paths...]
# Example: lint.sh Notes/
#
# Flags:
#   1. Obsidian comments  %% ... %%      (leak as literal text outside Obsidian)
#   2. Non-standard alert callouts        (only the 5 GFM types render portably)
#
# The 5 allowed GFM alert types: NOTE TIP IMPORTANT WARNING CAUTION (UPPERCASE).
#
# Exit code 0 = portable (no findings), 1 = findings need fixing, 2 = usage error.

set -uo pipefail

if [ "$#" -lt 1 ]; then
  echo "usage: lint.sh <file-or-dir> [path...]" >&2
  exit 2
fi

# Collect target markdown/text files.
FILES=()
for target in "$@"; do
  if [ -f "$target" ]; then
    FILES+=("$target")
  elif [ -d "$target" ]; then
    while IFS= read -r f; do FILES+=("$f"); done \
      < <(find "$target" -type f \( -name '*.md' -o -name '*.markdown' -o -name '*.txt' \) | sort)
  else
    echo "skip (not found): $target" >&2
  fi
done

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "No .md/.markdown/.txt files found." >&2
  exit 2
fi

FINDINGS=0

for f in "${FILES[@]}"; do
  # 1. Obsidian %% comments.
  if hits=$(grep -nE '%%' "$f"); then
    echo "== $f :: Obsidian %% comment (use <!-- --> instead) =="
    printf '%s\n' "$hits"
    FINDINGS=1
  fi

  # 2. Alert callouts whose type is not one of the 5 standard (case-sensitive).
  #    Matches '> [!something]' then filters out the allowed UPPERCASE set.
  if hits=$(grep -nE '^[[:space:]]*>[[:space:]]*\[![A-Za-z]+\]' "$f" \
            | grep -vE '\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]'); then
    echo "== $f :: non-standard or lowercase alert (use one of NOTE/TIP/IMPORTANT/WARNING/CAUTION) =="
    printf '%s\n' "$hits"
    FINDINGS=1
  fi

  # 3. Trailing text on an alert title line. GitHub requires the tag to sit ALONE
  #    on its line; '> [!NOTE] some text' degrades to a plain blockquote.
  if hits=$(grep -nE '^[[:space:]]*>[[:space:]]*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\][[:space:]]+[^[:space:]]' "$f"); then
    echo "== $f :: text after the alert tag (put it on the next '> ' line) =="
    printf '%s\n' "$hits"
    FINDINGS=1
  fi
done

if [ "$FINDINGS" -eq 0 ]; then
  echo "OK — portable Markdown, no findings."
fi
exit "$FINDINGS"
