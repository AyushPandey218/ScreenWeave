"""Measure an isolated real HTTP server; this is not a Render hardware test."""
import io
import json
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

import psutil
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
(ROOT / 'reports').mkdir(exist_ok=True)
samples = []
stop = threading.Event()
log = (ROOT / 'reports/service-benchmark.log').open('w')
server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8011'], cwd=ROOT / 'backend', stdout=log, stderr=log)
process = psutil.Process(server.pid)

def rss_mib():
    # Windows virtualenv launchers can spawn the actual Python server as a child.
    return sum(p.memory_info().rss for p in [process, *process.children(recursive=True)] if p.is_running()) / 1024**2

def sample():
    while not stop.is_set():
        try:
            samples.append(rss_mib())
        except psutil.NoSuchProcess:
            break
        stop.wait(.01)

def request(path, payload=None):
    req = urllib.request.Request('http://127.0.0.1:8011' + path, data=payload, headers={'Content-Type': 'application/json' if path == '/render' else 'image/png'})
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.load(response)

thread = threading.Thread(target=sample, daemon=True)
thread.start()
try:
    for _ in range(100):
        try:
            request('/health')
            break
        except OSError:
            if server.poll() is not None:
                raise RuntimeError('Server exited; inspect reports/service-benchmark.log')
            time.sleep(.1)
    else:
        raise RuntimeError('Server startup timed out')
    fixtures = [(name, (ROOT / path).read_bytes()) for name, path in [('login', 'tests/fixtures/login.png'), ('rounded', 'tests/fixtures/rounded-controls.png')]]
    with Image.open(ROOT / 'tests/fixtures/rounded-controls.png') as source:
        image = source.resize((2000, 2000))
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        fixtures.append(('4-megapixel-resized-fixture', buffer.getvalue()))
    rows = []
    for name, payload in fixtures:
        for iteration in range(3):
            start = time.perf_counter()
            result = request('/reconstruct', payload)
            rows.append({'fixture': name, 'iteration': iteration + 1, 'seconds': round(time.perf_counter()-start, 3), 'rss_after_mib': round(rss_mib(), 2), 'elements': len(result['layout']['elements'])})
    start = time.perf_counter()
    request('/render', json.dumps(result['layout']).encode())
    report = {'scope': 'Isolated Windows HTTP server including OCR, geometry, and both ZIP exports. Not Linux/Render; 10ms memory sampling can miss brief peaks.', 'sampled_peak_rss_mib': round(max(samples), 2), 'render_seconds': round(time.perf_counter()-start, 3), 'requests': rows}
    (ROOT / 'reports/service-benchmark.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
finally:
    stop.set()
    thread.join()
    for child in process.children(recursive=True):
        child.terminate()
    server.terminate()
    try:
        server.wait(timeout=10)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait()
    log.close()
