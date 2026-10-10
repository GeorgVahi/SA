#!/usr/bin/env python3
"""Install SA globally without replacing an existing skill or manual edits."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys


MARKER = '.sa-install.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def package_files(source):
    files = [source / 'SKILL.md']
    for folder in ('agents', 'references', 'scripts'):
        directory = source / folder
        if directory.exists():
            files.extend(path for path in directory.rglob('*')
                         if path.is_file() and '__pycache__' not in path.parts
                         and path.suffix != '.pyc')
    result = {}
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(source):
            raise ValueError('Skill package must not contain linked files outside its root')
        result[path.relative_to(source).as_posix()] = path.read_bytes()
    return result


def install(source, skills_dir, update=False):
    source = Path(source).resolve()
    skills_dir = Path(skills_dir).resolve()
    target = skills_dir / 'SA'
    if target.is_symlink() or (hasattr(target, 'is_junction') and target.is_junction()):
        raise ValueError('Refusing to install over a linked skill directory')
    if target.is_relative_to(source) or source.is_relative_to(target):
        raise ValueError('Source and installed skill must not overlap')
    content = package_files(source)
    old_files = {}
    if target.exists():
        if not update:
            raise ValueError('SA already exists; use --update for an unmodified managed installation')
        marker = target / MARKER
        if not marker.is_file() or marker.is_symlink():
            raise ValueError('Existing SA is not a managed installation; preserve it manually')
        manifest = json.loads(marker.read_text(encoding='utf-8'))
        if manifest.get('package') != 'SA' or manifest.get('schema') != 1:
            raise ValueError('Unknown installation manifest')
        old_files = manifest.get('files')
        if not isinstance(old_files, dict):
            raise ValueError('Invalid installation manifest')
        for name, expected in old_files.items():
            relative = PurePosixPath(name)
            if (relative.is_absolute() or '..' in relative.parts
                    or '\\' in name or ':' in name or name == MARKER):
                raise ValueError('Unsafe path in installation manifest')
            path = target / name
            if (not path.resolve().is_relative_to(target) or not path.is_file()
                    or path.is_symlink() or sha(path.read_bytes()) != expected):
                raise ValueError('Installed files were edited or removed; no files changed')
        existing = set()
        for path in target.rglob('*'):
            if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                raise ValueError('Linked installed files are not safe to update')
            if path.is_file():
                name = path.relative_to(target).as_posix()
                if '__pycache__' in path.parts and path.suffix == '.pyc':
                    continue
                existing.add(name)
        if existing != set(old_files) | {MARKER}:
            raise ValueError('Installation contains untracked files; no files changed')
    # Reject predictable layout conflicts before replacing even the first file.
    # File/directory conversions need a deliberate migration, not a partial update.
    for name in content:
        destination = target / name
        if destination.exists() and not destination.is_file():
            raise ValueError('Package file conflicts with an installed directory; no files changed')
        for parent in destination.parents:
            if parent == target:
                break
            if parent.exists() and not parent.is_dir():
                raise ValueError('Package directory conflicts with an installed file; no files changed')
    target.mkdir(parents=True, exist_ok=True)
    for name, data in content.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    for name in set(old_files) - set(content):
        path = target / name
        if not path.resolve().is_relative_to(target):
            raise ValueError('Removed package file outside installation root')
        path.unlink()
    manifest = {'package': 'SA', 'schema': 1,
                'files': {name: sha(data) for name, data in sorted(content.items())}}
    (target / MARKER).write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skills-dir', type=Path, default=Path.home() / '.agents' / 'skills')
    parser.add_argument('--update', action='store_true')
    args = parser.parse_args()
    try:
        target = install(Path(__file__).resolve().parents[1], args.skills_dir, args.update)
    except (OSError, ValueError) as error:
        print(f'Install failed: {error}', file=sys.stderr)
        return 1
    print(f'Installed SA: {target}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
