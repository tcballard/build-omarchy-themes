"""Black-box handoff regressions. Runtime rows below are synthetic test fixtures."""
from pathlib import Path
import tempfile
import unittest
from test_bundle import tool


class Handoff(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'omarchy-handoff-theme'
        self.ok(tool('scaffold', self.root))
        self.sequence = 0

    def ok(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def edit(self, path, old, new):
        file = self.root / path
        text = file.read_text()
        self.assertIn(old, text)
        file.write_text(text.replace(old, new))

    def snapshot(self, implementation=False):
        self.sequence += 1
        name = f'evidence/snapshot-{self.sequence}.manifest'
        self.ok(tool('snapshot', self.root, name, *(['--implementation'] if implementation else [])))
        return name

    def handoff(self, manifest=None):
        return tool('handoff', self.root, manifest or self.snapshot())

    def fail(self, result, *messages):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        for message in messages:
            self.assertIn(message, result.stderr)

    def row(self, state, manifest, kind='local', version='-'):
        # Deliberately fictional command/results; tests verify consistency only.
        row = f'{state}\t{kind}\t{manifest}\tfixture-repo@' + 'a' * 40
        row += f'\t{version}\tfixture-command (not executed)\tsynthetic test result\n'
        with (self.root / 'evidence/checks.tsv').open('a') as file:
            file.write(row)

    def test_fresh_scaffold_handoff_without_runtime_claim(self):
        result = self.ok(self.handoff())
        self.assertIn('NOT-RUN live:', result.stdout)
        self.assertIn('NOT-RUN registry:', result.stdout)
        self.assertIn('consistency only', result.stdout)
        self.assertFalse((self.root / 'preview.png').exists())
        self.assertIn('Tested installed Omarchy version: none', (self.root / 'README.md').read_text())

    def test_incomplete_handoff_reports_independent_problems(self):
        old = self.snapshot(True)
        self.row('now', old)
        self.edit('README.md', 'height="20"', 'height="21"')
        self.edit('README.md', 'version: none', 'version: 4.0.3')
        with (self.root / 'CREDITS.md').open('a') as file:
            file.write('\nRemoved wallpaper: `backgrounds/excluded.png`\n')
        with (self.root / 'colors.toml').open('a') as file:
            file.write('\n# Different delivered implementation\n')
        self.fail(self.handoff(), 'missing approved Theme SVG', 'stale asset/link',
                  'unsupported tested installed version', 'evidence from different files')

    def test_delivery_detects_added_deleted_and_changed_files(self):
        manifest = self.snapshot()
        self.edit('README.md', '# handoff', '# Updated handoff')
        self.fail(self.handoff(manifest), 'delivery manifest differs')
        manifest = self.snapshot()
        (self.root / 'new.conf').write_text('new runtime setting')
        self.fail(self.handoff(manifest), 'delivery manifest differs')
        manifest = self.snapshot()
        (self.root / 'new.conf').unlink()
        self.fail(self.handoff(manifest), 'delivery manifest differs')

    def test_documentation_only_keeps_historical_implementation_evidence(self):
        old = self.snapshot(True)
        self.row('historical', old)
        self.edit('README.md', '# handoff', '# Corrected title')
        result = self.ok(self.handoff())
        self.assertIn('unchanged; not rerun', result.stdout)
        self.assertIn('NOT-RUN live:', result.stdout)

    def test_historical_different_files_are_visible_not_current_evidence(self):
        old = self.snapshot(True)
        self.row('historical', old)
        (self.root / 'shell.toml').write_text('# new configuration')
        result = self.ok(self.handoff())
        self.assertIn('DIFFER; not evidence for this delivery', result.stdout)

    def test_matching_live_fixture_supports_only_exact_version(self):
        old = self.snapshot(True)
        self.row('historical', old, 'live', '4.0.3')
        self.edit('README.md', 'version: none', 'version: 4.0.3')
        self.ok(self.handoff())
        self.edit('README.md', 'version: 4.0.3', 'version: 4.0.3+')
        self.fail(self.handoff(), 'unsupported tested installed version')

    def test_changed_implementation_invalidates_historical_live_claim(self):
        old = self.snapshot(True)
        self.row('historical', old, 'live', '4.0.3')
        self.edit('README.md', 'version: none', 'version: 4.0.3')
        (self.root / 'shell.toml').write_text('# different files')
        self.fail(self.handoff(), 'unsupported tested installed version')

    def test_missing_failure_and_not_run_evidence_remain_visible(self):
        old = self.snapshot(True)
        self.row('failure', old)
        result = self.ok(self.handoff())
        self.assertIn('FAILURE local:', result.stdout)
        self.edit('evidence/checks.tsv', 'not-run\tlive\t-\tnone\t-\t-\tNo live Omarchy desktop available; installation and rollback unverified\n', '')
        self.fail(self.handoff(), 'missing live evidence')

    def test_missing_rollback_and_broad_claim_are_rejected(self):
        self.edit('README.md', '## Rollback', '## Other')
        with (self.root / 'README.md').open('a') as file:
            file.write('\nCompatible with Omarchy 4 and all future versions.\n')
        self.fail(self.handoff(), 'missing ## Rollback', 'unsupported compatibility claim')

    def test_inline_html_and_reference_links(self):
        with (self.root / 'README.md').open('a') as file:
            file.write('\n[manual](missing.md)\n<img src="missing.png">\n[asset]: missing.webp\n')
        self.fail(self.handoff(), 'missing.md', 'missing.png', 'missing.webp')

    def test_snapshot_is_immutable_and_rejects_unsafe_paths(self):
        name = self.snapshot()
        self.fail(tool('snapshot', self.root, name), 'snapshot is immutable')
        self.fail(tool('snapshot', self.root, '../escape.manifest'), 'safe relative')

    def test_symlink_evidence_rejected_before_reads(self):
        (self.root / 'evidence/checks.tsv').unlink()
        (self.root / 'evidence/checks.tsv').symlink_to('/etc/passwd')
        self.fail(tool('handoff', self.root, 'evidence/anything.manifest'), 'symlink')

    def test_tampered_manifest_cannot_omit_runtime_file(self):
        (self.root / 'shell.toml').write_text('# relevant')
        manifest = self.snapshot(True)
        path = self.root / manifest
        path.write_text(''.join(line for line in path.read_text().splitlines(True) if '\tshell.toml' not in line))
        self.row('now', manifest)
        self.fail(self.handoff(), 'evidence from different files')

    def test_evidence_directory_cannot_hide_runtime_files(self):
        (self.root / 'evidence/hidden.qml').write_text('Item {}')
        self.fail(self.handoff(), 'reserved for ledgers')

    def test_contact_sheet_is_distinct_from_desktop_capture(self):
        (self.root / 'docs').mkdir()
        (self.root / 'docs/contact.png').write_bytes(b'not a decoded image; consistency fixture')
        (self.root / 'media.tsv').write_text('docs/contact.png\tcontact-sheet\tWallpaper collection — not a desktop screenshot\n')
        with (self.root / 'README.md').open('a') as file:
            file.write('\n![Desktop screenshot](docs/contact.png)\n')
        self.fail(self.handoff(), 'README must include its media caption')
        self.edit('README.md', '![Desktop screenshot]', '![Wallpaper collection — not a desktop screenshot]')
        self.ok(self.handoff())
        self.edit('media.tsv', 'contact-sheet', 'desktop-screenshot')
        self.fail(self.handoff(), 'desktop screenshots require matching live evidence')

    def test_wallpaper_requires_classification_and_delivered_credit_path(self):
        (self.root / 'backgrounds/art.png').write_bytes(b'fixture')
        self.fail(self.handoff(), 'unclassified delivered media', 'missing delivered asset')
        (self.root / 'media.tsv').write_text('backgrounds/art.png\twallpaper\tOriginal art\n')
        with (self.root / 'CREDITS.md').open('a') as file:
            file.write('\nbackgrounds/art.png — test fixture, not redistributable media.\n')
        self.ok(self.handoff())
        (self.root / 'backgrounds/art.png').unlink()
        self.fail(self.handoff(), 'stale asset/link', 'stale/invalid/duplicate asset')

    def test_readme_and_evidence_from_another_theme_cannot_pass(self):
        other = Path(self.tmp.name) / 'omarchy-other-theme'
        self.ok(tool('scaffold', other))
        manifest = self.snapshot()
        (other / manifest).write_bytes((self.root / manifest).read_bytes())
        self.fail(tool('handoff', other, manifest), 'delivery manifest differs')

    def test_target_and_status_badges_are_required(self):
        self.edit('README.md', 'alt="Target:', 'alt="Other:')
        self.edit('README.md', 'alt="Status:', 'alt="Other:')
        self.fail(self.handoff(), 'missing Target: badge', 'missing Status: badge')

    def test_moving_upstream_revision_is_not_exact_evidence(self):
        old = self.snapshot(True)
        self.row('now', old)
        self.edit('evidence/checks.tsv', 'fixture-repo@' + 'a' * 40, 'fixture-repo@main')
        self.fail(self.handoff(), 'exact commit/blob SHA')

    def test_stale_credit_outside_standard_media_directory(self):
        with (self.root / 'CREDITS.md').open('a') as file:
            file.write('\n`art/removed.webp` by Example.\n')
        self.fail(self.handoff(), 'stale asset/link art/removed.webp')

    def test_extracted_archive_matches_delivery_snapshot(self):
        import tarfile
        manifest = self.snapshot()
        archive = Path(self.tmp.name) / 'theme.tar'
        with tarfile.open(archive, 'w') as tar:
            tar.add(self.root, arcname=self.root.name)
        destination = Path(self.tmp.name) / 'extracted'
        destination.mkdir()
        with tarfile.open(archive) as tar:
            tar.extractall(destination, filter='data')
        result = self.ok(tool('handoff', destination / self.root.name, manifest))
        self.assertIn('NOT-RUN live:', result.stdout)

if __name__ == '__main__':
    unittest.main()
