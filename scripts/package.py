#!/usr/bin/env python3
"""Package only a clean committed tree. No network or publication side effects."""
import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = 'build-omarchy-themes'
def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])
def archive(path, entries):
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_STORED) as z:
        for name, data, mode in sorted(entries):
            info = zipfile.ZipInfo(name, (2026, 9, 14, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (int(mode, 8) & 0o177777) << 16
            z.writestr(info, data)
def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, required=True)
    args = p.parse_args()
    if git('status', '--porcelain').strip():
        raise SystemExit('Commit the reviewed changes before packaging; working tree is not clean.')
    commit = git('rev-parse', 'HEAD').decode().strip()
    entries = []
    for row in git('ls-tree', '-rz', 'HEAD').split(b'\0'):
        if not row: continue
        meta, rawpath = row.split(b'\t', 1)
        mode, typ, sha = meta.decode().split()
        name = rawpath.decode()
        if typ != 'blob' or mode not in ('100644', '100755'):
            raise SystemExit(f'Unsupported tracked object: {name}')
        if any(part in ('target', '__pycache__', 'dist', '.git') for part in Path(name).parts):
            raise SystemExit(f'Generated/private path tracked: {name}')
        entries.append((name, git('cat-file', 'blob', sha), mode))
    manifest = json.loads(next(data for name, data, _ in entries if name == 'plugin.json'))
    version = manifest['version']
    if not re.fullmatch(r'\d+\.\d+\.\d+', version): raise SystemExit('Invalid version')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    prefix = 'plugins/'+NAME+'/'
    groups = {
        'source': entries,
        'plugin': [e for e in entries if e[0] in ('plugin.json', 'LICENSE') or e[0].startswith('skills/')],
        'skills': [((n[7:] if n.startswith('skills/') else n), d, m) for n,d,m in entries if n.startswith('skills/') or n=='LICENSE'],
        'openai-plugin': [(n[len(prefix):],d,m) for n,d,m in entries if n.startswith(prefix)] + [e for e in entries if e[0]=='LICENSE'],
        'claude-plugin': [e for e in entries if e[0].startswith(('skills/', '.claude-plugin/')) or e[0]=='LICENSE'],
    }
    checks = []
    for kind, group in groups.items():
        path = args.output_dir/f'{NAME}-{kind}-{version}.zip'
        archive(path,group)
        checks.append((path.name,hashlib.sha256(path.read_bytes()).hexdigest()))
    inventory = {'version':version,'commit':commit,'files':[{'path':n,'sha256':hashlib.sha256(d).hexdigest(),'mode':m} for n,d,m in entries]}
    path = args.output_dir/'source-manifest.json'
    path.write_text(json.dumps(inventory,indent=2)+'\n')
    checks.append((path.name,hashlib.sha256(path.read_bytes()).hexdigest()))
    (args.output_dir/'SHA256SUMS').write_text(''.join(f'{digest}  {name}\n' for name,digest in sorted(checks)))
    print(f'Packaged {len(groups)} archives from {commit}')
if __name__ == '__main__': main()
