"""Render real PDFs and prove the verifier rejects inconsistent formatting."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from verify_layout import verify_layout

ROOT = Path(__file__).resolve().parents[1]


class RenderedConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='.layout-check-', dir=ROOT)
        cls.addClassCleanup(cls.temp.cleanup)
        cls.folder = Path(cls.temp.name)
        compiler = ROOT / '.tools/bin/typst'
        cls.compiler = str(compiler) if compiler.is_file() else shutil.which('typst')
        if not cls.compiler:
            raise RuntimeError('Run python3 bootstrap.py before the rendered regression tests.')
        cls.profile = {
            'name': 'Fixture Example', 'title': 'Software Engineer',
            'location': 'Example City', 'phone': '+1 202 555 0147',
            'email': 'fixture@example.com', 'linkedin': 'https://example.com/link',
            'github': 'https://example.com/code',
            'experience': [
                {'id': 'first', 'company': 'Fixture Alpha', 'role': 'Software Engineer',
                 'location': 'Example City', 'dates': 'Jan 2024 – Present',
                 'groups': [{'heading': 'Platform delivery', 'bullets': ['Built a fictional platform for this verification fixture.']},
                            {'heading': 'Reliability', 'bullets': ['Added fictional monitoring and deployment checks.']}]},
                {'id': 'second', 'company': 'Fixture Beta', 'role': 'Software Engineer',
                 'location': 'Example City', 'dates': 'Jan 2022 – Dec 2023',
                 'groups': [{'heading': 'Main Contributions', 'bullets': [
                     'Project One: Designed a fictional service for repeatable regression tests.',
                     'Project Two: Implemented a fictional pipeline and verified its behavior.']},
                            {'heading': 'Mentoring', 'bullets': [
                                'Prepared fictional training exercises for a test profile.',
                                'Ran fictional workshops for this test profile.']}]},
                {'id': 'third', 'company': 'Fixture Gamma', 'role': 'Software Engineer',
                 'location': 'Example City', 'dates': 'Jan 2020 – Dec 2021',
                 'groups': [{'heading': '', 'bullets': [
                     'Researched fictional data for a regression fixture.',
                     'Implemented a fictional prototype and documented its behavior.']}]},
            ],
            'education': [{'school': 'Example University', 'location': 'Example City',
                           'dates': '2016 – 2020', 'degree': 'BSc Computer Science', 'detail': 'Fictional fixture'}],
            'skills': [{'heading': 'Technical skills', 'items': ['Python', 'Testing']}],
            'languages': 'English — Fluent',
        }
        cls.settings = {'omitted_experience': [], 'max_pages': 1}
        (cls.folder / 'profile.json').write_text(json.dumps(cls.profile))
        (cls.folder / 'settings.json').write_text(json.dumps(cls.settings))
        cls.source = (ROOT / 'templates/sidebar.typ').read_text()

    def render(self, old=None, new=None):
        source = self.source
        if old is not None:
            self.assertEqual(source.count(old), 1, 'Mutation anchor changed; update the regression fixture deliberately.')
            source = source.replace(old, new)
        template = self.folder / 'test.typ'
        pdf = self.folder / 'test.pdf'
        template.write_text(source)
        subprocess.run([self.compiler, 'compile', '--root', str(ROOT), '--font-path', str(ROOT / 'fonts'),
                        '--ignore-system-fonts', '--input', 'profile=profile.json',
                        '--input', 'settings=settings.json', str(template), str(pdf)],
                       check=True, capture_output=True)
        return pdf

    def test_headed_projects_and_untitled_bullets_are_consistent(self):
        verify_layout(self.render(), self.profile, self.settings)

    def test_missing_lead_in_for_untitled_job_is_rejected(self):
        pdf = self.render('v(spacing.role-content, weak: false)',
                          'if job-index != 2 { v(spacing.role-content, weak: false) }')
        with self.assertRaisesRegex(ValueError, 'inconsistent role-content spacing'):
            verify_layout(pdf, self.profile, self.settings)

    def test_different_employer_separation_is_rejected(self):
        pdf = self.render('if job-index > 0 { v(spacing.employer, weak: false) }',
                          'if job-index > 0 { v(spacing.employer + if job-index == 2 { 4pt } else { 0pt }, weak: false) }')
        with self.assertRaisesRegex(ValueError, 'inconsistent employer spacing'):
            verify_layout(pdf, self.profile, self.settings)

    def test_different_topic_format_is_rejected(self):
        pdf = self.render('block(sticky: true, strong(topic.heading))',
                          'block(sticky: true, text(size: if job-index == 1 { 12pt } else { 10.5pt }, weight: "bold", topic.heading))')
        with self.assertRaisesRegex(ValueError, 'inconsistent topic typography'):
            verify_layout(pdf, self.profile, self.settings)

    def test_different_body_color_is_rejected(self):
        pdf = self.render('} else { block(bullet) }',
                          '} else { block(text(fill: if job-index == 1 { red } else { black }, bullet)) }')
        with self.assertRaisesRegex(ValueError, 'inconsistent body typography'):
            verify_layout(pdf, self.profile, self.settings)

    def test_misaligned_date_is_rejected(self):
        pdf = self.render('], job.dates)',
                          '], move(dx: if job-index == 1 { 3pt } else { 0pt }, job.dates))')
        with self.assertRaisesRegex(ValueError, 'inconsistent date-right alignment'):
            verify_layout(pdf, self.profile, self.settings)


    def test_different_bullet_indentation_is_rejected(self):
        pdf = self.render('body-indent: 10pt',
                          'body-indent: if job-index == 2 { 14pt } else { 10pt }')
        with self.assertRaisesRegex(ValueError, 'inconsistent bullet-text alignment'):
            verify_layout(pdf, self.profile, self.settings)

    def test_different_contact_label_color_is_rejected(self):
        pdf = self.render('#text(weight: "bold")[Phone]',
                          '#text(weight: "bold", fill: red)[Phone]')
        with self.assertRaisesRegex(ValueError, 'inconsistent contact-label typography'):
            verify_layout(pdf, self.profile, self.settings)


if __name__ == '__main__':
    unittest.main()
