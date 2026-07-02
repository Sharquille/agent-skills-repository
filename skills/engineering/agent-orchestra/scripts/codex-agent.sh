#!/usr/bin/env bash
# codex-agent.sh - wrapper-first Codex caller for consult, review, and bounded implementation.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  codex-agent.sh consult [--cd DIR] [--model MODEL] [--with-mcp] -- "<prompt>"
  codex-agent.sh review  [--base REF|--commit SHA|--uncommitted] [--model MODEL] [--prompt TEXT]
  codex-agent.sh implement --allow-write [--cd DIR] [--model MODEL] [--scope PATH] [--allow-main] -- "<task>"

Defaults:
  consult    read-only codex exec
  review     codex review --uncommitted
  implement  workspace-write codex exec, guarded by --allow-write

The wrapper never uses danger-full-access, never bypasses sandbox/approvals, and never commits.
EOF
}

die() {
  echo "error: $*" >&2
  exit 2
}

secret_re='BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|github_pat_|gh[pousr]_[A-Za-z0-9_]{20,}|xox[baprs]-|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|password[[:space:]]*[:=]|api[_ -]?key[[:space:]]*[:=]|token[[:space:]]*[:=]'

check_prompt() {
  local prompt="$1"
  [ -n "$prompt" ] || die "prompt/task is required"
  if printf '%s' "$prompt" | grep -qiE "$secret_re"; then
    die "prompt appears to contain a secret; redact before invoking Codex"
  fi
}

ensure_codex() {
  command -v codex >/dev/null 2>&1 || die "'codex' CLI not found on PATH"
}

current_branch() {
  git -C "$1" rev-parse --abbrev-ref HEAD 2>/dev/null || true
}

run_consult() {
  local cd_dir="" model="" with_mcp=0 prompt=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --cd|-C) cd_dir="${2:-}"; shift 2 ;;
      --model|-m) model="${2:-}"; shift 2 ;;
      --with-mcp) with_mcp=1; shift ;;
      --) shift; prompt="$*"; break ;;
      -h|--help) usage; exit 0 ;;
      -*) die "unknown consult flag: $1" ;;
      *) prompt="${prompt:+$prompt }$1"; shift ;;
    esac
  done
  check_prompt "$prompt"
  ensure_codex

  local cmd=(codex exec --sandbox read-only)
  [ "$with_mcp" -eq 0 ] && cmd+=(-c 'mcp_servers={}')
  [ -n "$cd_dir" ] && cmd+=(--cd "$cd_dir")
  [ -n "$model" ] && cmd+=(-m "$model")
  cmd+=(-- "$prompt")

  echo "Codex consult: read-only; model=${model:-config-default}; cd=${cd_dir:-$PWD}" >&2
  exec "${cmd[@]}"
}

run_review() {
  local model="" prompt="" target_seen=0
  local cmd=(codex review)
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --base|--commit|--title)
        [ "$#" -ge 2 ] || die "$1 requires a value"
        cmd+=("$1" "$2")
        target_seen=1
        shift 2
        ;;
      --uncommitted)
        cmd+=(--uncommitted)
        target_seen=1
        shift
        ;;
      --model|-m)
        model="${2:-}"
        shift 2
        ;;
      --prompt)
        prompt="${2:-}"
        shift 2
        ;;
      --)
        shift
        prompt="$*"
        break
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      -*)
        die "unknown review flag: $1"
        ;;
      *)
        prompt="${prompt:+$prompt }$1"
        shift
        ;;
    esac
  done
  ensure_codex
  [ "$target_seen" -eq 1 ] || cmd+=(--uncommitted)
  [ -n "$model" ] && cmd+=(-c "model=\"$model\"")
  if [ -n "$prompt" ]; then
    check_prompt "$prompt"
    cmd+=("$prompt")
  fi

  echo "Codex review: model=${model:-config-default}" >&2
  exec "${cmd[@]}"
}

run_implement() {
  local cd_dir="$PWD" model="" prompt="" allow_write=0 allow_main=0
  local scopes=()
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --cd|-C) cd_dir="${2:-}"; shift 2 ;;
      --model|-m) model="${2:-}"; shift 2 ;;
      --scope) scopes+=("${2:-}"); shift 2 ;;
      --allow-write) allow_write=1; shift ;;
      --allow-main) allow_main=1; shift ;;
      --) shift; prompt="$*"; break ;;
      -h|--help) usage; exit 0 ;;
      -*) die "unknown implement flag: $1" ;;
      *) prompt="${prompt:+$prompt }$1"; shift ;;
    esac
  done

  [ "$allow_write" -eq 1 ] || die "implementation requires --allow-write"
  [ -d "$cd_dir" ] || die "directory not found: $cd_dir"
  check_prompt "$prompt"
  ensure_codex

  local branch
  branch="$(current_branch "$cd_dir")"
  case "$branch" in
    main|master)
      [ "$allow_main" -eq 1 ] || die "refusing workspace-write on branch '$branch'; create/switch to a working branch or pass --allow-main explicitly"
      ;;
  esac

  local scope_text="No explicit scope paths were provided. Infer the minimal safe scope from the task."
  if [ "${#scopes[@]}" -gt 0 ]; then
    scope_text="Only modify these paths unless the task is impossible without expanding scope:"
    local scope
    for scope in "${scopes[@]}"; do
      [ -n "$scope" ] || die "--scope requires a non-empty path"
      scope_text="$scope_text
- $scope"
    done
  fi

  local guarded_prompt
  guarded_prompt="You are Codex running as a bounded implementation agent.

Task:
$prompt

Scope:
$scope_text

Rules:
- Make the smallest correct patch.
- Do not commit, push, create PRs, or alter remotes.
- Do not delete user data or broad directories.
- Do not read or modify secret-bearing files such as .env, private keys, tokens, or credential stores.
- Run focused validation if safe and available.
- Finish with a concise summary of changed files, tests run, and any residual risks."

  local cmd=(codex exec --sandbox workspace-write -c 'mcp_servers={}' --cd "$cd_dir")
  [ -n "$model" ] && cmd+=(-m "$model")
  cmd+=(-- "$guarded_prompt")

  echo "Codex implementation: workspace-write; model=${model:-config-default}; cd=$cd_dir; branch=${branch:-unknown}" >&2
  exec "${cmd[@]}"
}

main() {
  local mode="${1:-}"
  case "$mode" in
    consult) shift; run_consult "$@" ;;
    review) shift; run_review "$@" ;;
    implement) shift; run_implement "$@" ;;
    -h|--help|"") usage ;;
    *) die "unknown mode: $mode" ;;
  esac
}

main "$@"
