"""Public aggregate diagnostics. No request bodies, images, logs, or secrets."""
import importlib.metadata
import threading
import time

started = time.monotonic()
lock = threading.Lock()
counts = {'requests': 0, 'failed': 0, 'total_seconds': 0.0, 'last_seconds': None}

def record(status, duration):
    with lock:
        counts['requests'] += 1
        counts['failed'] += int(status >= 400)
        counts['total_seconds'] += duration
        counts['last_seconds'] = round(duration, 3)

def snapshot(busy):
    with lock:
        data = dict(counts)
    try:
        import psutil
        memory = round(psutil.Process().memory_info().rss / 1024**2, 1)
    except (ImportError, OSError):
        memory = None
    try:
        ocr = importlib.metadata.version('rapidocr-onnxruntime')
    except importlib.metadata.PackageNotFoundError:
        ocr = None
    return {
        'status': 'ok', 'uptime_seconds': int(time.monotonic() - started),
        'reconstruction_busy': busy, 'memory_mib': memory,
        'ocr_version': ocr, 'ocr_status': 'Installed' if ocr else 'Unavailable',
        'requests': data['requests'], 'failed_requests': data['failed'],
        'average_seconds': round(data['total_seconds']/data['requests'], 3) if data['requests'] else None,
        'last_seconds': data['last_seconds'],
        'scope': 'Reconstruction, text extraction and render requests since this process started. Resets on restart.',
    }
