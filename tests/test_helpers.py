import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def temporary_workspace():
    scratch = ROOT / '.verification'
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch)


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FingerprintTests(unittest.TestCase):
    def setUp(self):
        self.temp = temporary_workspace()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'routes.py').write_text('route v1', encoding='utf-8')
        (self.root / 'auth.py').write_text('auth v1', encoding='utf-8')
        self.script = load_script('fingerprint')

    def test_order_does_not_change_fingerprint(self):
        first = self.script.snapshot(self.root, ['routes.py', 'auth.py'])
        second = self.script.snapshot(self.root, ['auth.py', 'routes.py', 'auth.py'])
        self.assertEqual(first['digest'], second['digest'])

    def test_shared_dependency_invalidates_unchanged_route(self):
        before = self.script.snapshot(self.root, ['routes.py', 'auth.py'])
        (self.root / 'auth.py').write_text('auth v2', encoding='utf-8')
        after = self.script.snapshot(self.root, ['routes.py', 'auth.py'])
        self.assertNotEqual(before['digest'], after['digest'])

    def test_uncommitted_content_is_used(self):
        before = self.script.snapshot(self.root, ['routes.py'])
        (self.root / 'routes.py').write_text('local edit', encoding='utf-8')
        self.assertNotEqual(before['digest'], self.script.snapshot(self.root, ['routes.py'])['digest'])

    def test_dependency_set_change_invalidates(self):
        self.assertNotEqual(self.script.snapshot(self.root, ['routes.py'])['digest'],
                            self.script.snapshot(self.root, ['routes.py', 'auth.py'])['digest'])

    def test_missing_file_fails_closed(self):
        with self.assertRaises(ValueError):
            self.script.snapshot(self.root, ['missing.py'])

    def test_outside_path_rejected(self):
        project = self.root / 'project'
        project.mkdir()
        (self.root / 'outside.py').write_text('existing outside dependency', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.script.snapshot(project, ['../outside.py'])

    def test_absolute_path_rejected(self):
        with self.assertRaises(ValueError):
            self.script.snapshot(self.root, [str(self.root / 'auth.py')])

    def test_secret_file_rejected(self):
        (self.root / '.env').write_text('synthetic-value', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.script.snapshot(self.root, ['.env'])

    def test_symlink_rejected_if_supported(self):
        try:
            (self.root / 'link.py').symlink_to(self.root / 'auth.py')
        except OSError:
            self.skipTest('Symlinks unavailable on this host')
        with self.assertRaises(ValueError):
            self.script.snapshot(self.root, ['link.py'])

    def test_cli_supports_unicode_paths_with_legacy_stdout(self):
        name = 'модель.py'
        (self.root / name).write_text('model v1', encoding='utf-8')
        task_env = os.environ.copy()
        task_env['PYTHONIOENCODING'] = 'ascii'
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'fingerprint.py'),
             '--root', str(self.root), '--files', name],
            capture_output=True, text=True, encoding='ascii', env=task_env,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['files'][0]['path'], name)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = temporary_workspace()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / 'source'
        self.source.mkdir()
        (self.source / 'SKILL.md').write_text('skill v1', encoding='utf-8')
        (self.source / 'references').mkdir()
        (self.source / 'references' / 'workflow.md').write_text('workflow v1', encoding='utf-8')
        self.skills = self.base / 'skills'
        self.script = load_script('install')

    def test_installs_only_skill_package(self):
        (self.source / 'README.md').write_text('repo documentation', encoding='utf-8')
        target = self.script.install(self.source, self.skills, 'codex')
        self.assertEqual(target.name, 'sa')
        self.assertTrue((target / 'SKILL.md').is_file())
        self.assertFalse((target / 'README.md').exists())

    def test_existing_directory_requires_update(self):
        self.script.install(self.source, self.skills, 'codex')
        with self.assertRaises(ValueError):
            self.script.install(self.source, self.skills, 'codex')

    def test_managed_update(self):
        target = self.script.install(self.source, self.skills, 'codex')
        (self.source / 'SKILL.md').write_text('skill v2', encoding='utf-8')
        self.script.install(self.source, self.skills, 'codex', update=True)
        self.assertEqual((target / 'SKILL.md').read_text(encoding='utf-8'), 'skill v2')

    def test_manual_edit_blocks_update_without_partial_writes(self):
        target = self.script.install(self.source, self.skills, 'codex')
        (target / 'references' / 'workflow.md').write_text('manual change', encoding='utf-8')
        (self.source / 'SKILL.md').write_text('skill v2', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.script.install(self.source, self.skills, 'codex', update=True)
        self.assertEqual((target / 'SKILL.md').read_text(encoding='utf-8'), 'skill v1')

    def test_unknown_extra_file_blocks_update(self):
        target = self.script.install(self.source, self.skills, 'codex')
        (target / 'notes.md').write_text('manual notes', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.script.install(self.source, self.skills, 'codex', update=True)

    def test_unmanaged_target_is_preserved(self):
        target = self.skills / 'sa'
        target.mkdir(parents=True)
        (target / 'SKILL.md').write_text('user skill', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.script.install(self.source, self.skills, 'codex', update=True)
        self.assertEqual((target / 'SKILL.md').read_text(encoding='utf-8'), 'user skill')

    def test_install_inside_source_is_rejected(self):
        with self.assertRaises(ValueError):
            self.script.install(self.source, self.source / 'skills', 'codex')

    def test_topology_file_to_directory_rejected_before_writes(self):
        section = self.source / 'references' / 'section'
        section.write_text('section v1', encoding='utf-8')
        target = self.script.install(self.source, self.skills, 'codex')
        section.unlink()
        section.mkdir()
        (section / 'details.md').write_text('section v2', encoding='utf-8')
        (self.source / 'SKILL.md').write_text('skill v2', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.script.install(self.source, self.skills, 'codex', update=True)
        self.assertEqual((target / 'SKILL.md').read_text(encoding='utf-8'), 'skill v1')
        self.assertEqual((target / 'references' / 'section').read_text(encoding='utf-8'), 'section v1')

    def test_topology_directory_to_file_rejected_before_writes(self):
        section = self.source / 'references' / 'section'
        section.mkdir()
        (section / 'details.md').write_text('section v1', encoding='utf-8')
        target = self.script.install(self.source, self.skills, 'codex')
        (section / 'details.md').unlink()
        section.rmdir()
        section.write_text('section v2', encoding='utf-8')
        (self.source / 'SKILL.md').write_text('skill v2', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.script.install(self.source, self.skills, 'codex', update=True)
        self.assertEqual((target / 'SKILL.md').read_text(encoding='utf-8'), 'skill v1')
        self.assertTrue((target / 'references' / 'section' / 'details.md').is_file())

    def test_codex_metadata_installed_only_for_codex(self):
        (self.source / 'agents').mkdir()
        (self.source / 'agents' / 'openai.yaml').write_text('interface: {}', encoding='utf-8')
        claude = self.script.install(self.source, self.base / 'claude', 'claude')
        codex = self.script.install(self.source, self.base / 'codex', 'codex')
        self.assertFalse((claude / 'agents').exists())
        self.assertTrue((codex / 'agents' / 'openai.yaml').is_file())
        self.assertTrue((claude / 'references' / 'workflow.md').is_file())

    def test_other_platform_installation_is_preserved(self):
        target = self.script.install(self.source, self.skills, 'codex')
        (self.source / 'SKILL.md').write_text('skill v2', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.script.install(self.source, self.skills, 'claude', update=True)
        self.assertEqual((target / 'SKILL.md').read_text(encoding='utf-8'), 'skill v1')

    def test_legacy_uppercase_installation_migrates_on_update(self):
        target = self.script.install(self.source, self.skills, 'codex')
        legacy = self.skills / 'SA'
        target.rename(self.skills / 'moving')
        (self.skills / 'moving').rename(legacy)
        marker = legacy / self.script.MARKER
        manifest = json.loads(marker.read_text(encoding='utf-8'))
        del manifest['platform']
        marker.write_text(json.dumps(manifest), encoding='utf-8')
        (self.source / 'SKILL.md').write_text('skill v2', encoding='utf-8')
        self.script.install(self.source, self.skills, 'codex', update=True)
        self.assertEqual([path.name for path in self.skills.iterdir()], ['sa'])
        self.assertEqual((self.skills / 'sa' / 'SKILL.md').read_text(encoding='utf-8'), 'skill v2')

    def test_case_duplicates_rejected_if_file_system_is_case_sensitive(self):
        (self.skills / 'SA').mkdir(parents=True)
        try:
            (self.skills / 'sa').mkdir()
        except FileExistsError:
            self.skipTest('File system is case-insensitive')
        with self.assertRaises(ValueError):
            self.script.install(self.source, self.skills, 'claude', update=True)

    def test_unknown_platform_rejected(self):
        with self.assertRaises(ValueError):
            self.script.install(self.source, self.skills, 'other')
        self.assertFalse(self.skills.exists())


if __name__ == '__main__':
    unittest.main()
