#!/usr/bin/env python3
"""Sync a manifested canonical skill without overwriting unreviewed copy edits."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synchronize(source: Path, destination: Path, write: bool = False) -> list[str]:
    source = source.resolve()
    if destination.is_symlink():
        raise ValueError('Destination must be a real directory, not a symlink')
    destination = destination.resolve()
    if source == destination:
        raise ValueError('Source and destination must differ')
    manifest = json.loads((source / 'MANIFEST.json').read_text())
    old_path = destination / 'MANIFEST.json'
    if old_path.is_symlink():
        raise ValueError('Destination manifest must not be a symlink')
    old = json.loads(old_path.read_text()) if old_path.exists() else {'files': {}}
    changes = []
    for relative, expected in manifest['files'].items():
        rel = Path(relative)
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError(f'Invalid manifest path: {relative}')
        original, target = source / rel, destination / rel
        if original.resolve() != original or target.resolve() != target:
            raise ValueError(f'Symlink in managed path: {relative}')
        if digest(original) != expected:
            raise ValueError(f'Canonical manifest stale: {relative}; regenerate after review')
        if target.exists():
            current = digest(target)
            if current == expected:
                continue
            if current != old.get('files', {}).get(relative):
                raise ValueError(f'Unreviewed deployed edit: {relative}; compare and back up before adoption')
        changes.append(relative)
    if write:
        destination.mkdir(parents=True, exist_ok=True)
        for relative in changes:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            pending = target.with_name(target.name + '.sync-pending')
            # Exclusive creation avoids following an existing symlink/temp file.
            with pending.open('xb') as stream:
                stream.write((source / relative).read_bytes())
            pending.replace(target)
        for relative, expected in manifest['files'].items():
            if digest(destination / relative) != expected:
                raise ValueError(f'Post-sync mismatch: {relative}')
        pending = destination / 'MANIFEST.json.sync-pending'
        with pending.open('x') as stream:
            stream.write(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
        pending.replace(old_path)
    return changes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True, type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1]
    try:
        changes = synchronize(source, args.destination, args.write)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'Sync stopped: {error}\n')
    print(('Synchronized' if args.write else 'Would update') + f' {len(changes)} files; unrelated files preserved.')


if __name__ == '__main__':
    main()
