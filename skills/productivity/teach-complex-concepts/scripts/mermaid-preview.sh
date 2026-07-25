#!/usr/bin/env bash
#
# mermaid-preview.sh — ephemeral localhost renderer for teaching diagrams.
#
# Purpose: give the tutor a real renderer during a live lesson, so Mermaid
# syntax that fails silently (labels beginning with a list marker, literal
# newlines, overflowing LR chains) is caught before the learner sees it, and
# so "draw it" can show a rendered diagram instead of raw code.
#
# This is a PREVIEW, never a deliverable. It writes only to a scratch
# directory, serves on 127.0.0.1, and dies with the session. It never writes
# into a vault, and diagram persistence stays owned by obsidian-study-loop.
#
# Usage:
#   mermaid-preview.sh start [--dir DIR] [--port PORT] [--open]
#   mermaid-preview.sh stop  [--dir DIR]
#   mermaid-preview.sh status [--dir DIR]
#
# The tutor drives the page by writing DIR/diagrams.json; the page polls it
# every 1.5s and re-renders on change. Schema:
#
#   {
#     "title": "AES — the block cipher anchor",
#     "subtitle": "optional line under the title",
#     "panels": [
#       {
#         "title": "Panel 1 — One invocation",
#         "note": "Plain-text description of the diagram, required for access.",
#         "mermaid": "flowchart LR\n  A[\"In\"] --> B[\"Out\"]"
#       }
#     ]
#   }
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS_DIR="$(cd "${SCRIPT_DIR}/../assets" && pwd)"

DEFAULT_DIR="${TMPDIR:-/tmp}/teach-complex-concepts-preview"
WORKDIR="${DEFAULT_DIR}"
PORT=""
OPEN_BROWSER=0
CMD="${1:-}"
[ $# -gt 0 ] && shift || true

while [ $# -gt 0 ]; do
  case "$1" in
    --dir)  WORKDIR="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --open) OPEN_BROWSER=1; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

case "$WORKDIR" in
  /*) ;;
  *) WORKDIR="${PWD}/${WORKDIR}" ;;
esac

PID_FILE="${WORKDIR}/.server.pid"
PORT_FILE="${WORKDIR}/.server.port"

die() { echo "mermaid-preview: $*" >&2; exit 1; }

# Hard boundary: a preview must never be able to land inside a study vault or
# a tracked repository. Walk up from the target and refuse if we are inside one.
assert_ephemeral_location() {
  local dir probe
  dir="$1"
  probe="$dir"
  while [ -n "$probe" ] && [ "$probe" != "/" ]; do
    if [ -e "${probe}/STUDY-PROTOCOL.md" ] || [ -d "${probe}/.obsidian" ]; then
      die "refusing to run inside an Obsidian study vault (${probe}).
      This renderer is preview-only. Point --dir at a scratch directory;
      diagram persistence belongs to obsidian-study-loop, not here."
    fi
    if [ -d "${probe}/.git" ]; then
      die "refusing to run inside a git working tree (${probe}).
      This renderer is preview-only and must not create committable files.
      Point --dir at a scratch directory instead."
    fi
    probe="$(dirname "$probe")"
  done
}

pick_port() {
  local candidate
  if [ -n "$PORT" ]; then echo "$PORT"; return; fi
  for candidate in $(seq 8477 8487); do
    if ! nc -z 127.0.0.1 "$candidate" >/dev/null 2>&1; then
      echo "$candidate"; return
    fi
  done
  die "no free port in range 8477-8487; pass --port explicitly."
}

running_pid() {
  [ -f "$PID_FILE" ] || return 1
  local pid; pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  [ -n "$pid" ] || return 1
  kill -0 "$pid" >/dev/null 2>&1 || return 1
  echo "$pid"
}

cmd_start() {
  command -v python3 >/dev/null 2>&1 || die "python3 is required to serve the preview."
  [ -f "${ASSETS_DIR}/mermaid.min.js" ] || die "missing ${ASSETS_DIR}/mermaid.min.js"
  [ -f "${ASSETS_DIR}/preview.html" ]   || die "missing ${ASSETS_DIR}/preview.html"

  assert_ephemeral_location "$WORKDIR"

  if pid="$(running_pid)"; then
    echo "already running (pid ${pid}) at http://127.0.0.1:$(cat "$PORT_FILE")/"
    return 0
  fi

  mkdir -p "$WORKDIR"
  cp "${ASSETS_DIR}/preview.html"   "${WORKDIR}/index.html"
  cp "${ASSETS_DIR}/mermaid.min.js" "${WORKDIR}/mermaid.min.js"
  [ -f "${WORKDIR}/diagrams.json" ] || cat > "${WORKDIR}/diagrams.json" <<'JSON'
{ "title": "Mermaid Preview", "subtitle": "waiting for the first diagram", "panels": [] }
JSON

  local port; port="$(pick_port)"
  ( cd "$WORKDIR" && nohup python3 -m http.server "$port" --bind 127.0.0.1 \
      >"${WORKDIR}/server.log" 2>&1 & echo $! > "$PID_FILE" )
  echo "$port" > "$PORT_FILE"

  sleep 1
  running_pid >/dev/null || { cat "${WORKDIR}/server.log" >&2; die "server failed to start."; }

  local url="http://127.0.0.1:${port}/"
  echo "preview live at ${url}"
  echo "write diagrams to ${WORKDIR}/diagrams.json (auto-reloads, no refresh needed)"
  if [ "$OPEN_BROWSER" -eq 1 ] && command -v open >/dev/null 2>&1; then
    open "$url"
  fi
  return 0
}

cmd_stop() {
  if pid="$(running_pid)"; then
    kill "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo "stopped (pid ${pid})"
  else
    echo "not running"
  fi
}

cmd_status() {
  if pid="$(running_pid)"; then
    echo "running (pid ${pid}) at http://127.0.0.1:$(cat "$PORT_FILE")/ · dir ${WORKDIR}"
  else
    echo "not running · dir ${WORKDIR}"
  fi
}

case "$CMD" in
  start)  cmd_start ;;
  stop)   cmd_stop ;;
  status) cmd_status ;;
  *) sed -n '3,25p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
