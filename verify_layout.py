"""Check repeated semantic styles and spacing in the rendered sidebar PDF.

Uses Poppler geometry and font runs. Structural labels must fit on one line;
ambiguous/wrapped labels fail closed and require explicit verifier support.
"""
import re
import subprocess
import xml.etree.ElementTree as ET


def compact(value):
    return re.sub(r'\s+', '', value).replace('\u00ad', '')


def check(condition, message):
    if not condition:
        raise ValueError('Layout consistency: ' + message)


def topics_for(job):
    topics = []
    for group in job['groups']:
        if group['heading'] == 'Main Contributions':
            for bullet in group['bullets']:
                heading, separator, body = bullet.partition(': ')
                topics.append({'heading': heading if separator else '',
                               'bullets': [body if separator else bullet]})
        else:
            topics.append(group)
    return topics


def verify_layout(pdf, profile, settings):
    ns = {'x': 'http://www.w3.org/1999/xhtml'}
    bbox = ET.fromstring(subprocess.check_output(['pdftotext', '-bbox-layout', str(pdf), '-']))
    pages = bbox.findall('.//x:page', ns)
    check(len(pages) == 1, 'the fixed sidebar layout verifier currently supports one page')
    page = pages[0]
    # The template's main column starts at 66 mm; sidebar starts at 11 mm.
    main_left = 66 * 72 / 25.4
    lines = []
    for node in page.findall('.//x:line', ns):
        if float(node.attrib['xMin']) >= main_left - 0.5:
            lines.append({'text': ' '.join(w.text or '' for w in node.findall('x:word', ns)),
                          **{k: float(v) for k, v in node.attrib.items()}})
    lines.sort(key=lambda line: (line['yMin'], line['xMin']))
    check(lines, 'main-column text not found')
    xml = ET.fromstring(subprocess.check_output(
        ['pdftohtml', '-xml', '-hidden', '-fontfullname', '-i', '-zoom', '1', '-stdout', str(pdf)]))
    fonts = {f.attrib['id']: (f.attrib['family'].split('+')[-1],
                              int(f.attrib['size']), f.attrib['color'])
             for f in xml.findall('.//fontspec')}
    runs = []
    for run in xml.findall('.//text'):
        runs.append({'text': ''.join(run.itertext()), 'x': float(run.attrib['left']),
                     'y': float(run.attrib['top']), 'style': fonts[run.attrib['font']]})

    def line_for(text, low, high):
        found = [line for line in lines if low <= line['yMin'] < high
                 and compact(text) in compact(line['text'])]
        check(len(found) == 1,
              f'cannot uniquely locate single-line structural label {text!r}; inspect wrapping/alignment')
        return found[0]

    def after(line, high):
        found = [other for other in lines if line['yMax'] < other['yMin'] < high]
        check(found, f'no content follows {line["text"]!r}')
        return found[0]

    def style_for(text, line, column="main"):
        # Font runs use integer coordinates; geometry checks use precise bboxes.
        row = [r for r in runs if abs(r['y'] - line['yMin']) <= 1.2
               and ((r['x'] >= main_left - 0.5) if column == 'main' else (r['x'] < main_left - 0.5))]
        row.sort(key=lambda r: r['x'])
        value = compact(text)
        position = ''.join(compact(r['text']) for r in row).find(value)
        check(position >= 0, f'cannot locate font runs for {text!r}')
        styles = []
        cursor = 0
        for run in row:
            end = cursor + len(compact(run['text']))
            if end > position and cursor < position + len(value):
                styles.append(run['style'])
            cursor = end
        check(styles, f'no font style found for {text!r}')
        return styles

    classes = {name: [] for name in ('employer', 'date', 'role', 'location', 'topic', 'body', 'duration')}
    gaps = {name: [] for name in ('role-content', 'heading-body', 'topic', 'contribution', 'employer')}
    alignments = {name: [] for name in ('employer', 'date-right', 'role', 'topic', 'body', 'bullet')}
    jobs = [job for job in profile['experience'] if job.get('id') not in settings['omitted_experience']]
    check(jobs, 'at least one visible employer is required')
    headers = []
    cursor = 0
    for job in jobs:
        header = line_for(job['company'], cursor, float(page.attrib['height']))
        headers.append(header)
        cursor = header['yMax']
    for index, (job, header) in enumerate(zip(jobs, headers)):
        high = headers[index + 1]['yMin'] if index + 1 < len(headers) else float(page.attrib['height'])
        date = line_for(job['dates'], header['yMin'] - 1, header['yMax'] + 1)
        role = line_for(job['role'] + ' · ' + job['location'], header['yMax'], high)
        check(abs(header['yMin'] - date['yMin']) <= 1.5, 'date not aligned with employer heading')
        classes['employer'] += style_for(job['company'], header)
        classes['date'] += style_for(job['dates'], date)
        classes['role'] += style_for(job['role'], role)
        classes['location'] += style_for(job['location'], role)
        alignments['employer'].append(header['xMin'])
        alignments['date-right'].append(date['xMax'])
        if job.get('duration'):
            duration = line_for(job['duration'], date['yMax'], role['yMax'] + 1)
            check(abs(duration['yMin'] - role['yMin'] + 3.69) <= 0.3,
                  'duration must sit 3.69pt above the role line')
            gaps.setdefault('date-duration', []).append(duration['yMin'] - date['yMax'])
            check(abs(duration['xMax'] - date['xMax']) <= 0.5,
                  'duration not right-aligned with date')
            classes['duration'] += style_for(job['duration'], duration)
            check(style_for(job['duration'], duration) == style_for(job['dates'], date),
                  'duration typography must match date')

        alignments['role'].append(role['xMin'])
        first = after(role, high)
        gaps['role-content'].append(first['yMin'] - role['yMax'])
        if index:
            previous = max(line['yMax'] for line in lines if headers[index - 1]['yMax'] < line['yMax'] < header['yMin'])
            gaps['employer'].append(header['yMin'] - previous)
        previous_end = None
        for topic in topics_for(job):
            # First line of a paragraph may wrap; match its starting word sequence.
            if topic['heading']:
                title = line_for(topic['heading'], role['yMax'], high)
                classes['topic'] += style_for(topic['heading'], title)
                alignments['topic'].append(title['xMin'])
                body = after(title, high)
                gaps['heading-body'].append(body['yMin'] - title['yMax'])
                if previous_end is not None:
                    gaps['topic'].append(title['yMin'] - previous_end)
            else:
                body = first
            for number, bullet in enumerate(topic['bullets']):
                normalized = compact(bullet)
                candidates = [line for line in lines if role['yMax'] < line['yMin'] < high
                              and compact(line['text'].lstrip('• '))
                              and normalized.startswith(compact(line['text'].lstrip('• ')))]
                check(candidates, f'cannot locate contribution beginning {bullet[:50]!r}')
                start = candidates[0]
                first_text = start['text'].lstrip('• ')
                classes['body'] += style_for(first_text, start)
                if len(topic['bullets']) > 1:
                    markers = [r['x'] for r in runs if abs(r['y'] - start['yMin']) <= 1.2
                               and r['x'] >= main_left - 0.5 and r['text'].strip() == '•']
                    check(markers, 'cannot locate bullet marker')
                    alignments['bullet'].append(min(markers))
                    text_runs = [r for r in runs if abs(r['y'] - start['yMin']) <= 1.2
                                 and r['x'] >= main_left - 0.5 and r['text'].strip() != '•']
                    check(text_runs, 'cannot locate indented bullet text')
                    alignments.setdefault('bullet-text', []).append(min(r['x'] for r in text_runs))
                else:
                    alignments['body'].append(start['xMin'])
                if number and previous_end is not None:
                    gaps['contribution'].append(start['yMin'] - previous_end)
                # Read the complete paragraph's consecutive lines, excluding bullets.
                consumed = ''
                last = start
                for line in lines:
                    if line['yMin'] < start['yMin'] or line['yMin'] >= high:
                        continue
                    part = compact(line['text'].lstrip('• '))
                    if not part:
                        continue
                    if normalized.startswith(consumed + part):
                        consumed += part
                        last = line
                        classes['body'] += style_for(line['text'].lstrip('• '), line)
                    if consumed == normalized:
                        break
                check(consumed == normalized, 'cannot measure complete contribution paragraph')
                previous_end = last['yMax']
    # Check repeated sidebar semantics too, without equating unrelated levels.
    side_lines = []
    for node in page.findall('.//x:line', ns):
        if float(node.attrib['xMin']) < main_left - 0.5:
            side_lines.append({'text': ' '.join(w.text or '' for w in node.findall('x:word', ns)),
                               **{k: float(v) for k, v in node.attrib.items()}})
    side_lines.sort(key=lambda line: (line['yMin'], line['xMin']))

    def side_phrase(text, low=0):
        target = compact(text)
        for index, start in enumerate(side_lines):
            if start['yMin'] < low:
                continue
            consumed, matched = '', []
            for line in side_lines[index:]:
                part = compact(line['text'])
                if not target.startswith(consumed + part):
                    break
                consumed += part
                matched.append(line)
                if consumed == target:
                    return matched
        check(False, f'cannot locate sidebar text {text!r}')

    def side_style(kind, text, low=0):
        matched = side_phrase(text, low)
        for line in matched:
            classes.setdefault(kind, []).extend(style_for(line['text'], line, 'side'))
        return matched[0], matched[-1]

    for title in ['CONTACT', 'SKILLS', 'LANGUAGES', 'EDUCATION']:
        side_style('sidebar-section', title)
    values = [('Location', profile['location']), ('Phone', profile['phone']), ('Email', profile['email']),
              ('LinkedIn', profile['linkedin'].rstrip('/').split('/')[-1]),
              ('GitHub', profile['github'].rstrip('/').split('/')[-1])]
    previous_end = None
    for title, value in values:
        first, last = side_style('contact-label', title)
        value_first, value_last = side_style('contact-value', value, last['yMax'])
        gaps.setdefault('contact-label-value', []).append(value_first['yMin'] - last['yMax'])
        if previous_end is not None:
            gaps.setdefault('contact-field', []).append(first['yMin'] - previous_end)
        previous_end = value_last['yMax']
    low = side_phrase('SKILLS')[0]['yMin']
    for skill in profile['skills']:
        _, last = side_style('skill-heading', skill['heading'], low)
        previous_end = None
        for item in skill['items']:
            first, final = side_style('skill-item', item, last['yMax'])
            if previous_end is None:
                gaps.setdefault('skill-heading-items', []).append(first['yMin'] - last['yMax'])
            else:
                gaps.setdefault('skill-items', []).append(first['yMin'] - previous_end)
            previous_end = final['yMax']
        low = previous_end
    for language in profile['languages'].split(' · '):
        side_style('language', language, side_phrase('LANGUAGES')[0]['yMax'])
    low = side_phrase('EDUCATION')[0]['yMax']
    for education in profile['education']:
        _, last = side_style('school', education['school'], low)
        for field in ['location', 'dates', 'degree', 'detail']:
            _, last = side_style('education-detail', education[field], last['yMax'])
        low = last['yMax']
    for name, values in classes.items():
        if values:
            check(len(set(values)) == 1, f'inconsistent {name} typography (font, size or color): {set(values)}')
    for name, values in gaps.items():
        if values:
            check(min(values) > 0, f'non-positive {name} spacing')
            check(max(values) - min(values) <= 0.3,
                  f'inconsistent {name} spacing: {[round(v, 2) for v in values]} pt')
    for name, values in alignments.items():
        if values:
            check(max(values) - min(values) <= 0.5, f'inconsistent {name} alignment')
    check(classes['body'], 'at least one visible contribution is required')
    check(classes['employer'][0][1] > classes['body'][0][1], 'employer headings must be larger than body text')
    if classes['topic']:
        check(classes['employer'][0][1] > classes['topic'][0][1], 'employer headings must be larger than topics')
    print('PASS rendered layout: repeated typography, alignment and spacing are consistent.')
