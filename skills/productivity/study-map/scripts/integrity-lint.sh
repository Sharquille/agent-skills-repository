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
from collections import Counter

vault, maps = os.path.realpath(sys.argv[1]), os.path.realpath(sys.argv[2])
try:
    if os.path.commonpath([vault, maps]) != vault:
        print(f"usage error: maps directory is outside the vault: {maps}", file=sys.stderr)
        sys.exit(2)
except ValueError:
    print(f"usage error: maps directory is outside the vault: {maps}", file=sys.stderr)
    sys.exit(2)
maps_rel = os.path.relpath(maps, vault).replace('\\', '/')

# Content scope: configured note roots + the maps folder (maps may link to maps).
content_roots = []
for raw_root in os.environ.get('STUDY_MAP_CONTENT_ROOTS', 'Notes').split(','):
    raw_root = raw_root.strip().replace('\\', '/')
    if not raw_root:
        continue
    normalized_root = os.path.normpath(raw_root).replace('\\', '/')
    if os.path.isabs(raw_root) or normalized_root == '..' or normalized_root.startswith('../'):
        print(f"usage error: content root is outside the vault: {raw_root}", file=sys.stderr)
        sys.exit(2)
    content_roots.append(normalized_root)
warranted_roots = set(content_roots) | {maps_rel}

def relpath(p):
    return os.path.relpath(os.path.abspath(p), vault).replace('\\', '/')

def warranted(rel):
    return any(rel == r or rel.startswith(r + '/') for r in warranted_roots)

def md_files(root):
    return glob.glob(os.path.join(root, '**', '*.md'), recursive=True)

def safe_target(raw):
    if not isinstance(raw, str) or not raw.strip():
        return None
    normalized = raw.strip().replace('\\', '/')
    if normalized.startswith('/') or '..' in normalized.split('/'):
        return None
    resolved = os.path.realpath(os.path.join(vault, normalized))
    try:
        if os.path.commonpath([vault, resolved]) != vault:
            return None
    except ValueError:
        return None
    if not os.path.isfile(resolved):
        return None
    return relpath(resolved)

# basename -> [vault-relative paths]
note_paths = {}
for f in md_files(vault):
    resolved = safe_target(relpath(f))
    if resolved is not None:
        note_paths.setdefault(os.path.splitext(os.path.basename(f))[0], []).append(resolved)

heading_cache = {}
def headings(rel):
    if rel not in heading_cache:
        text = open(os.path.join(vault, rel), encoding='utf-8', errors='ignore').read()
        heading_cache[rel] = {
            re.sub(r'\s+#+\s*$', '', title).strip().casefold()
            for title in re.findall(r'(?m)^#{1,6}[ \t]+(.+?)[ \t]*$', text)
        }
    return heading_cache[rel]

def valid_subpath(rel, subpath, owner):
    if subpath in (None, ''):
        return True
    if not isinstance(subpath, str) or not subpath.startswith('#') or len(subpath) == 1:
        flag('DANGLING', f"{owner}: invalid subpath '{subpath}'")
        return False
    anchor = subpath[1:].strip()
    if anchor.startswith('^'):
        block_id = re.escape(anchor[1:])
        text = open(os.path.join(vault, rel), encoding='utf-8', errors='ignore').read()
        if not re.search(rf'(?m)(?:^|[ \t])\^{block_id}[ \t]*$', text):
            flag('DANGLING', f"{owner}: subpath '{subpath}' -> missing block")
            return False
    elif anchor.casefold() not in headings(rel):
        flag('DANGLING', f"{owner}: subpath '{subpath}' -> missing heading")
        return False
    return True

def resolve_wikilink(raw, owner):
    note, separator, anchor = raw.strip().partition('#')
    if not note:
        flag('DANGLING', f"{owner}: [[{raw}]] -> empty note target")
        return None
    normalized = note.replace('\\', '/')
    if '/' in normalized:
        if not normalized.lower().endswith('.md'):
            normalized += '.md'
        rel = safe_target(normalized)
        paths = [rel] if rel is not None else []
    else:
        basename = os.path.splitext(normalized)[0]
        paths = sorted(set(note_paths.get(basename, [])))
        scoped = [path for path in paths if warranted(path)]
        if scoped:
            paths = scoped
    if not paths:
        flag('DANGLING', f"{owner}: [[{raw}]] -> no such note")
        return None
    if len(paths) > 1:
        flag('DANGLING', f"{owner}: [[{raw}]] -> ambiguous note ({', '.join(paths)})")
        return None
    rel = paths[0]
    if not warranted(rel):
        flag('UNWARRANTED', f"{owner}: [[{raw}]] -> scaffolding/out-of-scope '{rel}'")
        return None
    if separator:
        valid_subpath(rel, '#' + anchor, owner)
    return rel

# Tag vocabulary: built ONLY from in-scope content notes (not maps, not scaffolding),
# so a fabricated or scaffolding tag can never self-validate.
tags = set()
fm_item = re.compile(r'^\s*-\s*([A-Za-z0-9][\w/-]*)\s*$')
for f in md_files(vault):
    r = relpath(f)
    resolved = safe_target(r)
    if resolved is None or not warranted(resolved) or resolved.startswith(maps_rel + '/') or resolved == maps_rel:
        continue
    text = open(os.path.join(vault, resolved), encoding='utf-8', errors='ignore').read()
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
    resolved_canvas = safe_target(relpath(cf))
    if resolved_canvas is None or not warranted(resolved_canvas):
        flag("UNWARRANTED", f"{name}: canvas resolves outside Maps/")
        continue
    try:
        data = json.load(open(os.path.join(vault, resolved_canvas), encoding='utf-8'))
    except Exception as e:
        flag("DANGLING", f"{name}: invalid JSON ({e})")
        continue
    if not isinstance(data, dict):
        flag("DANGLING", f"{name}: JSON root must be an object")
        continue
    nodes = data.get('nodes', []) or []
    edges = data.get('edges', []) or []
    if not isinstance(nodes, list) or not all(isinstance(node, dict) for node in nodes):
        flag("DANGLING", f"{name}: nodes must be an array of objects")
        continue
    if not isinstance(edges, list) or not all(isinstance(edge, dict) for edge in edges):
        flag("DANGLING", f"{name}: edges must be an array of objects")
        continue
    node_id_counts = Counter(n.get('id') for n in nodes)
    for node_id, count in node_id_counts.items():
        if not node_id or count > 1:
            flag("DANGLING", f"{name}: node id must be non-empty and unique ('{node_id}')")
    ids = set(node_id_counts)
    edge_id_counts = Counter(e.get('id') for e in edges)
    for edge_id, count in edge_id_counts.items():
        if not edge_id or count > 1:
            flag("DANGLING", f"{name}: edge id must be non-empty and unique ('{edge_id}')")
    for n in nodes:
        if n.get('type') == 'file':
            p = (n.get('file', '') or '').replace('\\', '/')
            resolved = safe_target(p)
            if resolved is None:
                flag("DANGLING", f"{name}: file node -> missing '{p}'")
            elif not warranted(resolved):
                flag("UNWARRANTED", f"{name}: file node -> scaffolding/out-of-scope '{resolved}'")
            else:
                valid_subpath(resolved, n.get('subpath'), f"{name}: file node '{p}'")
    for e in edges:
        for end in ('fromNode', 'toNode'):
            if e.get(end) not in ids:
                flag("DANGLING", f"{name}: edge {end} -> unknown node '{e.get(end)}'")

# --- MOC / outline markdown ---
wikilink = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]')
for mf in md_files(maps):
    name = os.path.basename(mf)
    resolved_map = safe_target(relpath(mf))
    if resolved_map is None or not warranted(resolved_map):
        flag("UNWARRANTED", f"{name}: map note resolves outside Maps/")
        continue
    text = open(os.path.join(vault, resolved_map), encoding='utf-8', errors='ignore').read()
    for link in wikilink.findall(text):
        resolve_wikilink(link, name)
    nocode = re.sub(r'```.*?```', '', text, flags=re.S)
    for t in re.findall(r'(?<!\w)#([A-Za-z][\w/-]+)', nocode):
        if t.lower() not in tags:
            flag("DANGLING", f"{name}: #{t} -> tag not used by any content note")

if findings == 0:
    print("OK - every map node, edge, link, and tag resolves to real, in-scope content.")
sys.exit(1 if findings else 0)
PY
