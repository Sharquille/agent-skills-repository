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
# Guard a value-taking flag: require an argument that is not another option, so
# `--title --apply` can never silently set TITLE=--apply.
need_val() {
  [ "$#" -ge 2 ] || die "$1 needs a value"
  case "$2" in -*|"") die "$1 needs a non-option value (got: '${2:-}')" ;; esac
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --install-root) MODE="install"; shift ;;
    --title) need_val "$@"; TITLE="$2"; MODE="${MODE:-project}"; shift 2 ;;
    --category) need_val "$@"; CATEGORY="$2"; shift 2 ;;
    --base) need_val "$@"; BASE="$2"; shift 2 ;;
    --allow-new-category) ALLOW_NEW_CAT=1; shift ;;
    --apply) APPLY=1; shift ;;
    -h|--help) sed -n '2,22p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

# --- json_escape: make an arbitrary string safe to embed between JSON quotes.
# Strip control chars (to spaces), then escape backslash and double-quote.
# Without this, a title like  My "cool" project  produces invalid project.json.
json_escape() {
  printf '%s' "$1" | tr '\000-\037' ' ' | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

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

# refuse symlinks in any existing ancestor of the target AND in the target
# itself — a pre-existing symlinked project dir would otherwise escape the base.
ensure_no_symlink_chain "$BASE_REAL/$CATEGORY"
[ -L "$TARGET" ] && die "refusing: target path is a symlink -> $TARGET"

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
note "seed     : build-log/{tasks.md,observations.md,artifact-manifest.json}, references/{external-references.md,tooling.md}"
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
TITLE_J="$(json_escape "$TITLE")"
CATEGORY_J="$(json_escape "$CATEGORY")"
cat > "$TARGET/project.json" <<JSON
{
  "schema_version": "1.1",
  "id": "$SLUG",
  "title": "$TITLE_J",
  "category": "$CATEGORY_J",
  "created": "$NOW",
  "phase": "intake",
  "authorization": null,
  "classification": {
    "status": "provisional",
    "archetype": null,
    "capability_flags": [],
    "data_classes": [],
    "dual_use_tier": "T2",
    "artifact_class_floor": "private",
    "publish_policy": "no-publish",
    "git_policy": "local-only"
  },
  "tasks": []
}
JSON

# event-log is append-only; seq gives a stable order independent of timestamps.
printf '{"seq":1,"ts":"%s","event":"bootstrap","slug":"%s","category":"%s"}\n' "$NOW" "$SLUG" "$CATEGORY_J" > "$TARGET/event-log.jsonl"

if [ -f "$SCRIPT_DIR/../references/project-protocol-template.md" ]; then
  cp "$SCRIPT_DIR/../references/project-protocol-template.md" "$TARGET/PROJECT-PROTOCOL.md"
fi

# Seed the first-class lifecycle files the SKILL.md workflow expects, so later
# gates (markdown hygiene, manifest, references registry) never run against a
# missing path. Minimal skeletons only; the conductor fills them per phase.
cat > "$TARGET/build-log/tasks.md" <<'MD'
# Tasks

Sequential task board (low-noise status view). One row per task; keep
reproducibility detail in `task-N.N.steps.md`, not here.

| Task | Status | Next / Blocked | Notes |
|---|---|---|---|
MD

cat > "$TARGET/build-log/observations.md" <<'MD'
# Observations

Working notes: assumptions, defaults before resolution, current-state review,
issue context, candidate decisions, and rationale. Not a checkpoint log.
MD

printf '{\n  "schema_version": "1.0",\n  "artifacts": []\n}\n' > "$TARGET/build-log/artifact-manifest.json"

cat > "$TARGET/references/external-references.md" <<'MD'
# External references

Governed registry of authoritative external sources this project relies on.
Task notes and steps ledgers cite a row here plus the advisory caveat; they do
not duplicate this table.

| ID | Source | Why authoritative | Retrieved | Advisory caveat |
|---|---|---|---|---|
MD

cat > "$TARGET/references/tooling.md" <<'MD'
# Tooling & software setup

Tool bill of materials for hands-on tasks. Each task's `tools[]` sources from
this registry: what it needs, install method, and where to obtain non-repo
artifacts.

| Tool | Version / lock | Install method | Source | Used by task |
|---|---|---|---|---|
MD

( cd "$TARGET" && git init -q && git symbolic-ref HEAD refs/heads/main 2>/dev/null || true )
echo "git remote check: $(cd "$TARGET" && git remote -v | wc -l | tr -d ' ') remotes (expected 0)"

# Created-files manifest for undo-project-build-loop: records exactly what this
# bootstrap made so a mistaken/false-start scaffold can be reversed precisely
# (never improvised). Local-only (.project is gitignored).
cat > "$TARGET/.project/bootstrap-manifest.json" <<JSON
{
  "schema_version": "1.0",
  "created_by": "bootstrap_project.sh",
  "created_at": "$NOW",
  "project_dir": "$CATEGORY/$SLUG",
  "seed_files": [
    ".gitignore", "project.json", "event-log.jsonl", "PROJECT-PROTOCOL.md",
    "build-log/tasks.md", "build-log/observations.md", "build-log/artifact-manifest.json",
    "references/external-references.md", "references/tooling.md",
    ".project/bootstrap-manifest.json"
  ],
  "seed_dirs": [
    "build-log", "evidence", ".vault", "topology", "publish", ".project", "references"
  ],
  "git_initialized": true,
  "global_pointer": "_index/last-active.json"
}
JSON

echo "Created project at $TARGET"
echo "Wrote undo manifest: $TARGET/.project/bootstrap-manifest.json"
echo "Set the global pointer next: $BASE/_index/last-active.json -> $CATEGORY/$SLUG"
