"""Run from backend: python -m unittest test_api.py"""
import base64
import io
import unittest
import json
from pathlib import Path
from zipfile import ZipFile

from fastapi.testclient import TestClient
from app.main import app, job_lock


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_invalid_and_empty(self):
        for data in (b"", b"not an image"):
            self.assertEqual(self.client.post('/reconstruct', content=data).status_code, 422)

    def test_byte_limit(self):
        self.assertEqual(self.client.post('/reconstruct', content=b'x' * (5 * 1024 * 1024 + 1)).status_code, 413)

    def test_busy(self):
        job_lock.acquire()
        try:
            self.assertEqual(self.client.post('/reconstruct', content=b'x').status_code, 429)
        finally:
            job_lock.release()

    def test_origins(self):
        for origin in ('http://localhost:5173', 'http://127.0.0.1:5173'):
            response = self.client.options('/reconstruct', headers={'Origin': origin, 'Access-Control-Request-Method': 'POST'})
            self.assertEqual(response.headers.get('access-control-allow-origin'), origin)
        response = self.client.get('/health', headers={'Origin': 'https://unknown.example'})
        self.assertNotIn('access-control-allow-origin', response.headers)

    def test_reconstruction_exports(self):
        fixture = Path(__file__).resolve().parents[1] / 'tests/fixtures/login.png'
        response = self.client.post('/reconstruct', content=fixture.read_bytes())
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(sum(e['type'] == 'input' for e in result['layout']['elements']), 2)
        for key, expected in [('html', 'index.html'), ('react', 'src/App.tsx'), ('tailwind', 'src/classes.ts')]:
            with ZipFile(io.BytesIO(base64.b64decode(result['exports'][key]))) as archive:
                self.assertIn(expected, archive.namelist())
        self.assertFalse(job_lock.locked())

    def test_edited_layout_updates_both_exports(self):
        fixture = Path(__file__).resolve().parents[1] / 'tests/fixtures/rounded-layout.json'
        layout = json.loads(fixture.read_text())
        button = next(e for e in layout['elements'] if e['type'] == 'button')
        button.update(text='<Start & go>', font_size=26, color='#112233', background='#aabbcc', radius=12, border_width=3, x=150)
        response = self.client.post('/render', json=layout)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn('&lt;Start &amp; go&gt;', result['html'])
        for value in ('font:26.0px', 'color:#112233', 'background:#aabbcc', 'border-radius:12.0px', 'left:150.0px'):
            self.assertIn(value, result['css'])
        for key in ('html', 'react'):
            with ZipFile(io.BytesIO(base64.b64decode(result['exports'][key]))) as archive:
                css = archive.read('styles.css' if key == 'html' else 'src/styles.css').decode()
                self.assertEqual(css, result['css'])
                if key == 'react':
                    data = json.loads(archive.read('src/layout.json'))
                    self.assertEqual(next(e['text'] for e in data['elements'] if e['type'] == 'button'), '<Start & go>')

    def test_layout_rejects_injection_and_invalid_sizes(self):
        fixture = Path(__file__).resolve().parents[1] / 'tests/fixtures/rounded-layout.json'
        for patch in ({'id': 'x\" onclick=alert(1)'}, {'background': 'red;position:fixed'}, {'width': -1}, {'src': 'javascript:alert(1)'}):
            layout = json.loads(fixture.read_text())
            layout['elements'][0].update(patch)
            self.assertEqual(self.client.post('/render', json=layout).status_code, 422)


if __name__ == '__main__':
    unittest.main()
