#!/usr/bin/env python3
"""Create an independent FolioPress profile without copying anyone else's facts."""
import argparse
import json
import re
import shlex
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('slug', help='Folder name, e.g. alex-smith')
    parser.add_argument('--name', required=True)
    parser.add_argument('--title', required=True)
    parser.add_argument('--directory', help='Create the profile at this path instead of profiles/<slug>')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', args.slug):
        parser.error('Use lowercase letters, numbers and hyphens for the folder name.')
    folder = Path(args.directory).resolve() if args.directory else ROOT / 'profiles' / args.slug
    if folder.exists():
        parser.error(f'{folder} already exists; refusing to overwrite it.')
    profile = {
        'name': args.name, 'title': args.title,
        'location': 'TODO: City, Country', 'phone': 'TODO: Phone number',
        'email': 'TODO: Email address', 'linkedin': 'TODO: LinkedIn URL',
        'github': 'TODO: GitHub URL',
        'experience': [{
            'id': 'first-job', 'company': 'TODO: Employer', 'role': args.title,
            'location': 'TODO: City, Country', 'dates': 'TODO: Start – End',
            'groups': [{'heading': 'Selected contributions', 'bullets': [
                'TODO: Describe your contribution, ownership and outcome using confirmed facts.'
            ]}],
        }],
        'education': [{
            'school': 'TODO: Institution', 'location': 'TODO: City, Country',
            'degree': 'TODO: Qualification', 'dates': 'TODO: Start – End',
            'detail': 'TODO: Confirmed specialization or grade',
        }],
        'skills': [{'heading': 'Technical skills', 'items': ['TODO: Your confirmed skills']}],
        'languages': 'TODO: Language — Proficiency',
    }
    folder.mkdir(parents=True)
    (folder / 'profile.json').write_text(json.dumps(profile, ensure_ascii=False, indent=2) + '\n')
    (folder / 'cv-settings.json').write_text(json.dumps({'omitted_experience': [], 'max_pages': 1}, indent=2) + '\n')
    (folder / 'AGENTS.md').write_text(
        f'# {args.name} — personal CV instructions\n\n'
        'Follow root AGENTS.md. This is an independent profile, not an adaptation of another person’s facts.\n'
        'Replace TODO fields only with owner-confirmed information before producing a final PDF.\n'
        'Ask the owner for missing facts and record personal preferences here.\n')
    print(f'Created {folder}. Keep real data in a private workspace. Fill TODO fields, then run:')
    print(f'python3 {shlex.quote(str(ROOT / "build.py"))} --profile {shlex.quote(str(folder))}')

if __name__ == '__main__':
    main()
