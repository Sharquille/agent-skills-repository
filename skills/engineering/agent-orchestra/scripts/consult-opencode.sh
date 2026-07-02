#!/usr/bin/env bash
# Canonical Agent Orchestra entry point for read-only OpenCode consults.
# For now this forwards to the audited legacy wrapper to avoid duplicating logic.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

candidates=(
  "$SCRIPT_DIR/../../opencode-consult/scripts/consult-opencode.sh"
  "$SCRIPT_DIR/../opencode-consult/scripts/consult-opencode.sh"
)

for wrapper in "${candidates[@]}"; do
  if [ -x "$wrapper" ]; then
    exec "$wrapper" "$@"
  fi
done

echo "error: consult-opencode.sh compatibility wrapper not found" >&2
exit 2
