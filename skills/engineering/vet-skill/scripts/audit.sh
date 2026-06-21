#!/usr/bin/env bash
# audit.sh — static security audit for an untrusted skill before installation.
#
# Usage:   audit.sh <path-to-skill-dir-or-file> [more paths...]
# Example: audit.sh /tmp/skill-audit
#
# Scans Markdown/text files for the things that make a downloaded skill dangerous:
#   1. Hidden / bidi / zero-width Unicode (invisible prompt injection)
#   2. External URLs / network-fetch references (side-loading, chained deps)
#   3. Embedded scripts / shell / eval (code execution)
#   4. Prompt-injection / instruction-hijack phrasing
#   5. Active code fences (non-inert languages)
#   6. Frontmatter YAML validity (a malformed SKILL.md manifest won't load)
#
# Exit code 0 = clean, 1 = findings need human review. Checks 1-5 are advisory:
# many are false positives in *security* skills (which legitimately discuss
# "exfiltration", "credentials", etc.) — always read the matched context.
# Check 6 is NOT advisory: a frontmatter parse failure is a hard "fix before install".

set -uo pipefail

if [ "$#" -lt 1 ]; then
  echo "usage: audit.sh <path> [path...]" >&2
  exit 2
fi

# Collect target files (.md/.txt/.markdown), skipping LICENSE noise is optional.
FILES=()
for target in "$@"; do
  if [ -f "$target" ]; then
    FILES+=("$target")
  elif [ -d "$target" ]; then
    while IFS= read -r f; do FILES+=("$f"); done \
      < <(find "$target" -type f \( -name '*.md' -o -name '*.txt' -o -name '*.markdown' \) | sort)
  else
    echo "skip (not found): $target" >&2
  fi
done

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "No .md/.txt files found to audit." >&2
  exit 2
fi

FINDINGS=0
line() { printf '%s\n' "===================================================================="; }

# --- 1. Hidden / bidi / zero-width Unicode -------------------------------------
line; echo "1. HIDDEN / BIDI / ZERO-WIDTH UNICODE"; line
HID=0
for f in "${FILES[@]}"; do
  if hits=$(LC_ALL=C grep -nP '[^\x09\x0a\x20-\x7e]' "$f" 2>/dev/null); then
    # Classify the actual code points; only flag dangerous ranges.
    bad=$(printf '%s' "$hits" | python3 -c '
import sys,unicodedata
DANGER=set(range(0x200b,0x2010))|{0x200e,0x200f,0x061c,0xfeff}|set(range(0x202a,0x2030))|set(range(0x2066,0x206a))
found=set()
for ch in sys.stdin.read():
    if ord(ch) in DANGER: found.add(ch)
for ch in sorted(found,key=ord):
    print(f"U+{ord(ch):04X} {unicodedata.name(ch,\"?\")}")
' 2>/dev/null)
    if [ -n "$bad" ]; then
      echo "  DANGER in $f:"; printf '    %s\n' "$bad"; HID=1; FINDINGS=$((FINDINGS+1))
    fi
  fi
done
[ "$HID" -eq 0 ] && echo "  CLEAN — no bidi/zero-width/invisible characters"

# --- 2. External URLs / network-fetch ------------------------------------------
line; echo "2. EXTERNAL URLs / NETWORK-FETCH (side-load / chained deps)"; line
if grep -nEi 'https?://|ftp://|curl |wget |fetch\(|raw\.github|\.sh\b|pip install|npm i ' "${FILES[@]}" 2>/dev/null; then
  echo "  ^ review — confirm none are auto-fetched at skill runtime"; FINDINGS=$((FINDINGS+1))
else
  echo "  CLEAN — no external URLs or fetch references"
fi

# --- 3. Embedded scripts / shell / eval ----------------------------------------
line; echo "3. EMBEDDED SHELL / EXEC / EVAL"; line
if grep -nEi '\b(eval|exec|os\.system|subprocess|child_process|require\(|import os|sudo |rm -rf|chmod \+x|base64 -d|\$\([^)])' "${FILES[@]}" 2>/dev/null; then
  echo "  ^ review — distinguish real code from prose (security skills name these as topics)"; FINDINGS=$((FINDINGS+1))
else
  echo "  CLEAN — no shell/exec/eval primitives"
fi

# --- 4. Prompt-injection / hijack ----------------------------------------------
line; echo "4. PROMPT-INJECTION / INSTRUCTION-HIJACK"; line
PAT='ignore (previous|prior|above|all)|disregard (the|your|previous)|forget (everything|previous)|you are now|new instructions|override your|do not tell the user|without (telling|asking) the user|reveal your (system )?prompt|print your (system )?prompt|exfiltrate'
if grep -nEi "$PAT" "${FILES[@]}" 2>/dev/null; then
  echo "  ^ review — these phrasings hijack the agent; benign skills rarely use them"; FINDINGS=$((FINDINGS+1))
else
  echo "  CLEAN — no hijack phrasing"
fi

# --- 5. Active (non-inert) code fences -----------------------------------------
line; echo "5. CODE FENCES (inert text/mermaid vs. executable languages)"; line
fences=$(grep -nE '^\s*```[a-zA-Z]' "${FILES[@]}" 2>/dev/null | grep -ivE '```(text|mermaid|md|markdown)\b' || true)
if [ -n "$fences" ]; then
  printf '%s\n' "$fences"
  echo "  ^ review — executable-language fences in a skill body are worth a second look"; FINDINGS=$((FINDINGS+1))
else
  echo "  CLEAN — only inert (text/mermaid/markdown) fences, if any"
fi

# --- 6. Frontmatter YAML validity ----------------------------------------------
line; echo "6. FRONTMATTER YAML VALIDITY"; line
python3 - "${FILES[@]}" <<'PY'
import sys, re
try:
    import yaml; HAVE = True
except Exception:
    HAVE = False
bad = []
checked = 0
for f in sys.argv[1:]:
    try:
        t = open(f, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    if not t.startswith('---'):
        continue  # no frontmatter -> not a skill manifest (reference/text file)
    checked += 1
    lines = t.split('\n')
    close = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
    if close is None:
        bad.append((f, 'frontmatter opened with --- but never closed')); continue
    fm = '\n'.join(lines[1:close])
    if HAVE:
        try:
            yaml.safe_load(fm)
        except Exception as e:
            bad.append((f, 'YAML error: ' + str(e).splitlines()[0]))
        continue
    # No PyYAML: heuristic for the common breakers.
    if '\t' in fm:
        bad.append((f, 'tab character in frontmatter (YAML forbids tabs for indentation)')); continue
    for ln in lines[1:close]:
        if not ln or ln[0] in ' #':
            continue
        m = re.match(r'^([\w.-]+):(.*)$', ln)
        if not m:
            continue
        val = m.group(2).strip()
        # unquoted, non-block scalar that contains a colon-space (or trailing colon)
        if val and val[0] not in '"\'|>[{&*!' and re.search(r':\s|:$', val):
            bad.append((f, f'unquoted "{m.group(1)}" value contains \': \' — quote it or use a \'>-\' block scalar'))
            break
for f, e in bad:
    print(f'  BROKEN: {f}')
    print(f'          {e}')
if checked == 0:
    print('  (no frontmatter files in scope)')
elif not bad:
    print(f'  CLEAN — frontmatter parses in all {checked} manifest file(s)' + ('' if HAVE else ' (heuristic; PyYAML not installed)'))
sys.exit(1 if bad else 0)
PY
fm_rc=$?
if [ "$fm_rc" -ne 0 ]; then
  echo "  ^ FIX before install/commit — a malformed manifest fails to load (stricter parsers like Codex reject it)."
  FINDINGS=$((FINDINGS+1))
fi

# --- Verdict -------------------------------------------------------------------
echo ""; line
if [ "$FINDINGS" -eq 0 ]; then
  echo "VERDICT: ✅ CLEAN — no findings across ${#FILES[@]} file(s). Safe to install."
  exit 0
else
  echo "VERDICT: ⚠️  $FINDINGS check(s) produced matches across ${#FILES[@]} file(s)."
  echo "Read the matched context above before installing — many are false positives"
  echo "in security-themed skills, but each must be eyeballed, not assumed benign."
  exit 1
fi
