#!/usr/bin/env bash
# Canonical Agent Orchestra entry point for read-only Codex consults.
# For now this forwards to the audited legacy wrapper to avoid duplicating logic.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

candidates=(
  "$SCRIPT_DIR/../../codex-consult/scripts/consult-codex.sh"
  "$SCRIPT_DIR/../codex-consult/scripts/consult-codex.sh"
)

for wrapper in "${candidates[@]}"; do
  if [ -x "$wrapper" ]; then
    exec "$wrapper" "$@"
  fi
done

echo "error: consult-codex.sh compatibility wrapper not found" >&2
exit 2
