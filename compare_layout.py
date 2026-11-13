#!/usr/bin/env python3
"""Compare rendered pixels against the approved sidebar; not PDF metadata bytes."""
import hashlib
import argparse
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True, help='Profile folder with reference/approved.pdf')
    parser.add_argument('--output-dir')
    args = parser.parse_args()
    folder = Path(args.profile).resolve()
    output = Path(args.output_dir).resolve() if args.output_dir else folder / 'output'
    with tempfile.TemporaryDirectory() as temp:
        digests = []
        for label, pdf in [('approved', folder / 'reference/approved.pdf'),
                           ('current', output / 'cv.pdf')]:
            prefix = Path(temp) / label
            subprocess.run(['pdftoppm', '-r', '144', '-png', str(pdf), str(prefix)], check=True)
            pages = sorted(Path(temp).glob(label + '-*.png'))
            digests.append([hashlib.sha256(p.read_bytes()).hexdigest() for p in pages])
        if digests[0] != digests[1]:
            raise SystemExit('Rendered layout differs from the approved reference. Review the images; content edits may legitimately differ.')
    print('PASS: all rendered pixels match the approved sidebar at 144 DPI.')

if __name__ == '__main__':
    main()
