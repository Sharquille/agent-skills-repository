#!/usr/bin/env bash
# Forwarding script to the deploy-agent-skills executable
exec "$(dirname "$0")/../skills/engineering/deploy-agent-skills/scripts/deploy.sh" "$@"
