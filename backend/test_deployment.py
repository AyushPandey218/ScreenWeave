"""Check imports/exports using only the files copied into the deployment image."""
import json
import shlex
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

class DeploymentPackageTests(unittest.TestCase):
    def test_docker_file_set_supports_all_exports(self):
        backend = Path(__file__).resolve().parent
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            for line in (backend / 'Dockerfile').read_text().splitlines():
                if not line.startswith('COPY '):
                    continue
                parts = shlex.split(line)
                destination = root / parts[-1]
                destination.mkdir(parents=True, exist_ok=True)
                for name in parts[1:-1]:
                    source = backend / name
                    if source.is_dir():
                        shutil.copytree(source, destination, dirs_exist_ok=True,
                                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                    else:
                        shutil.copy2(source, destination / source.name)
            code = """import sys, os, json
sys.path.insert(0, os.getcwd())
from app.main import package_layout
layout = {'version': 1, 'viewport': {'width': 1, 'height': 1}, 'background': '#ffffff', 'elements': [], 'limitations': []}
print(json.dumps(sorted(package_layout(layout)['exports'])))
"""
            result = subprocess.run([sys.executable, '-I', '-c', code], cwd=root,
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), ['html', 'react', 'tailwind'])
