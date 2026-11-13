"""Exercise a standalone profile from a caller outside the generator checkout."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ExternalProfileTests(unittest.TestCase):
    def test_external_build_matches_example_and_supports_output_override(self):
        with tempfile.TemporaryDirectory(prefix='external profile ') as temp:
            caller = Path(temp)
            shutil.copytree(ROOT / 'profiles/example', caller / 'profile')
            subprocess.run(['bash', str(ROOT / 'build.sh'), '--profile', 'profile',
                            '--output-dir', 'custom output'], cwd=caller, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual((caller / 'custom output/cv.pdf').read_bytes(),
                             (ROOT / 'profiles/example/output/cv.pdf').read_bytes())
            subprocess.run([sys.executable, str(ROOT / 'verify.py'), '--profile', 'profile',
                            '--output-dir', 'custom output'], cwd=caller, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_external_scaffold_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            args = [sys.executable, str(ROOT / 'new_profile.py'), 'example',
                    '--name', 'Alex Example', '--title', 'Engineer', '--directory', 'profile']
            subprocess.run(args, cwd=temp, check=True, stdout=subprocess.PIPE)
            profile = Path(temp) / 'profile/profile.json'
            original = profile.read_bytes()
            self.assertEqual(json.loads(original)['name'], 'Alex Example')
            result = subprocess.run(args, cwd=temp, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(profile.read_bytes(), original)
