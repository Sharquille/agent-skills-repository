# Maintaining this skill

Read this only when editing the skill itself, not when building a kit.

Canonical `SKILL_DIR` (git-tracked in the agent-skills repository):
`/Users/sharquilleandrew/Documents/development/github-local/agent-skills-repository/skills/productivity/chapter-study-kit`

| Location | Kind | How it updates |
| --- | --- | --- |
| `~/.claude/skills/chapter-study-kit` | symlink to canonical | automatically |
| `~/.agents/skills/chapter-study-kit` | real-folder copy | `sync_skill.py` |
| `Education/.cursor/skills/chapter-study-kit` | real-folder copy for Cursor | `sync_skill.py` |

Edit only the canonical folder. Do not treat the copies as a second source of
truth. If versions differ, use the canonical instructions and report drift.

## Release steps

1. Bump `Workflow version` in SKILL.md.
2. Run the tests: `python3 -m unittest discover -s "$SKILL_DIR/tests"`.
3. Regenerate `MANIFEST.json` from the reviewed SKILL.md, references, scripts,
   and tests (caches excluded):

   ```sh
   python3 - "$SKILL_DIR" <<'EOF'
   import hashlib, json, re, sys
   from pathlib import Path
   root = Path(sys.argv[1])
   version = re.search(r"Workflow version: \*\*([\d.]+)\*\*", (root / "SKILL.md").read_text()).group(1)
   files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*"))
            if p.is_file() and p.name not in {"MANIFEST.json", ".DS_Store"} and "__pycache__" not in p.parts}
   (root / "MANIFEST.json").write_text(json.dumps({"files": files, "version": version}, indent=2, sort_keys=True) + "\n")
   EOF
   ```

4. For each real-folder copy, run canonical
   `scripts/sync_skill.py --destination <copy>` as a dry run, then add
   `--write`. It stops on unreviewed deployed edits, refuses symlinks, and
   verifies SHA-256 hashes afterwards. Unrelated files are preserved.

For initial adoption without a manifest, compare and back up each copy first;
record its reviewed baseline hashes before syncing. Never auto-adopt a mismatch.

## Bumping Mermaid

`build_section_pdf.py` pins an exact Mermaid version (`MERMAID_JS`) and its
Subresource Integrity hash (`MERMAID_SRI`). Chrome refuses the script if the
bytes differ, so the build fails safe and the previous PDFs stay in place.
Change both together:

```sh
V=11.17.2   # the new exact version
TMP=$(mktemp -d)
curl -fsS -o "$TMP/mermaid.min.js" "https://cdn.jsdelivr.net/npm/mermaid@$V/dist/mermaid.min.js"
echo "sha384-$(openssl dgst -sha384 -binary "$TMP/mermaid.min.js" | openssl base64 -A)"
openssl dgst -sha256 -binary "$TMP/mermaid.min.js" | openssl base64 -A; echo
curl -fsS "https://data.jsdelivr.com/v1/packages/npm/mermaid@$V?structure=flat" \
  | python3 -c "import json,sys; print(next(f['hash'] for f in json.load(sys.stdin)['files'] if f['name'] == '/dist/mermaid.min.js'))"
```

The last two lines must print the same SHA-256. Then run the tests, rebuild one
section and inspect its maps, and only then rebuild every course without
`--section`. A new Mermaid release can change layout, so tell the user which
notebooks to replace in GoodNotes.
