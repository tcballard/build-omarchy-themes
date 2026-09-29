#!/usr/bin/env python3
"""Check release versions, provider paths and independent shared references."""
import argparse
import json
import re
from pathlib import Path

NAME = 'build-omarchy-themes'
MANIFESTS = ('plugin.json', '.claude-plugin/plugin.json',
             f'plugins/{NAME}/.codex-plugin/plugin.json')

def validate(root):
    errors = []
    try:
        version = (root / 'VERSION').read_text().strip()
        if not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version):
            errors.append('VERSION must be a release semantic version')
        for path in MANIFESTS:
            manifest = json.loads((root / path).read_text())
            if manifest.get('version') != version or manifest.get('name') != NAME:
                errors.append(f'{path}: name/version differs from release')
        adapter = json.loads((root / MANIFESTS[-1]).read_text())
        if adapter.get('skills') != './skills/':
            errors.append('OpenAI adapter skills path must be ./skills/')
        agents = json.loads((root / '.agents/plugins/marketplace.json').read_text())
        claude = json.loads((root / '.claude-plugin/marketplace.json').read_text())
        if [(p.get('name'), p.get('source')) for p in agents['plugins']] != [(NAME, {'source':'local', 'path':f'./plugins/{NAME}'})]:
            errors.append('OpenAI marketplace points to the wrong local plugin')
        if [(p.get('name'), p.get('source')) for p in claude['plugins']] != [(NAME, './')]:
            errors.append('Claude marketplace points to the wrong local plugin')
        if not (root / f'docs/releases/v{version}.md').is_file():
            errors.append('release notes missing for VERSION')
        skills = sorted((root / 'skills').glob('*/SKILL.md'))
        if len(skills) != 12:
            errors.append('expected twelve canonical skills')
        contracts, completions = set(), set()
        for skill in skills:
            contracts.add((skill.parent / 'references/contract.md').read_bytes())
            text = skill.read_text()
            if '\n## Task completion\n' not in text:
                errors.append(f'{skill.parent.name}: missing completion contract')
            else:
                completions.add(text.split('\n## Task completion\n', 1)[1])
        if len(contracts) != 1:
            errors.append('shared contract references differ')
        if len(completions) != 1:
            errors.append('shared task completion guidance differs')
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        errors.append(f'cannot validate bundle: {exc}')
    return errors

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root)
    for error in errors:
        print('ERROR:', error)
    if not errors:
        print('PASS: versions, provider entry points and shared references')
    return bool(errors)

if __name__ == '__main__':
    raise SystemExit(main())
