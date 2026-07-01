#!/usr/bin/env bash
# lifecycle-lint.sh - portable Markdown + project-build-loop house style checks.
#
# Usage: lifecycle-lint.sh <file-or-dir> [more paths...]
#
# Runs the base portable Markdown lint first, then checks lifecycle-note hygiene:
# unambiguous task state, sane heading levels, table row shape, routed-work
# clarity, and checklist/table size warnings. See ../rules/lifecycle.md.
#
# Exit code: 0 = no errors, 1 = errors found, 2 = usage/no files.

set -uo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BASE_LINT="$SCRIPT_DIR/lint.sh"
RULES_DOC="$SCRIPT_DIR/../rules/lifecycle.md"

if [ "$#" -lt 1 ]; then
  echo "usage: lifecycle-lint.sh <file-or-dir> [more paths...]" >&2
  exit 2
fi

FILES=()
for target in "$@"; do
  if [ -f "$target" ]; then
    case "$target" in *.md|*.markdown) FILES+=("$target") ;; esac
  elif [ -d "$target" ]; then
    while IFS= read -r f; do FILES+=("$f"); done \
      < <(find "$target" -type f \( -name '*.md' -o -name '*.markdown' \) | sort)
  else
    echo "skip (not found): $target" >&2
  fi
done

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "No .md/.markdown files found." >&2
  exit 2
fi

ERRORS=0
WARNINGS=0
COUNT_FILE="${TMPDIR:-/tmp}/lifecycle-lint-counts.$$"
OUT_FILE="${TMPDIR:-/tmp}/lifecycle-lint-output.$$"
trap 'rm -f "$COUNT_FILE" "$OUT_FILE"' EXIT

# Base portability is an error gate.
if ! "$BASE_LINT" "${FILES[@]}"; then
  ERRORS=$((ERRORS + 1))
fi

for f in "${FILES[@]}"; do
  awk -v file="$f" '
    function emit_error(line, msg) { printf("ERROR %s:%d: %s\n", file, line, msg); errors++ }
    function emit_warn(line, msg) { printf("WARN  %s:%d: %s\n", file, line, msg); warnings++ }
    function pipe_count(s,    i,c,prev,ch) {
      c=0; prev=""
      for (i=1; i<=length(s); i++) {
        ch=substr(s,i,1)
        if (ch=="|" && prev!="\\") c++
        prev=ch
      }
      return c
    }
    BEGIN {
      has_status_section=0
      has_status_line=0
      is_task_file=(file ~ /build-log\/task-[0-9]+\.[0-9]+.*\.md$/)
      needs_status=(file ~ /build-log\/task-[0-9]+\.[0-9]+(\.steps)?\.md$/)
      closed=0
      table_header_pipes=0
      table_count=0
      checklist_count=0
      prev_heading=0
    }
    /^## Status[[:space:]]*$/ { has_status_section=1 }
    /^Status:[[:space:]]*/ {
      has_status_line=1
      if ($0 ~ /^Status:[[:space:]]*(DONE|done|closed|Closed)/) closed=1
    }
    /Status:[[:space:]]*(DONE|done|closed|Closed)/ { closed=1 }
    /remains open/ { if (closed) emit_error(NR, "contradictory-task-state: closed note also says it remains open") }
    /- \[ \].*Explicitly say task .*ready to close/ {
      if (closed) emit_error(NR, "contradictory-task-state: closed note still asks for explicit close confirmation")
    }
    /^#{2,6}[[:space:]]/ {
      level=0
      while (substr($0, level+1, 1)=="#") level++
      if (prev_heading && level > prev_heading + 1) emit_warn(NR, "heading-level-skip: heading jumps by more than one level")
      prev_heading=level
    }
    /^\|.*\|[[:space:]]*$/ {
      pc=pipe_count($0)
      if (table_header_pipes==0) {
        table_header_pipes=pc
        table_count++
      } else if (pc != table_header_pipes) {
        emit_error(NR, "broken-table-row: row has a different cell count than the current table header")
      }
      next
    }
    !/^\|.*\|[[:space:]]*$/ { table_header_pipes=0 }
    /^- \[[ xX]\]/ { checklist_count++ }
    /DECISION:/ && /^- \[ \]/ && $0 !~ /(routed|Routed|tracked under|task `[0-9]+\.[0-9]+`|task [0-9]+\.[0-9]+)/ {
      emit_error(NR, "stale-route-action: unchecked DECISION must either belong here or say which task owns it")
    }
    END {
      if (needs_status && !has_status_section) emit_error(1, "missing-task-status: task note or steps ledger needs a ## Status section")
      if (needs_status && !has_status_line) emit_error(1, "missing-task-status: task note or steps ledger needs a Status: line")
      if (file ~ /build-log\/task-[0-9]+\.[0-9]+\.md$/ && table_count > 3) emit_warn(1, "table-overuse: focused task note has more than three tables")
      if (file ~ /build-log\/task-[0-9]+\.[0-9]+\.md$/ && checklist_count > 10) emit_warn(1, "long-checklist: focused task note has more than ten checklist items")
      printf("__COUNTS__ %d %d\n", errors, warnings)
    }
  ' "$f" > "$OUT_FILE"

  while IFS= read -r line; do
    case "$line" in
      __COUNTS__*)
        set -- $line
        ERRORS=$((ERRORS + $2))
        WARNINGS=$((WARNINGS + $3))
        ;;
      *) printf '%s\n' "$line" ;;
    esac
  done < "$OUT_FILE"
done

if [ "$ERRORS" -eq 0 ]; then
  if [ "$WARNINGS" -eq 0 ]; then
    echo "OK - lifecycle Markdown clean. Rules: $RULES_DOC"
  else
    echo "OK - lifecycle Markdown has $WARNINGS warning(s), no errors. Rules: $RULES_DOC"
  fi
  exit 0
fi

echo "FAIL - lifecycle Markdown has $ERRORS error(s), $WARNINGS warning(s). Rules: $RULES_DOC" >&2
exit 1
