"""Offline evaluation utilities. Never import skills as Python or execute fixture sources."""
import hashlib
import json
import os
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES = ('accent-only', 'diagnose-staging', 'helper-unavailable', 'ideas-only', 'neighbour-bug', 'override-present')
SETTINGS = ('fable-high', 'opus-medium', 'sonnet-medium', 'sonnet-low')
SKILL_PATH = '/opt/evaluation/.claude/skills'
FIXTURE_PATH = '/work/fixture'
SECONDARY = ('closest_builtin_comparison', 'neighbour_followup_reported', 'override_named_before_edit')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def write(path, value, exclusive=False):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x' if exclusive else 'w') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')

def inventory(root):
    result = []
    for p in sorted(Path(root).rglob('*')):
        if p.is_symlink():
            raise ValueError('Symlinks are forbidden in delivered fixtures')
        if p.is_file():
            result.append({'path': p.relative_to(root).as_posix(), 'mode': format(stat.S_IMODE(p.stat().st_mode), '04o'), 'sha256': sha(p.read_bytes())})
    return result

def restricted(path):
    p = Path(path).resolve()
    if p == ROOT or ROOT in p.parents:
        raise ValueError('Restricted storage must be outside the repository')
    p.mkdir(parents=True, exist_ok=True, mode=0o700)
    p.chmod(0o700)
    return p

def private_write(path, value):
    p = Path(path)
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump(value, f, sort_keys=True)
        f.write('\n')

def evaluator(case):
    if case not in CASES:
        raise ValueError('Unknown case')
    return read(ROOT / 'evals/evaluator-manifests/claude-v0.2.1' / (case + '.json'))
