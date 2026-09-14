import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'skills/omarchy-theme-scaffold/scripts/theme-tool/Cargo.toml'
def run(*args):
 return subprocess.run(args,cwd=ROOT,text=True,capture_output=True)
def tool(*args):
 return run('cargo','run','--quiet','--manifest-path',str(MANIFEST),'--',*map(str,args))
class ThemeWorkflow(unittest.TestCase):
 def test_scaffold_and_check(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp)/'omarchy-sample-theme'
   self.assertEqual(tool('scaffold',dest).returncode,0)
   self.assertEqual(tool('check',dest).returncode,0)
   self.assertNotEqual(tool('check',dest,'--release').returncode,0)
   self.assertFalse((dest/'preview.png').exists())
 def test_existing_scaffold_preserved(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp)/'omarchy-sample-theme';dest.mkdir();(dest/'precious').write_text('keep')
   self.assertNotEqual(tool('scaffold',dest).returncode,0)
   self.assertEqual((dest/'precious').read_text(),'keep')
 @unittest.skipIf(os.name=='nt','symlink privileges differ on Windows')
 def test_symlink_rejected_without_reading(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp)/'omarchy-sample-theme';tool('scaffold',dest)
   (dest/'leak').symlink_to('/etc/passwd')
   self.assertNotEqual(tool('check',dest).returncode,0)
 def test_ignored_terminal_config_reported(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp)/'omarchy-sample-theme';tool('scaffold',dest)
   (dest/'kitty.conf').write_text('foreground red')
   result=tool('check',dest)
   self.assertEqual(result.returncode,0)
   self.assertIn('ignored by Git-installed theme staging: kitty.conf',result.stdout)
 def test_installer_lifecycle_and_modified_files(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp)/'installed'
   cmd=[sys.executable,'scripts/install_agent_skills.py','--target','generic','--destination',str(dest)]
   result=run(*cmd);self.assertEqual(result.returncode,0,result.stderr)
   self.assertEqual(len(list(dest.glob('*/SKILL.md'))),12)
   self.assertEqual(list(dest.rglob('target')),[])
   target=dest/'omarchy-theme-palette/SKILL.md'
   original=target.read_text();target.write_text(original+'\nLocal change\n')
   self.assertNotEqual(run(*cmd,'--update').returncode,0)
   self.assertNotEqual(run(*cmd,'--uninstall').returncode,0)
   target.write_text(original)
   self.assertEqual(run(*cmd,'--uninstall').returncode,0)
   self.assertFalse(target.exists())
if __name__=='__main__': unittest.main()
