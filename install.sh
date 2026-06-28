#!/usr/bin/env bash
# Install skills and safety guardrails using the canonical deploy script.

set -euo pipefail

exec "$(dirname "$0")/scripts/deploy.sh" "$@"
