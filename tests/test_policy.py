"""Project gates run against disposable sources; no desktop or network required."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'skills/omarchy-theme-scaffold/scripts/check_policy.py'
spec = importlib.util.spec_from_file_location('policy', SCRIPT)
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class Policy(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'colors.toml').write_text('foreground = "#ffffff"\nbackground = "#000000"\n')

    def run_gate(self, *flags):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.root), *flags], text=True, capture_output=True)

    def test_explicit_selection_and_unknown_flags_fail(self):
        for flags in [(), ('--unknown',), ('--contrast', 'foreground/background=nan'), ('--contrast', 'foreground/background=22')]:
            self.assertNotEqual(self.run_gate(*flags).returncode, 0)

    def test_contrast_pass_fail_missing_and_unresolved(self):
        self.assertEqual(self.run_gate('--contrast', 'foreground/background=21').returncode, 0)
        (self.root/'colors.toml').write_text('foreground = "#000000"\nbackground = "#000000"\n')
        self.assertNotEqual(self.run_gate('--contrast', 'foreground/background=4.5').returncode, 0)
        self.assertNotEqual(self.run_gate('--contrast', 'accent/background=3').returncode, 0)
        (self.root/'colors.toml').write_text('foreground = "gradient"\nbackground = "#000000"\n')
        self.assertNotEqual(self.run_gate('--contrast', 'foreground/background=4.5').returncode, 0)

    def test_repeated_rules_all_enforced_and_no_palette_mutation(self):
        original = (self.root/'colors.toml').read_bytes()
        result = self.run_gate('--contrast', 'foreground/background=4.5', '--contrast', 'missing/background=3')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.root/'colors.toml').read_bytes(), original)

    def test_staging_rule_is_opt_in_and_root_scoped(self):
        (self.root/'kitty.conf').write_text('shell unwanted')
        self.assertEqual(self.run_gate('--contrast', 'foreground/background=4.5').returncode, 0)
        self.assertNotEqual(self.run_gate('--deny-ignored-files').returncode, 0)
        (self.root/'kitty.conf').unlink()
        nested = self.root/'examples'; nested.mkdir()
        (nested/'example.lua').write_text('example')
        self.assertEqual(self.run_gate('--deny-ignored-files').returncode, 0)
        (self.root/'hyprland.lua').write_text('example')
        self.assertNotEqual(self.run_gate('--deny-ignored-files').returncode, 0)

    def test_invalid_palette_fails(self):
        (self.root/'colors.toml').write_text('not TOML')
        self.assertNotEqual(self.run_gate('--contrast', 'foreground/background=4.5').returncode, 0)

    def test_links_fail_without_decoding_target(self):
        link = self.root/'preview.png'
        try:
            link.symlink_to(self.root/'missing')
        except OSError:
            self.skipTest('symlink creation unavailable')
        self.assertNotEqual(self.run_gate('--check-images').returncode, 0)

    def test_unreadable_inventory_fails(self):
        with patch.object(Path, 'iterdir', side_effect=PermissionError('unreadable')):
            with self.assertRaises(PermissionError):
                policy.check(self.root, [], True)

    def test_images_decode_and_corruption_mismatch_and_empty_fail(self):
        from PIL import Image
        self.assertNotEqual(self.run_gate('--check-images').returncode, 0)
        path = self.root/'preview.png'
        Image.new('RGB', (16, 16), 'red').save(path)
        self.assertEqual(self.run_gate('--check-images').returncode, 0)
        path.write_bytes(path.read_bytes()[:40])
        self.assertNotEqual(self.run_gate('--check-images').returncode, 0)
        Image.new('RGB', (16, 16)).save(path, format='JPEG')
        self.assertNotEqual(self.run_gate('--check-images').returncode, 0)

    def test_decoder_missing_fails_instead_of_skipping(self):
        (self.root/'preview.png').write_bytes(b'not-an-image')
        with patch.dict(sys.modules, {'PIL': None}):
            errors, _ = policy.check(self.root, [], check_images=True)
        self.assertTrue(errors)
        self.assertIn('ModuleNotFoundError', errors[0])

    def test_image_resource_limits(self):
        from PIL import Image
        path = self.root/'preview.png'
        Image.new('RGB', (16, 16)).save(path)
        with patch.object(policy, 'MAX_PIXELS', 100):
            self.assertTrue(policy.check(self.root, [], check_images=True)[0])
        with patch.object(policy, 'MAX_BYTES', 1):
            self.assertTrue(policy.check(self.root, [], check_images=True)[0])

    def test_all_animation_frames_decode(self):
        from PIL import Image
        path = self.root/'animated.gif'
        frames = [Image.new('RGB', (16, 16), color) for color in ('red', 'blue')]
        frames[0].save(path, save_all=True, append_images=frames[1:])
        self.assertEqual(self.run_gate('--check-images').returncode, 0)
        with patch.object(policy, 'MAX_FRAMES', 1):
            self.assertTrue(policy.check(self.root, [], check_images=True)[0])


if __name__ == '__main__':
    unittest.main()
