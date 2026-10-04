#!/usr/bin/env python3
"""Opt-in project gates; not the upstream registry validator or a desktop test.

Python >=3.11. --check-images additionally requires Pillow (see requirements-media.txt).
No files are changed; no theme is installed or executed.
"""
import argparse
import math
from pathlib import Path
import re
import stat
import sys
import tomllib
import warnings

DENIED = {'alacritty.toml', 'foot.ini', 'ghostty.conf', 'kitty.conf', 'vscode.json'}
IMAGE_FORMATS = {'.png': 'PNG', '.jpg': 'JPEG', '.jpeg': 'JPEG', '.gif': 'GIF', '.bmp': 'BMP', '.webp': 'WEBP'}
MAX_BYTES = 50 * 1024 * 1024
MAX_PIXELS = 40_000_000
MAX_FRAMES = 256


def contrast_rule(value):
    match = re.fullmatch(r'([A-Za-z0-9_]+)/([A-Za-z0-9_]+)=([0-9]+(?:\.[0-9]+)?)', value)
    if not match:
        raise argparse.ArgumentTypeError('use KEY/KEY=RATIO, for example foreground/background=4.5')
    a, b, raw = match.groups()
    ratio = float(raw)
    if not math.isfinite(ratio) or not 1 <= ratio <= 21:
        raise argparse.ArgumentTypeError('contrast ratio must be between 1 and 21')
    return a, b, ratio


def luminance(value):
    if not isinstance(value, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', value):
        raise ValueError('selected contrast keys must be explicit #RRGGBB; resolve aliases/gradients with the target runtime separately')
    channels = [int(value[i:i+2], 16)/255 for i in (1, 3, 5)]
    linear = [x/12.92 if x <= .04045 else ((x+.055)/1.055)**2.4 for x in channels]
    return sum(x*w for x, w in zip(linear, (.2126, .7152, .0722)))


def files(root):
    """Reject links and special files without following them; exclude root Git metadata."""
    if root.is_symlink() or not root.is_dir():
        raise ValueError('use a real theme directory, not a symlink')
    pending = [root]
    result = []
    while pending:
        directory = pending.pop()
        for path in sorted(directory.iterdir()):
            if path == root / '.git':
                continue
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError(f'symlink: {path.relative_to(root)}')
            if stat.S_ISDIR(mode):
                pending.append(path)
            elif stat.S_ISREG(mode):
                result.append(path)
            else:
                raise ValueError(f'not a regular file: {path.relative_to(root)}')
    return sorted(result)


def check_image(path):
    # Import only when explicitly selected. Missing decoder fails the gate.
    from PIL import Image
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('image exceeds 50 MiB project limit')
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(path) as image:
            if image.format != IMAGE_FORMATS[path.suffix.lower()]:
                raise ValueError('decoded format does not match filename extension')
            if image.width * image.height > MAX_PIXELS:
                raise ValueError('image exceeds 40 million pixels')
            image.verify()
        with Image.open(path) as image:
            frames = getattr(image, 'n_frames', 1)
            if frames > MAX_FRAMES:
                raise ValueError('animation exceeds 256-frame project limit; validate separately')
            pixels = 0
            for frame in range(frames):
                image.seek(frame)
                pixels += image.width * image.height
                if pixels > MAX_PIXELS:
                    raise ValueError('decoded frames exceed 40 million total pixels')
                image.load()


def check(root, rules, deny_ignored=False, check_images=False):
    errors, notes = [], []
    inventory = files(root)
    if rules:
        palette = root / 'colors.toml'
        if palette not in inventory or palette.stat().st_size > 1024*1024:
            raise ValueError('contrast checks require a regular colors.toml <=1 MiB')
        values = tomllib.loads(palette.read_text(encoding='utf-8'))
        for a, b, minimum in rules:
            try:
                x, y = luminance(values[a]), luminance(values[b])
                ratio = (max(x, y)+.05)/(min(x, y)+.05)
                notes.append(f'CONTRAST {a}/{b}: {ratio:.4f}:1; required {minimum}:1')
                if ratio < minimum:
                    errors.append(f'{a}/{b} below chosen threshold {minimum}:1')
            except (KeyError, ValueError) as exc:
                errors.append(f'{a}/{b}: {exc}')
    if deny_ignored:
        for path in inventory:
            if path.parent == root and (path.name in DENIED or path.suffix == '.lua'):
                errors.append(f'ignored by reviewed Git-installed staging: {path.name}')
    if check_images:
        images = [p for p in inventory if p.suffix.lower() in IMAGE_FORMATS]
        if not images:
            errors.append('no supported image files to decode')
        for path in images:
            try:
                check_image(path)
                notes.append(f'DECODED {path.relative_to(root)}')
            except Exception as exc:
                errors.append(f'{path.relative_to(root)}: {type(exc).__name__}: {exc}')
        notes.append('NOT CHECKED: video decoding, image rights, preview composition or live rendering')
    return errors, notes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('theme', type=Path)
    parser.add_argument('--contrast', type=contrast_rule, action='append', default=[])
    parser.add_argument('--deny-ignored-files', action='store_true')
    parser.add_argument('--check-images', action='store_true')
    args = parser.parse_args()
    if not (args.contrast or args.deny_ignored_files or args.check_images):
        parser.error('choose at least one project gate; use the Rust helper for advisory checks')
    try:
        errors, notes = check(args.theme.absolute(), args.contrast, args.deny_ignored_files, args.check_images)
    except (OSError, ValueError) as exc:
        errors, notes = [str(exc)], []
    for note in notes:
        print(note)
    for error in errors:
        print(f'FAIL: {error}', file=sys.stderr)
    if errors:
        return 1
    print('PASS: selected project gates only; registry acceptance and desktop behaviour NOT CHECKED')
    return 0


if __name__ == '__main__':
    sys.exit(main())
