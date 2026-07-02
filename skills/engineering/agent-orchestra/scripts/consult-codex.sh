#!/usr/bin/env bash
# Compatibility shim: read-only Codex consults are handled by codex-agent.sh.
# Same interface as the old consult-codex.sh: [--cd DIR] [--model M] [--with-mcp] "<prompt>"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/codex-agent.sh" consult "$@"
