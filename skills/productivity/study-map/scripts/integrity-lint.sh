#!/usr/bin/env bash
# integrity-lint.sh — verify a study-map's nodes, edges, wikilinks, and tags all
# resolve to real content in the vault. The study-map "integrity over volume"
# gate: zero dangling references before any map is considered done.
#
# Usage:   integrity-lint.sh <vault-root> [maps-dir]   (maps-dir defaults to <vault>/Maps)
# Exit:    0 = clean, 1 = dangling references found, 2 = usage error.

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

python3 - "$VAULT" "$MAPS" <<'PY'
import sys, os, json, re, glob

vault, maps = sys.argv[1], sys.argv[2]

def md_files(root):
    return glob.glob(os.path.join(root, '**', '*.md'), recursive=True)

# --- Allow-lists built from the real vault ---
# Note basenames include Maps/ so MOC-to-MOC links resolve; the tag vocabulary is
# built ONLY from real notes (outside Maps/) so a fabricated tag in a generated
# map cannot self-validate.
maps_abs = os.path.abspath(maps) + os.sep
def in_maps(f):
    return os.path.abspath(f).startswith(maps_abs)

note_basenames = {os.path.splitext(os.path.basename(f))[0] for f in md_files(vault)}

tags = set()
fm_item = re.compile(r'^\s*-\s*([A-Za-z0-9][\w/-]*)\s*$')
for f in md_files(vault):
    if in_maps(f):
        continue
    try:
        text = open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
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
def fail(msg):
    global findings
    findings += 1
    print("DANGLING:", msg)

# --- Canvas files: file nodes resolve, edges join real nodes ---
for cf in glob.glob(os.path.join(maps, '**', '*.canvas'), recursive=True):
    try:
        data = json.load(open(cf, encoding='utf-8'))
    except Exception as e:
        fail(f"{os.path.basename(cf)}: invalid JSON ({e})")
        continue
    nodes = data.get('nodes', []) or []
    ids = {n.get('id') for n in nodes}
    for n in nodes:
        if n.get('type') == 'file':
            p = n.get('file', '')
            if not p or not os.path.exists(os.path.join(vault, p)):
                fail(f"{os.path.basename(cf)}: file node -> missing '{p}'")
    for e in (data.get('edges', []) or []):
        for end in ('fromNode', 'toNode'):
            if e.get(end) not in ids:
                fail(f"{os.path.basename(cf)}: edge {end} -> unknown node '{e.get(end)}'")

# --- MOC / outline markdown: wikilinks resolve, inline tags exist ---
wikilink = re.compile(r'\[\[([^\]|#]+)')
for mf in md_files(maps):
    text = open(mf, encoding='utf-8', errors='ignore').read()
    for link in wikilink.findall(text):
        base = link.strip()
        if base and base not in note_basenames:
            fail(f"{os.path.basename(mf)}: [[{base}]] -> no such note")
    nocode = re.sub(r'```.*?```', '', text, flags=re.S)
    for t in re.findall(r'(?<!\w)#([A-Za-z][\w/-]+)', nocode):
        if t.lower() not in tags:
            fail(f"{os.path.basename(mf)}: #{t} -> tag not used by any note")

if findings == 0:
    print("OK - every map node, edge, link, and tag resolves to real vault content.")
sys.exit(1 if findings else 0)
PY
