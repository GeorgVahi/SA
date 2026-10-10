#!/usr/bin/env python3
"""Hash an explicitly reviewed dependency closure; never discover it implicitly."""

import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import sys


SECRET_NAMES = {'credentials', 'credentials.json', 'auth.json', 'secrets.json',
                'secrets.yaml', 'secrets.yml', 'id_rsa', 'id_ed25519', '.netrc'}
SECRET_SUFFIXES = {'.key', '.pem', '.p12', '.pfx', '.keystore'}


def safe_file(root, name):
    relative = Path(name)
    if (not isinstance(name, str) or not name or relative.is_absolute()
            or PureWindowsPath(name).is_absolute() or PureWindowsPath(name).drive
            or '..' in relative.parts or '..' in PureWindowsPath(name).parts):
        raise ValueError('Dependency must be a relative path within the project')
    path = root / relative
    for component in relative.parts:
        lowered = component.lower()
        if lowered.startswith('.env') or lowered in SECRET_NAMES or lowered in {'.git', '.ssh'}:
            raise ValueError('Secret or repository metadata paths cannot be fingerprinted')
    if path.suffix.lower() in SECRET_SUFFIXES:
        raise ValueError('Secret key/certificate paths cannot be fingerprinted')
    current = root
    for component in relative.parts:
        current = current / component
        if current.is_symlink() or (hasattr(current, 'is_junction') and current.is_junction()):
            raise ValueError('Linked dependency paths cannot be fingerprinted')
    resolved = path.resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError('Dependency missing or outside project root')
    return resolved


def snapshot(root, names):
    root = Path(root).resolve()
    if not root.is_dir() or not names:
        raise ValueError('An existing project and a nonempty dependency list are required')
    entries = {}
    for name in names:
        if not isinstance(name, str):
            raise ValueError('Dependency names must be strings')
        path = safe_file(root, name)
        before = path.stat()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError('Dependency changed during snapshot; retry on stable code')
        entries[path.relative_to(root).as_posix()] = digest
    files = [{'path': path, 'sha256': entries[path]} for path in sorted(entries)]
    encoded = json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return {'schema': 1, 'algorithm': 'sha256',
            'digest': hashlib.sha256(encoded).hexdigest(), 'files': files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--files', nargs='+')
    group.add_argument('--files-from', type=Path, help='JSON array of project-relative paths')
    args = parser.parse_args()
    try:
        names = args.files
        if args.files_from:
            names = json.loads(args.files_from.read_text(encoding='utf-8-sig'))
            if not isinstance(names, list):
                raise ValueError('Dependency manifest must be a JSON array')
        result = snapshot(args.root, names)
    except (OSError, ValueError) as error:
        print(f'Snapshot failed: {error}', file=sys.stderr)
        return 1
    # Escaped JSON remains valid UTF-8 and also survives legacy Windows stdout.
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
