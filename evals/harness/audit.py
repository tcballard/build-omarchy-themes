"""Commit this public audit selection after sealed mapping generation, before execution."""
import argparse
import platform
import random
from common import read, write


def select(ids):
    if len(ids) != 144 or len(set(ids)) != 144:
        raise ValueError('Exactly 144 unique opaque IDs required')
    return {'seed': 20260929, 'python': platform.python_version(), 'session_ids': random.Random(20260929).sample(sorted(ids), 29)}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('public_mapping'); p.add_argument('output')
    a = p.parse_args()
    write(a.output, select(read(a.public_mapping)['session_ids']), exclusive=True)
