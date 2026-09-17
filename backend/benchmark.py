"""Run from the repository root: python backend/benchmark.py."""

import io
import json
import platform
import statistics
import threading
import time
from pathlib import Path

import psutil
from PIL import Image, ImageDraw

from app.baseline import inspect_image

OUT = Path(__file__).resolve().parents[1] / "reports" / "baseline"
OUT.mkdir(parents=True, exist_ok=True)
process = psutil.Process()
samples = []
stop = threading.Event()


def sample_memory():
    while not stop.is_set():
        samples.append(process.memory_info().rss / 1024**2)
        stop.wait(0.005)


def fixture(name, size, boxes):
    image = Image.new("RGB", size, "#f8fafc")
    draw = ImageDraw.Draw(image)
    for index, box in enumerate(boxes):
        draw.rectangle(box, fill="#dbeafe", outline="#2563eb", width=2)
        draw.text((box[0] + 10, box[1] + 10), f"Element {index + 1}", fill="#172554")
    image.save(OUT / f"{name}.png")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


fixtures = {
    "flat-login": fixture("flat-login", (900, 700), [(280, 190, 620, 240), (280, 270, 620, 320), (280, 360, 620, 415)]),
    "nested-login": fixture("nested-login", (900, 700), [(200, 100, 700, 600), (280, 190, 620, 240), (280, 270, 620, 320), (280, 360, 620, 415)]),
    "landing": fixture("landing", (1440, 900), [(30, 25, 1410, 95), (70, 180, 650, 480), (780, 180, 1360, 480), (70, 600, 440, 830), (535, 600, 905, 830), (1000, 600, 1370, 830)]),
    "large": fixture("large", (2000, 2000), [(50, 50, 1950, 300), (50, 500, 900, 1800), (1100, 500, 1950, 1800)]),
}
thread = threading.Thread(target=sample_memory, daemon=True)
thread.start()
results = {}
try:
    for name, payload in fixtures.items():
        before = process.memory_info().rss / 1024**2
        times = []
        for _ in range(21):
            start = time.perf_counter()
            result = inspect_image(payload)
            times.append((time.perf_counter() - start) * 1000)
        after = process.memory_info().rss / 1024**2
        results[name] = {"first_call_ms": round(times[0], 2), "warm_median_ms": round(statistics.median(times[1:]), 2), "warm_max_ms": round(max(times[1:]), 2), "regions_detected": len(result["regions"]), "rss_before_mib": round(before, 2), "rss_after_mib": round(after, 2)}
        preview = Image.open(io.BytesIO(payload)).convert("RGB")
        draw = ImageDraw.Draw(preview)
        for box in result["regions"]:
            x, y, w, h = (box[k] for k in ("x", "y", "width", "height"))
            draw.rectangle((x, y, x + w, y + h), outline="red", width=3)
        preview.save(OUT / f"{name}-detections.png")
    rejected = []
    for label, payload in [("empty", b""), ("invalid", b"not an image"), ("oversized-bytes", b"x" * (5 * 1024 * 1024 + 1))]:
        try:
            inspect_image(payload)
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError(f"Accepted {label}")
    image = Image.new("RGB", (2001, 2000))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    try:
        inspect_image(buffer.getvalue())
    except ValueError:
        rejected.append("oversized-dimensions")
    else:
        raise AssertionError("Accepted oversized dimensions")
finally:
    stop.set()
    thread.join()
report = {"platform": platform.platform(), "python": platform.python_version(), "scope": "Local synthetic geometry baseline only; no OCR, trained model, hosted test, or reconstruction quality claim.", "iterations_per_fixture": 21, "sampled_peak_rss_mib": round(max(samples), 2), "memory_sampling_interval_ms": 5, "results": results, "validation_rejections_passed": rejected}
(OUT / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
