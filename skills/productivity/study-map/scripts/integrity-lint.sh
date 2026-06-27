#!/usr/bin/env bash
# integrity-lint.sh — verify a study-map's nodes, edges, wikilinks, and tags all
# resolve to real, IN-SCOPE content. Two failure classes:
#   DANGLING    — points at something that does not exist.
#   UNWARRANTED — points at a real file that is scaffolding, not study content
#                 (e.g. CLAUDE.md / AGENTS.md / GEMINI.md / STUDY-PROTOCOL.md /
#                 README / LICENSE, or anything under _study/ or .obsidian/).
#
# Content scope defaults to the "Notes" folder plus the maps folder itself.
# Override with STUDY_MAP_CONTENT_ROOTS="Notes,Refs" (comma-separated, vault-relative).
#
# Usage:   integrity-lint.sh <vault-root> [maps-dir]   (maps-dir defaults to <vault>/Maps)
# Exit:    0 = clean, 1 = findings, 2 = usage error.

set -uo pipefail

VAULT="${1:-}"
MAPS="${2:-${VAULT:-}/Maps}"

if [ -z "$VAULT" ] || [ ! -d "$VAULT" ]; then
  echo "usage: integrity-lint.sh <vault-root> [maps-dir]" >&2
  exit 2
fi
if [ ! -d "$MAPS" ]; then
  echo "No maps dir at '$MAPS' — nothing to lint."
  exit 0
fi
command -v python3 >/dev/null 2>&1 || { echo "python3 required" >&2; exit 2; }

STUDY_MAP_CONTENT_ROOTS="${STUDY_MAP_CONTENT_ROOTS:-Notes}" \
python3 - "$VAULT" "$MAPS" <<'PY'
import sys, os, json, re, glob

vault, maps = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
maps_rel = os.path.relpath(maps, vault).replace('\\', '/')

# Content scope: configured note roots + the maps folder (maps may link to maps).
content_roots = [r.strip() for r in os.environ.get('STUDY_MAP_CONTENT_ROOTS', 'Notes').split(',') if r.strip()]
warranted_roots = set(content_roots) | {maps_rel}

def relpath(p):
    return os.path.relpath(os.path.abspath(p), vault).replace('\\', '/')

def warranted(rel):
    return any(rel == r or rel.startswith(r + '/') for r in warranted_roots)

def md_files(root):
    return glob.glob(os.path.join(root, '**', '*.md'), recursive=True)

# basename -> [vault-relative paths]
note_paths = {}
for f in md_files(vault):
    note_paths.setdefault(os.path.splitext(os.path.basename(f))[0], []).append(relpath(f))

# Tag vocabulary: built ONLY from in-scope content notes (not maps, not scaffolding),
# so a fabricated or scaffolding tag can never self-validate.
tags = set()
fm_item = re.compile(r'^\s*-\s*([A-Za-z0-9][\w/-]*)\s*$')
for f in md_files(vault):
    r = relpath(f)
    if not warranted(r) or r.startswith(maps_rel + '/') or r == maps_rel:
        continue
    text = open(f, encoding='utf-8', errors='ignore').read()
    fm = re.match(r'^---\n(.*?)\n---', text, re.S)
    if fm:
        tm = re.search(r'(?m)^tags:\s*$((?:\n\s*-\s*.+)+)', fm.group(1))
        if tm:
            for line in tm.group(1).splitlines():
                m = fm_item.match(line)
                if m:
                    tags.add(m.group(1).lower())
    nocode = re.sub(r'```.*?```', '', text, flags=re.S)
    for t in re.findall(r'(?<!\w)#([A-Za-z][\w/-]+)', nocode):
        tags.add(t.lower())

findings = 0
def flag(kind, msg):
    global findings
    findings += 1
    print(f"{kind}:", msg)

# --- Canvas files ---
for cf in glob.glob(os.path.join(maps, '**', '*.canvas'), recursive=True):
    name = os.path.basename(cf)
    try:
        data = json.load(open(cf, encoding='utf-8'))
    except Exception as e:
        flag("DANGLING", f"{name}: invalid JSON ({e})")
        continue
    nodes = data.get('nodes', []) or []
    ids = {n.get('id') for n in nodes}
    for n in nodes:
        if n.get('type') == 'file':
            p = (n.get('file', '') or '').replace('\\', '/')
            if not p or not os.path.exists(os.path.join(vault, p)):
                flag("DANGLING", f"{name}: file node -> missing '{p}'")
            elif not warranted(p):
                flag("UNWARRANTED", f"{name}: file node -> scaffolding/out-of-scope '{p}'")
    for e in (data.get('edges', []) or []):
        for end in ('fromNode', 'toNode'):
            if e.get(end) not in ids:
                flag("DANGLING", f"{name}: edge {end} -> unknown node '{e.get(end)}'")

# --- MOC / outline markdown ---
wikilink = re.compile(r'\[\[([^\]|#]+)')
for mf in md_files(maps):
    name = os.path.basename(mf)
    text = open(mf, encoding='utf-8', errors='ignore').read()
    for link in wikilink.findall(text):
        base = link.strip()
        if not base:
            continue
        paths = note_paths.get(base)
        if not paths:
            flag("DANGLING", f"{name}: [[{base}]] -> no such note")
        elif not any(warranted(p) for p in paths):
            flag("UNWARRANTED", f"{name}: [[{base}]] -> scaffolding/out-of-scope ({paths[0]})")
    nocode = re.sub(r'```.*?```', '', text, flags=re.S)
    for t in re.findall(r'(?<!\w)#([A-Za-z][\w/-]+)', nocode):
        if t.lower() not in tags:
            flag("DANGLING", f"{name}: #{t} -> tag not used by any content note")

if findings == 0:
    print("OK - every map node, edge, link, and tag resolves to real, in-scope content.")
sys.exit(1 if findings else 0)
PY
