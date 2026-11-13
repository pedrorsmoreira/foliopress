#!/usr/bin/env python3
"""Build, validate and render the approved CV from a profile/settings pair."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--profile', help='Folder containing profile.json and cv-settings.json')
    selection.add_argument('--all', action='store_true', help='Build every profile and saved variant')
    parser.add_argument('--output-dir', help='Override the selected profile’s output folder')
    args = parser.parse_args()
    if args.all:
        if args.output_dir:
            parser.error('--output-dir requires --profile')
        profiles = sorted((ROOT / 'profiles').rglob('profile.json'))
        if not profiles:
            raise SystemExit('No profiles found.')
        for profile in profiles:
            build(profile.parent)
    else:
        build(Path(args.profile).resolve(), args.output_dir)

def build(folder, output_dir=None):
    profile = folder / 'profile.json'
    settings = folder / 'cv-settings.json'
    output = Path(output_dir).resolve() if output_dir else folder / 'output'
    from verify import validate_inputs, verify
    data, config = [json.loads(p.read_text()) for p in (profile, settings)]
    validate_inputs(data, config)
    lock = json.loads((ROOT / 'toolchain.json').read_text())
    for filename, expected in lock['fonts'].items():
        if hashlib.sha256((ROOT / filename).read_bytes()).hexdigest() != expected:
            raise SystemExit(f'Font changed: {filename}; review before updating the font lock.')
    compiler = ROOT / '.tools/bin/typst'
    compiler = str(compiler) if compiler.is_file() else shutil.which('typst')
    if not compiler:
        raise SystemExit('Typst missing. Run python3 bootstrap.py first.')
    if subprocess.check_output([compiler, '--version'], text=True).strip() != lock['typst_version']:
        raise SystemExit('Wrong Typst version. Run python3 bootstrap.py for the pinned compiler.')
    for tool in ('pdfinfo', 'pdftotext', 'pdffonts', 'pdftoppm', 'pdftohtml'):
        if not shutil.which(tool):
            raise SystemExit(f'Missing {tool}. Install Poppler (Ubuntu/Debian: poppler-utils).')
    output.mkdir(parents=True, exist_ok=True)
    pdf = output / 'cv.pdf'
    # Stage only the selected inputs and template, keeping Typst's file root narrow.
    # No personal data is copied into the public checkout.
    with tempfile.TemporaryDirectory(prefix='foliopress-') as temp:
        stage = Path(temp)
        shutil.copytree(ROOT / 'templates', stage / 'templates')
        (stage / 'profile.json').write_text(json.dumps(data, ensure_ascii=False))
        (stage / 'cv-settings.json').write_text(json.dumps(config, ensure_ascii=False))
        subprocess.run([compiler, 'compile', '--root', str(stage), '--font-path', str(ROOT / 'fonts'),
                        '--ignore-system-fonts', '--creation-timestamp', str(lock['creation_timestamp']),
                        '--input', 'profile=../profile.json',
                        '--input', 'settings=../cv-settings.json',
                        str(stage / 'templates/sidebar.typ'), str(pdf)], check=True)
    verify(pdf, data, config)
    previews = output / 'previews'
    previews.mkdir(exist_ok=True)
    subprocess.run(['pdftoppm', '-scale-to', '1700', '-png', str(pdf), str(previews / 'cv')], check=True)
    print(f'Built the CV in {output}. Visually inspect every preview before delivery.')

if __name__ == '__main__':
    main()
