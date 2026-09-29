"""Generate sealed mapping only after readiness stages 1–6; never prints mapping/seed."""
import argparse
import random
import secrets
import sys
from pathlib import Path
from common import CASES, SETTINGS, read, write, restricted, private_write, sha


def generate(destination):
    # SystemRandom draws from the OS; no reproducible seed is disclosed or persisted.
    rng = random.SystemRandom()
    sessions = []
    for case in CASES:
        for setting in SETTINGS:
            for rep in range(1, 4):
                arms = ['baseline', 'candidate']
                rng.shuffle(arms)
                for arm in arms:
                    sessions.append({'id': secrets.token_hex(16), 'case': case, 'setting': setting, 'repetition': rep, 'arm': arm})
    path = restricted(destination) / 'arm-mapping.json'
    private_write(path, {'sessions': sessions})
    return {'sha256': sha(path.read_bytes()), 'session_ids': sorted(s['id'] for s in sessions)}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', required=True)
    p.add_argument('--restricted-dir', required=True)
    p.add_argument('--public-output', required=True)
    a = p.parse_args()
    from readiness import errors
    problems = errors(read(a.manifest), through=6)
    if problems:
        sys.exit('Mapping blocked: ' + '; '.join(problems))
    write(a.public_output, generate(a.restricted_dir), exclusive=True)
