#!/usr/bin/env bash
# Shared filesystem/index write-scope checks for implementation wrappers.
# This file is sourced; it does not execute a wrapper by itself.

orchestra_normalize_scope() {
  local raw="$1" scope component lower

  [ -n "$raw" ] || {
    echo "error: --scope requires a non-empty repository-relative path" >&2
    return 2
  }
  case "$raw" in
    /*|~|~/*) echo "error: --scope must be repository-relative, not '$raw'" >&2; return 2 ;;
    *$'\n'*|*$'\r'*) echo "error: --scope may not contain newline characters" >&2; return 2 ;;
    *'*'*|*'?'*|*'['*|*']'*) echo "error: --scope is a literal path prefix, not a glob: '$raw'" >&2; return 2 ;;
  esac

  scope="$raw"
  while [ "${scope#./}" != "$scope" ]; do scope="${scope#./}"; done
  while [ "$scope" != "/" ] && [ "${scope%/}" != "$scope" ]; do scope="${scope%/}"; done
  [ -n "$scope" ] || scope="."
  if [ "$scope" != "." ]; then
    case "/$scope/" in
      *'/../'*|*'/./'*|*'//'*) echo "error: --scope contains an ambiguous path segment: '$raw'" >&2; return 2 ;;
      *'/.git/'*) echo "error: refusing write scope under .git: '$raw'" >&2; return 2 ;;
    esac
  fi

  while IFS= read -r component; do
    lower=$(printf '%s' "$component" | tr '[:upper:]' '[:lower:]')
    case "$lower" in
      .env|.env.*|.envrc|id_rsa|id_dsa|id_ecdsa|id_ed25519|*.pem|*.key|*.p12|*.pfx|*.jks|secret|secrets|secrets.*|credential|credentials|credentials.*|token|tokens|tokens.*)
        echo "error: refusing likely secret-bearing write scope: '$raw'" >&2
        return 2
        ;;
    esac
  done <<EOF
$(printf '%s' "$scope" | tr '/' '\n')
EOF
  printf '%s' "$scope"
}

orchestra_path_in_scopes() {
  local path="$1" scope
  shift
  for scope in "$@"; do
    [ "$scope" = "." ] && return 0
    case "$path" in "$scope"|"$scope"/*) return 0 ;; esac
  done
  return 1
}

orchestra_path_is_scope_ancestor() {
  local path="$1" scope
  shift
  [ "$path" = "." ] && return 0
  for scope in "$@"; do
    case "$scope" in "$path"/*) return 0 ;; esac
  done
  return 1
}

orchestra_path_is_secret_shaped() {
  local path="$1" component lower
  while IFS= read -r component; do
    lower=$(printf '%s' "$component" | tr '[:upper:]' '[:lower:]')
    case "$lower" in
      .env|.env.*|.envrc|id_rsa|id_dsa|id_ecdsa|id_ed25519|*.pem|*.key|*.p12|*.pfx|*.jks|secret|secrets|secrets.*|credential|credentials|credentials.*|token|tokens|tokens.*) return 0 ;;
    esac
  done <<EOF
$(printf '%s' "$path" | tr '/' '\n')
EOF
  return 1
}

# Reject scopes whose existing path, parent path, or descendants are symlinks.
# Also reject an existing secret-shaped descendant, including ignored files.
orchestra_validate_scope_tree() {
  local repo="$1" scope candidate rel path_file component resolved
  shift

  # Any repository symlink that resolves outside the repository is an escape
  # hatch even when its link path is outside the allowed scope. Reject it
  # before the delegate starts. Unresolvable/broken links are rejected too.
  path_file=$(mktemp "${TMPDIR:-/tmp}/orchestra-repo-links.XXXXXX") || return 2
  if ! find "$repo" -path "$repo/.git" -prune -o -type l -print0 >"$path_file"; then
    rm -f "$path_file"
    echo "error: could not inspect repository symlinks" >&2
    return 2
  fi
  while IFS= read -r -d '' candidate; do
    rel="${candidate#"$repo/"}"
    resolved=$(realpath "$candidate" 2>/dev/null) || {
      rm -f "$path_file"
      echo "error: refusing unresolved repository symlink: $rel" >&2
      return 2
    }
    case "$resolved" in
      "$repo"|"$repo"/*) : ;;
      *) rm -f "$path_file"; echo "error: refusing repository symlink outside root: $rel -> $resolved" >&2; return 2 ;;
    esac
  done <"$path_file"
  rm -f "$path_file"

  for scope in "$@"; do
    candidate="$repo"
    if [ "$scope" != "." ]; then
      while IFS= read -r component; do
        candidate="$candidate/$component"
        if [ -L "$candidate" ]; then
          echo "error: refusing --scope through symlink: ${candidate#"$repo/"}" >&2
          return 2
        fi
      done <<EOF
$(printf '%s' "$scope" | tr '/' '\n')
EOF
    fi

    candidate="$repo/$scope"
    [ "$scope" = "." ] && candidate="$repo"
    [ -e "$candidate" ] || continue
    path_file=$(mktemp "${TMPDIR:-/tmp}/orchestra-scope-tree.XXXXXX") || return 2
    if ! find "$candidate" -path "$repo/.git" -prune -o \( -type f -o -type l -o -type d \) -print0 >"$path_file"; then
      rm -f "$path_file"
      echo "error: could not inspect --scope tree: $scope" >&2
      return 2
    fi
    while IFS= read -r -d '' candidate; do
      if [ "$candidate" = "$repo" ]; then rel="."; else rel="${candidate#"$repo/"}"; fi
      if [ -L "$candidate" ]; then
        rm -f "$path_file"
        echo "error: refusing --scope containing symlink: $rel" >&2
        return 2
      fi
      if orchestra_path_is_secret_shaped "$rel"; then
        rm -f "$path_file"
        echo "error: refusing --scope containing likely secret-bearing path: $rel" >&2
        return 2
      fi
    done <"$path_file"
    rm -f "$path_file"
  done
  return 0
}

# Validate the small, task-local acceptance record required when a caller says
# this implementation is plan-gated. The record is evidence for the conductor;
# its contents are not forwarded to the delegate.
orchestra_validate_plan_record() {
  local record="$1" plan_id
  [ -f "$record" ] && [ ! -L "$record" ] || {
    echo "error: --plan-record must name a regular, non-symlink file: $record" >&2
    return 2
  }
  [ "$(wc -c <"$record" | tr -d ' ')" -le 65536 ] || {
    echo "error: --plan-record exceeds 64 KiB: $record" >&2
    return 2
  }
  plan_id=$(sed -nE 's/^[[:space:]]*plan:[[:space:]]*(P[1-9][0-9]*)[[:space:]]*$/\1/p' "$record" | head -1)
  [ -n "$plan_id" ] || {
    echo "error: --plan-record needs 'plan: P<n>'" >&2
    return 2
  }
  grep -Eq '^[[:space:]]*status:[[:space:]]*accepted[[:space:]]*$' "$record" || {
    echo "error: --plan-record needs 'status: accepted'" >&2
    return 2
  }
  grep -Eq '^[[:space:]]*independent-review:[[:space:]]*complete[[:space:]]*$' "$record" || {
    echo "error: --plan-record needs 'independent-review: complete'" >&2
    return 2
  }
  grep -Eq '^[[:space:]]*blocking-findings:[[:space:]]*(none|resolved)[[:space:]]*$' "$record" || {
    echo "error: --plan-record needs 'blocking-findings: none|resolved'" >&2
    return 2
  }
  printf '%s' "$plan_id"
}

orchestra_sha256_stream() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum | awk '{print $1}'
  else
    openssl dgst -sha256 | awk '{print $NF}'
  fi
}

orchestra_file_mode() {
  if stat -f '%Lp' "$1" >/dev/null 2>&1; then stat -f '%Lp' "$1"
  else stat -c '%a' "$1"
  fi
}

orchestra_snapshot_record() {
  local bucket="$1" path="$2" state="$3" key
  key=$(printf '%s' "$path" | orchestra_sha256_stream) || return 2
  printf '%s' "$path" >"$bucket/$key.path" || return 2
  printf '%s' "$state" >"$bucket/$key.state" || return 2
}

# Capture every filesystem object and index entry outside the allowed scopes,
# plus HEAD. Regular-file contents are represented only by SHA-256 digests;
# their bytes never leave the local hashing process or enter a model prompt.
orchestra_scope_snapshot_create() {
  local repo="$1" state_dir="$2" entry path rel full mode digest index_meta path_file refs_hash config_hash reflog_hash
  shift 2
  local scopes=("$@")

  mkdir -p "$state_dir/fs" "$state_dir/index" || return 2
  git -C "$repo" rev-parse --verify HEAD >"$state_dir/head" 2>/dev/null || {
    echo "error: could not snapshot repository HEAD" >&2; return 2;
  }
  refs_hash=$(git -C "$repo" for-each-ref --format='%(refname) %(objectname) %(symref)' | orchestra_sha256_stream) || {
    echo "error: could not snapshot Git refs" >&2; return 2;
  }
  config_hash=$(git -C "$repo" config --local --null --list | orchestra_sha256_stream) || {
    echo "error: could not snapshot local Git configuration" >&2; return 2;
  }
  reflog_hash=$(git -C "$repo" reflog show --all --format='%H %gd %gs' | orchestra_sha256_stream) || {
    echo "error: could not snapshot Git reflogs" >&2; return 2;
  }
  printf '%s\n%s\n%s\n' "$refs_hash" "$config_hash" "$reflog_hash" >"$state_dir/git-metadata" || return 2

  path_file="$state_dir/find.paths"
  if ! find "$repo" -path "$repo/.git" -prune -o \( -type f -o -type l -o -type d \) -print0 >"$path_file"; then
    echo "error: could not snapshot repository files" >&2
    return 2
  fi
  while IFS= read -r -d '' full; do
    if [ "$full" = "$repo" ]; then rel="."; else rel="${full#"$repo/"}"; fi
    orchestra_path_in_scopes "$rel" "${scopes[@]}" && continue
    if [ -d "$full" ] && [ ! -L "$full" ]; then
      orchestra_path_is_scope_ancestor "$rel" "${scopes[@]}" && continue
      mode=$(orchestra_file_mode "$full") || return 2
      orchestra_snapshot_record "$state_dir/fs" "$rel" "dir|$mode" || return 2
      continue
    fi
    mode=$(orchestra_file_mode "$full") || return 2
    if [ -L "$full" ]; then
      digest=$(readlink "$full") || return 2
      orchestra_snapshot_record "$state_dir/fs" "$rel" "link|$mode|$digest" || return 2
    else
      digest=$(orchestra_sha256_stream <"$full") || return 2
      orchestra_snapshot_record "$state_dir/fs" "$rel" "file|$mode|$digest" || return 2
    fi
  done <"$path_file"

  if ! git -C "$repo" ls-files --stage -z >"$state_dir/index.paths"; then
    echo "error: could not snapshot repository index" >&2
    return 2
  fi
  while IFS= read -r -d '' entry; do
    case "$entry" in *$'\t'*) : ;; *) echo "error: malformed Git index record" >&2; return 2 ;; esac
    path="${entry#*$'\t'}"
    orchestra_path_in_scopes "$path" "${scopes[@]}" && continue
    index_meta="${entry%%$'\t'*}"
    orchestra_snapshot_record "$state_dir/index" "$path" "$index_meta" || return 2
  done <"$state_dir/index.paths"
  rm -f "$path_file" "$state_dir/index.paths"
  return 0
}

orchestra_compare_snapshot_bucket() {
  local before="$1" after="$2" label="$3" file key path found=0
  for file in "$before"/*.state; do
    [ -e "$file" ] || continue
    key="${file##*/}"; key="${key%.state}"
    if [ ! -f "$after/$key.state" ] || ! cmp -s "$file" "$after/$key.state"; then
      path=$(<"$before/$key.path")
      printf '  %s (%s changed or removed)\n' "$path" "$label" >&2
      found=1
    fi
  done
  for file in "$after"/*.state; do
    [ -e "$file" ] || continue
    key="${file##*/}"; key="${key%.state}"
    if [ ! -f "$before/$key.state" ]; then
      path=$(<"$after/$key.path")
      printf '  %s (%s added)\n' "$path" "$label" >&2
      found=1
    fi
  done
  return "$found"
}

orchestra_scope_snapshot_verify() {
  local repo="$1" baseline="$2" phase="$3" current head_before head_after violation=0
  shift 3
  local scopes=("$@")

  orchestra_validate_scope_tree "$repo" "${scopes[@]}" || return 2
  current=$(mktemp -d "${TMPDIR:-/tmp}/orchestra-scope-current.XXXXXX") || {
    echo "error: could not create temporary scope snapshot" >&2; return 2;
  }
  if ! orchestra_scope_snapshot_create "$repo" "$current" "${scopes[@]}"; then
    rm -rf "$current"
    echo "error: could not inspect repository after delegation" >&2
    return 2
  fi

  head_before=$(<"$baseline/head")
  head_after=$(<"$current/head")
  if [ "$head_before" != "$head_after" ]; then
    echo "error: repository HEAD changed during delegation ($head_before -> $head_after)" >&2
    violation=1
  fi
  if ! cmp -s "$baseline/git-metadata" "$current/git-metadata"; then
    echo "error: Git refs, local config, or reflogs changed during delegation" >&2
    violation=1
  fi
  orchestra_compare_snapshot_bucket "$baseline/fs" "$current/fs" "filesystem" || violation=1
  orchestra_compare_snapshot_bucket "$baseline/index" "$current/index" "index" || violation=1
  rm -rf "$current"

  if [ "$violation" -ne 0 ]; then
    echo "error: changes outside --scope detected $phase; no files or commits were reverted" >&2
    return 1
  fi
  return 0
}

orchestra_scope_snapshot_destroy() {
  local state_dir="${1:-}"
  [ -n "$state_dir" ] || return 0
  case "$state_dir" in
    "${TMPDIR:-/tmp}"/orchestra-scope-state.*) rm -rf "$state_dir" ;;
    *) echo "warning: refusing to remove unexpected scope snapshot path: $state_dir" >&2; return 2 ;;
  esac
}
