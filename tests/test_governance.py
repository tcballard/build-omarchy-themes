"""Release and contract regressions; fixtures never contact a live service."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import check_bundle
import check_contracts

class Bundle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/'source'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('.git', 'target', '__pycache__', 'dist'))

    def command(self, *args):
        return subprocess.run(args, cwd=self.root, text=True, capture_output=True)

    def commit(self):
        for args in [('init', '-b', 'main'), ('config', 'user.name', 'Fixture'),
                     ('config', 'user.email', 'fixture@example.invalid'), ('add', '.'), ('commit', '-m', 'fixture')]:
            result = self.command('git', *args)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_version_mismatch_rejected_by_validation_and_packaging(self):
        (self.root/'VERSION').write_text('99.0.0\n')
        self.assertTrue(check_bundle.validate(self.root))
        self.commit()
        result = self.command(sys.executable, 'scripts/package.py', '--output-dir', str(Path(self.tmp.name)/'out'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('version differs', result.stderr)

    def test_each_provider_version_is_checked(self):
        for name in check_bundle.MANIFESTS:
            with self.subTest(name=name):
                path = self.root/name
                original = path.read_text()
                value = json.loads(original);value['version'] = '99.0.0'
                path.write_text(json.dumps(value))
                self.assertTrue(check_bundle.validate(self.root))
                path.write_text(original)

    def test_reference_drift_and_missing_release_notes(self):
        self.assertEqual(check_bundle.validate(self.root), [])
        path = self.root/'skills/omarchy-theme-palette/references/contract.md'
        path.write_text(path.read_text()+'\nChanged contract\n')
        self.assertIn('shared contract references differ', check_bundle.validate(self.root))
        (self.root/'docs/releases/v0.2.0.md').unlink()
        self.assertIn('release notes missing for VERSION', check_bundle.validate(self.root))

    def test_provider_paths_and_completion_drift(self):
        path = self.root/'plugins/build-omarchy-themes/.codex-plugin/plugin.json'
        value=json.loads(path.read_text());value['skills']='../wrong';path.write_text(json.dumps(value))
        path=self.root/'skills/omarchy-theme-palette/SKILL.md'
        path.write_text(path.read_text()+'\nDifferent rule\n')
        errors=check_bundle.validate(self.root)
        self.assertIn('shared task completion guidance differs', errors)
        self.assertIn('OpenAI adapter skills path must be ./skills/', errors)

    def test_packages_are_reproducible_and_have_correct_entry_points(self):
        self.commit()
        outputs=[]
        for name in ('first','second'):
            out=Path(self.tmp.name)/name;outputs.append(out)
            result=self.command(sys.executable,'scripts/package.py','--output-dir',str(out))
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(sorted(p.name for p in outputs[0].iterdir()), sorted(p.name for p in outputs[1].iterdir()))
        for file in outputs[0].iterdir():
            self.assertEqual(file.read_bytes(), (outputs[1]/file.name).read_bytes())
        archives=list(outputs[0].glob('*.zip'));self.assertEqual(len(archives),5)
        for path in archives:
            with zipfile.ZipFile(path) as archive:
                names=archive.namelist()
                self.assertFalse(any('/target/' in n or '.git/' in n for n in names))
                self.assertEqual(len(names),len(set(names)))
                if '-openai-plugin-' in path.name:
                    self.assertIn('.codex-plugin/plugin.json',names)
                    self.assertEqual(12,sum(n.endswith('/agents/openai.yaml') for n in names))
                elif '-claude-plugin-' in path.name:
                    self.assertIn('.claude-plugin/plugin.json',names)
                elif '-plugin-' in path.name:
                    self.assertIn('plugin.json',names)
                    self.assertFalse(any(n.endswith('/agents/openai.yaml') for n in names))
        (self.root/'uncommitted.txt').write_text('local input')
        result=self.command(sys.executable,'scripts/package.py','--output-dir',str(Path(self.tmp.name)/'dirty'))
        self.assertNotEqual(result.returncode,0)
        self.assertIn('working tree is not clean',result.stderr)

class Contracts(unittest.TestCase):
    def fixture(self):
        return {'checked':'2026-09-29','sources':[{'repository':'omacom/omarchy','ref':'quattro','path':'theme.txt','commit':'a'*40,'blob_sha':check_contracts.blob_sha(b'reviewed\n')}]}

    def test_manifest_rejects_unsafe_missing_duplicate_identities(self):
        original=self.fixture();self.assertEqual([],check_contracts.validate(original))
        for field,value in [('path','../escape'),('repository','unknown/repo'),('commit','main'),('blob_sha','bad'),('path','a//b')]:
            data=copy.deepcopy(original);data['sources'][0][field]=value
            self.assertTrue(check_contracts.validate(data),(field,value))
        data=copy.deepcopy(original);data['sources']*=2
        self.assertTrue(check_contracts.validate(data))
        self.assertTrue(check_contracts.validate({}))

    def test_live_unchanged_content_survives_branch_movement(self):
        def get(url):
            return json.dumps({'sha':'b'*40}).encode() if '/commits/' in url else b'reviewed\n'
        errors,notes=check_contracts.check_live(self.fixture()['sources'],get)
        self.assertEqual(errors,[]);self.assertIn('branch moved',notes[0])

    def test_live_changed_pinned_or_current_content_fails(self):
        for changed in ('a'*40,'b'*40):
            def get(url):
                if '/commits/' in url:return json.dumps({'sha':'b'*40}).encode()
                return b'changed\n' if '/'+changed+'/' in url else b'reviewed\n'
            errors,_=check_contracts.check_live(self.fixture()['sources'],get)
            self.assertTrue(errors)

    def test_unavailable_upstream_fails_closed(self):
        def get(url):raise OSError('offline')
        errors,_=check_contracts.check_live(self.fixture()['sources'],get)
        self.assertTrue(errors)

    def test_malformed_commit_response_fails_closed(self):
        for response in (b'bad json',b'{}',b'{"sha":"main"}'):
            errors,_=check_contracts.check_live(self.fixture()['sources'],lambda url:response)
            self.assertTrue(errors)

if __name__=='__main__':unittest.main()
