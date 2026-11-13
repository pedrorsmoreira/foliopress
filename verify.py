#!/usr/bin/env python3
"""Validate content, page bounds/fonts and reading order. Visual review is separate."""
import argparse
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def require(condition, message):
    if not condition:
        raise ValueError(message)

def normalize(text):
    return re.sub(r'\s+', '', text).replace('\u00ad', '').replace(':', '')

def validate_inputs(profile, settings):
    def unfinished(value):
        if isinstance(value, str):
            return value.startswith('TODO:')
        if isinstance(value, dict):
            return any(unfinished(v) for v in value.values())
        if isinstance(value, list):
            return any(unfinished(v) for v in value)
        return False
    require(not unfinished(profile), 'Unfinished profile: replace all TODO fields with confirmed facts before building.')
    for key in ('name', 'title', 'location', 'phone', 'email', 'linkedin', 'github', 'languages'):
        require(isinstance(profile.get(key), str) and profile[key].strip(), f'Missing profile field: {key}')
    require(isinstance(settings.get('max_pages'), int) and settings['max_pages'] >= 1, 'max_pages must be positive')
    require(isinstance(settings.get('omitted_experience'), list), 'omitted_experience must be a list')
    for job in profile['experience']:
        for key in ('company', 'role', 'location', 'dates', 'groups'):
            require(key in job, f'Missing job field: {key}')
        if 'duration' in job:
            require(isinstance(job['duration'], str) and job['duration'].strip(), 'duration must be a non-empty string')
        require(all(isinstance(b, str) and b for g in job['groups'] for b in g['bullets']), 'Empty/invalid contribution')
    ids = {j.get('id') for j in profile['experience'] if j.get('id')}
    require(set(settings['omitted_experience']) <= ids, 'Unknown omitted experience ID')
    require(len(ids) == len([j for j in profile['experience'] if j.get('id')]), 'Duplicate experience IDs')
    require(profile['education'] and profile['skills'], 'Education and skills required')

def command(*args):
    return subprocess.check_output(list(args), text=True)

def ordered(text, anchors, description):
    text = normalize(text)
    cursor = 0
    for anchor in anchors:
        needle = normalize(anchor)
        found = text.find(needle, cursor)
        require(found >= 0, f'{description}: missing/out-of-order {anchor[:80]}')
        cursor = found + len(needle)

def history_anchors(profile, settings):
    anchors = []
    for job in profile['experience']:
        if job.get('id') in settings['omitted_experience']:
            continue
        anchors.extend([job['company'], job['dates'], job['role'], job['location']])
        if job.get('duration'):
            anchors.append(job['duration'])
        for group in job['groups']:
            if group['heading'] and group['heading'] != 'Main Contributions':
                anchors.append(group['heading'])
            anchors.extend(group['bullets'])
    return anchors

def education_anchors(profile):
    anchors = []
    for edu in profile['education']:
        anchors.extend([edu['school'], edu['location'], edu['dates'], edu['degree'], edu['detail']])
    return anchors

def verify(pdf, profile, settings):
    validate_inputs(profile, settings)
    info = command('pdfinfo', str(pdf))
    pages = int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1])
    require(pages <= settings['max_pages'], f'{pdf.name}: {pages} pages exceeds configured limit')
    require('595.276 x 841.89' in info, 'Expected A4 page size')
    raw = command('pdftotext', '-raw', str(pdf), '-')
    actual = normalize(raw)
    history = history_anchors(profile, settings)
    expected = history + education_anchors(profile)
    expected += [profile[k] for k in ('name', 'title', 'location', 'phone', 'email')]
    expected += [profile['linkedin'].rstrip('/').split('/')[-1], profile['github'].rstrip('/').split('/')[-1]]
    expected += profile['languages'].split(' · ')
    expected += [v for skill in profile['skills'] for v in [skill['heading'], *skill['items']]]
    for item in expected:
        require(normalize(item) in actual, f'{pdf.name}: missing/changed content: {item[:80]}')
    for job in profile['experience']:
        if job.get('id') in settings['omitted_experience']:
            for group in job['groups']:
                for bullet in group['bullets']:
                    require(normalize(bullet) not in actual, f'Omitted contribution unexpectedly rendered: {bullet[:70]}')
    xml = command('pdftotext', '-bbox', str(pdf), '-')
    tree = ET.fromstring(xml)
    ns = {'x': 'http://www.w3.org/1999/xhtml'}
    words = tree.findall('.//x:word', ns)
    require(words, 'No real PDF text')
    for page in tree.findall('.//x:page', ns):
        width, height = float(page.attrib['width']), float(page.attrib['height'])
        for word in page.findall('.//x:word', ns):
            a = word.attrib
            require(0 <= float(a['xMin']) < float(a['xMax']) <= width, 'Text outside horizontal page bounds')
            require(0 <= float(a['yMin']) < float(a['yMax']) <= height, 'Text outside vertical page bounds')
    fonts = command('pdffonts', str(pdf)).splitlines()[2:]
    require(fonts and all(re.search(r'\byes\s+yes\s+yes\b', line) for line in fonts if line.strip()),
            'Expected embedded subset fonts with Unicode maps')
    skill_anchors = [v for skill in profile['skills'] for v in [skill['heading'], *skill['items']]]
    anchors = [profile['name'], profile['title'], 'EXPERIENCE', *history, 'CONTACT', 'SKILLS',
               *skill_anchors, 'LANGUAGES', *profile['languages'].split(' · '), 'EDUCATION', *education_anchors(profile)]
    ordered(raw, anchors, 'Sidebar content stream')
    tags = command('pdfinfo', '-struct-text', str(pdf))
    # Quoted line fragments in pdfinfo's dump are checked with short anchors;
    # full paragraphs are separately checked above in content-stream order.
    tag_anchors = [profile['name'], 'EXPERIENCE']
    tag_anchors += [j['company'] for j in profile['experience'] if j.get('id') not in settings['omitted_experience']]
    tag_anchors += ['CONTACT', 'SKILLS', 'LANGUAGES', 'EDUCATION']
    ordered(tags, tag_anchors, 'Sidebar PDF tags')
    previews = pdf.parent / 'previews'
    previews.mkdir(exist_ok=True)
    (previews / 'reading-order.txt').write_text(raw)
    from verify_layout import verify_layout
    verify_layout(pdf, profile, settings)
    print(f'PASS {pdf.name}: {pages} A4 page(s), content, bounds, fonts and declared reading order.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True, help='Profile folder')
    parser.add_argument('--output-dir', help='Override that profile’s output folder')
    args = parser.parse_args()
    folder = Path(args.profile).resolve()
    profile = json.loads((folder / 'profile.json').read_text())
    settings = json.loads((folder / 'cv-settings.json').read_text())
    output = Path(args.output_dir).resolve() if args.output_dir else folder / 'output'
    verify(output / 'cv.pdf', profile, settings)

if __name__ == '__main__':
    main()
