#!/usr/bin/env python3
"""Validate reviewed pins; --live checks exact pinned and current upstream bytes."""
import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path, PurePosixPath
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SHA = re.compile(r'[0-9a-f]{40}')
REPOSITORIES = {'omacom/omarchy', 'omacom/omarchy-theme-registry'}
MAX_BYTES = 2 * 1024 * 1024

def blob_sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def validate(data):
    errors, seen = [], set()
    try:
        date.fromisoformat(data['checked'])
        if not isinstance(data['sources'], list) or not data['sources']:
            raise ValueError('sources must be a nonempty list')
        for source in data['sources']:
            repo, path, ref = source['repository'], source['path'], source['ref']
            if repo not in REPOSITORIES:
                raise ValueError('unexpected source repository')
            if not isinstance(path, str) or not path or PurePosixPath(path).is_absolute() or any(p in ('', '.', '..') for p in path.split('/')) or '\\' in path:
                raise ValueError('unsafe source path')
            if not isinstance(ref, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+', ref):
                raise ValueError('invalid tracked ref')
            if not SHA.fullmatch(source['commit']) or not SHA.fullmatch(source['blob_sha']):
                raise ValueError('commit and blob_sha must be exact SHA-1 identities')
            identity = (repo, path)
            if identity in seen:
                raise ValueError('duplicate source identity')
            seen.add(identity)
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        errors.append(f'invalid source manifest: {exc}')
    return errors

def fetch(url):
    request = Request(url, headers={'User-Agent':'build-omarchy-themes-contract-check'})
    with urlopen(request, timeout=20) as response:
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError('upstream file exceeds size limit')
    return body

def check_live(sources, get=fetch):
    errors, notes, heads = [], [], {}
    for source in sources:
        repo, ref, path = source['repository'], source['ref'], source['path']
        label = f'{repo}:{path}'
        try:
            key = (repo, ref)
            if key not in heads:
                response = json.loads(get(f'https://api.github.com/repos/{repo}/commits/{quote(ref, safe="")}'))
                head = response['sha']
                if not isinstance(head, str) or not SHA.fullmatch(head):
                    raise ValueError('invalid upstream commit response')
                heads[key] = head
            head = heads[key]
            def raw(commit):
                return get(f'https://raw.githubusercontent.com/{repo}/{commit}/{quote(path, safe="/")}')
            pinned = raw(source['commit'])
            if blob_sha(pinned) != source['blob_sha']:
                errors.append(f'{label}: pinned content does not match recorded blob')
                continue
            current = pinned if head == source['commit'] else raw(head)
            if blob_sha(current) != source['blob_sha']:
                errors.append(f'{label}: upstream content changed; review before updating pin')
            elif head != source['commit']:
                notes.append(f'{label}: branch moved; contract content unchanged')
            else:
                notes.append(f'{label}: reviewed commit and content unchanged')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f'{label}: unavailable or invalid upstream response ({type(exc).__name__})')
    return errors, notes

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--manifest', type=Path, default=ROOT/'contracts/sources.json')
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text())
        errors = validate(data)
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
    if not errors and args.live:
        errors, notes = check_live(data['sources'])
        for note in notes:
            print('INFO:', note)
    for error in errors:
        print('ERROR:', error)
    if not errors:
        print('PASS: live contract content' if args.live else 'PASS: pin structure only; upstream freshness NOT CHECKED')
    return bool(errors)

if __name__ == '__main__':
    raise SystemExit(main())
