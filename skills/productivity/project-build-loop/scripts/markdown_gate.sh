#!/usr/bin/env bash
# markdown_gate.sh - project-build-loop Markdown hygiene gate.
#
# Usage: markdown_gate.sh <file-or-dir> [more paths...]
#
# Delegates to portable-markdown lifecycle lint. Set PORTABLE_MARKDOWN_LIFECYCLE_LINT
# to override the resolver when skills are deployed somewhere else.

set -uo pipefail

if [ "$#" -lt 1 ]; then
  echo "usage: markdown_gate.sh <file-or-dir> [more paths...]" >&2
  exit 2
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DEFAULT_LINT="$SCRIPT_DIR/../../portable-markdown/scripts/lifecycle-lint.sh"
LINT="${PORTABLE_MARKDOWN_LIFECYCLE_LINT:-$DEFAULT_LINT}"

if [ ! -x "$LINT" ]; then
  echo "error: portable-markdown lifecycle lint not found or not executable: $LINT" >&2
  echo "set PORTABLE_MARKDOWN_LIFECYCLE_LINT=/path/to/lifecycle-lint.sh" >&2
  exit 2
fi

"$LINT" "$@"
