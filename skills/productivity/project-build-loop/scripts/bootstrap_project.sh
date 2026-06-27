#!/usr/bin/env bash
# bootstrap_project.sh — safe, idempotent project/root creation for the
# project-build-loop conductor. Dry-run by default; pass --apply to write.
#
# Usage:
#   bootstrap_project.sh --install-root [--apply]
#       Create ~/Documents/development/projects with category folders + _index.
#   bootstrap_project.sh --title "<desc/title>" --category <cat> [--apply]
#       Create one project under projects/<category>/<slug>.
#
# Options:
#   --base <dir>        Override approved base (default ~/Documents/development/projects)
#   --allow-new-category  Permit a category not in the built-in allowlist
#   --apply             Actually write (otherwise prints a dry-run plan only)
#
# SAFETY (do not weaken): slugifies the title; rejects '..', absolute paths, and
# symlink components; realpath-guards the target under the approved base; refuses
# a non-empty target that lacks a project.json marker; git init is LOCAL ONLY
# (never adds a remote). Exit: 0 ok, 2 usage/precondition error.

set -uo pipefail

BASE_DEFAULT="$HOME/Documents/development/projects"
BASE="$BASE_DEFAULT"
MODE=""
TITLE=""
CATEGORY=""
APPLY=0
ALLOW_NEW_CAT=0
ALLOWED_CATS="networking-and-cybersecurity software-development"

die() { echo "error: $*" >&2; exit 2; }
note() { echo "  $*"; }

while [ "$#" -gt 0 ]; do
  case "$1" in
    --install-root) MODE="install"; shift ;;
    --title) [ "$#" -ge 2 ] || die "--title needs a value"; TITLE="$2"; MODE="${MODE:-project}"; shift 2 ;;
    --category) [ "$#" -ge 2 ] || die "--category needs a value"; CATEGORY="$2"; shift 2 ;;
    --base) [ "$#" -ge 2 ] || die "--base needs a value"; BASE="$2"; shift 2 ;;
    --allow-new-category) ALLOW_NEW_CAT=1; shift ;;
    --apply) APPLY=1; shift ;;
    -h|--help) sed -n '2,22p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

# --- slugify: lowercase, spaces/underscores -> '-', strip unsafe, collapse '-'
slugify() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-+/-/g' \
    | cut -c1-64
}

# --- reject obviously unsafe inputs early
reject_unsafe() {
  case "$1" in
    *..*) die "path component contains '..': $1" ;;
    /*)   die "absolute path not allowed here: $1" ;;
  esac
}

ensure_no_symlink_chain() {
  # walk each existing ancestor; refuse if any is a symlink
  local p="$1" cur=""
  local IFS='/'
  for part in $p; do
    [ -z "$part" ] && { cur="/"; continue; }
    if [ "$cur" = "/" ]; then cur="/$part"; else cur="$cur/$part"; fi
    if [ -L "$cur" ]; then die "refusing: symlink in path -> $cur"; fi
  done
}

# --- realpath guard: resolved target must stay under resolved base
resolve() { cd "$1" 2>/dev/null && pwd -P; }

if [ "$MODE" = "install" ]; then
  echo "Install-root plan (base: $BASE):"
  note "mkdir -p $BASE"
  for c in $ALLOWED_CATS; do note "mkdir -p $BASE/$c"; done
  note "mkdir -p $BASE/_index"
  note "write   $BASE/_index/last-active.json  -> {\"last_active\": null}"
  if [ "$APPLY" -ne 1 ]; then echo "(dry-run; re-run with --apply to write)"; exit 0; fi
  mkdir -p "$BASE" || die "cannot create base"
  ensure_no_symlink_chain "$(resolve "$BASE")"
  for c in $ALLOWED_CATS; do mkdir -p "$BASE/$c"; done
  mkdir -p "$BASE/_index"
  [ -f "$BASE/_index/last-active.json" ] || printf '{\n  "last_active": null\n}\n' > "$BASE/_index/last-active.json"
  echo "Installed root at $BASE"
  exit 0
fi

[ "$MODE" = "project" ] || die "specify --install-root or --title"
[ -n "$TITLE" ] || die "--title is required"
[ -n "$CATEGORY" ] || die "--category is required"
reject_unsafe "$CATEGORY"
reject_unsafe "$TITLE"

# category allowlist
cat_ok=0
for c in $ALLOWED_CATS; do [ "$c" = "$CATEGORY" ] && cat_ok=1; done
[ "$cat_ok" -eq 1 ] || [ "$ALLOW_NEW_CAT" -eq 1 ] || die "category '$CATEGORY' not in allowlist; use --allow-new-category to override"

SLUG="$(slugify "$TITLE")"
[ -n "$SLUG" ] || die "title slugified to empty; pick a more descriptive title"

[ -d "$BASE" ] || die "approved base does not exist: $BASE (run --install-root first)"
BASE_REAL="$(resolve "$BASE")" || die "cannot resolve base"
TARGET="$BASE/$CATEGORY/$SLUG"

# refuse symlinks in any existing ancestor of the target
ensure_no_symlink_chain "$BASE_REAL/$CATEGORY"

# no-clobber: existing non-empty dir must already be a project
if [ -d "$TARGET" ]; then
  if [ -f "$TARGET/project.json" ]; then
    echo "Project already exists (idempotent): $TARGET"; exit 0
  fi
  if [ -n "$(ls -A "$TARGET" 2>/dev/null)" ]; then
    die "target exists, is non-empty, and lacks project.json (refusing to clobber): $TARGET"
  fi
fi

echo "Project bootstrap plan:"
note "category : $CATEGORY"
note "slug     : $SLUG   (from: $TITLE)"
note "target   : $TARGET"
note "mkdir    : build-log/ evidence/ .vault/ topology/ publish/ .project/ references/"
note "git init : LOCAL ONLY (no remote)"
note "write    : .gitignore, project.json, event-log.jsonl, PROJECT-PROTOCOL.md"
if [ "$APPLY" -ne 1 ]; then echo "(dry-run; re-run with --apply to write)"; exit 0; fi

# verify resolved category dir stays under base after creation
mkdir -p "$BASE/$CATEGORY" || die "cannot create category dir"
CAT_REAL="$(resolve "$BASE/$CATEGORY")" || die "cannot resolve category dir"
case "$CAT_REAL/" in
  "$BASE_REAL"/*) : ;;
  *) die "resolved category dir escaped approved base: $CAT_REAL" ;;
esac

mkdir -p "$TARGET"/build-log "$TARGET"/evidence "$TARGET"/.vault \
         "$TARGET"/topology "$TARGET"/publish "$TARGET"/.project "$TARGET"/references

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../assets/gitignore-baseline" ]; then
  cp "$SCRIPT_DIR/../assets/gitignore-baseline" "$TARGET/.gitignore"
else
  printf '.env*\n*.key\n*.pem\n*.p12\n*.pfx\nevidence/\n.vault/\n.project/\n*.pcap\n*.pcapng\n' > "$TARGET/.gitignore"
fi

NOW="$(date +%Y-%m-%dT%H:%M:%S%z)"
cat > "$TARGET/project.json" <<JSON
{
  "schema_version": "1.0",
  "id": "$SLUG",
  "title": "$TITLE",
  "category": "$CATEGORY",
  "created": "$NOW",
  "phase": "intake",
  "classification": { "status": "provisional", "dual_use_tier": "T2", "publish_policy": "no-publish", "git_policy": "local-only" },
  "tasks": []
}
JSON

printf '{"ts":"%s","event":"bootstrap","slug":"%s","category":"%s"}\n' "$NOW" "$SLUG" "$CATEGORY" > "$TARGET/event-log.jsonl"

if [ -f "$SCRIPT_DIR/../references/project-protocol-template.md" ]; then
  cp "$SCRIPT_DIR/../references/project-protocol-template.md" "$TARGET/PROJECT-PROTOCOL.md"
fi

( cd "$TARGET" && git init -q && git symbolic-ref HEAD refs/heads/main 2>/dev/null || true )
echo "git remote check: $(cd "$TARGET" && git remote -v | wc -l | tr -d ' ') remotes (expected 0)"

echo "Created project at $TARGET"
echo "Set the global pointer next: $BASE/_index/last-active.json -> $CATEGORY/$SLUG"
