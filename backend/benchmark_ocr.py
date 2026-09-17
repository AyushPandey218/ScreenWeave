"""CPU OCR feasibility experiment. Synthetic inputs are not a real-world test set."""
import argparse
import importlib.metadata
import json
import platform
import statistics
import threading
import time
from pathlib import Path

import psutil
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "reports" / "ocr"


def distance(a, b):
    row = list(range(len(b) + 1))
    for i, left in enumerate(a, 1):
        new = [i]
        for j, right in enumerate(b, 1):
            new.append(min(new[-1] + 1, row[j] + 1, row[j - 1] + (left != right)))
        row = new
    return row[-1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--font", default="C:/Windows/Fonts/arial.ttf")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    process = psutil.Process()
    samples = []
    stop = threading.Event()

    def monitor():
        while not stop.is_set():
            samples.append(process.memory_info().rss / 1024**2)
            stop.wait(0.005)

    worker = threading.Thread(target=monitor, daemon=True)
    worker.start()
    try:
        start = time.perf_counter()
        from rapidocr_onnxruntime import RapidOCR
        engine = RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)
        initialization_ms = (time.perf_counter() - start) * 1000
        fixtures = [
            ("login", (900, 700), "#f8fafc", [("Welcome back", 290, 140, 32, "#172554"), ("Email address", 290, 240, 18, "#334155"), ("Password", 290, 330, 18, "#334155"), ("Sign in", 390, 430, 20, "#ffffff")]),
            ("landing", (1440, 900), "#ffffff", [("ScreenWeave", 60, 35, 26, "#172554"), ("Build from a screenshot", 80, 230, 48, "#172554"), ("Turn your interface into editable code.", 80, 330, 24, "#475569"), ("Get started", 100, 430, 22, "#172554"), ("Export HTML and React", 80, 610, 28, "#172554")]),
            ("small-low-contrast", (900, 700), "#ffffff", [("Terms and conditions", 60, 100, 12, "#999999"), ("Forgot your password?", 60, 200, 14, "#777777"), ("support@example.com", 60, 300, 16, "#475569")]),
            ("blank", (900, 700), "#ffffff", []),
        ]
        report = {}
        for name, size, background, lines in fixtures:
            image = Image.new("RGB", size, background)
            draw = ImageDraw.Draw(image)
            if name == "login":
                draw.rounded_rectangle((250, 100, 650, 530), radius=16, fill="white", outline="#cbd5e1")
                draw.rectangle((280, 275, 620, 310), outline="#64748b")
                draw.rectangle((280, 365, 620, 400), outline="#64748b")
                draw.rounded_rectangle((280, 420, 620, 465), radius=6, fill="#2563eb")
            truth = []
            for text, x, y, font_size, color in lines:
                font = ImageFont.truetype(args.font, font_size)
                draw.text((x, y), text, font=font, fill=color)
                truth.append({"text": text, "box": list(draw.textbbox((x, y), text, font=font))})
            path = OUT / f"{name}.png"
            image.save(path)
            times = []
            memory = []
            for _ in range(6):
                start = time.perf_counter()
                result, _ = engine(str(path), use_cls=False)
                times.append((time.perf_counter() - start) * 1000)
                memory.append(round(process.memory_info().rss / 1024**2, 2))
            found = []
            for box, text, confidence in result or []:
                points = [[float(x), float(y)] for x, y in box]
                found.append({"text": text, "confidence": float(confidence), "polygon": points})
                draw.line([tuple(point) for point in points] + [tuple(points[0])], fill="red", width=2)
            image.save(OUT / f"{name}-detections.png")
            expected = " ".join(item["text"] for item in truth)
            actual = " ".join(item["text"] for item in found)
            report[name] = {
                "expected": truth, "recognized": found,
                "character_error_rate_reading_order": distance(expected, actual) / len(expected) if expected else None,
                "exact_line_matches": sum(item["text"] in [r["text"] for r in found] for item in truth),
                "first_call_ms": round(times[0], 2),
                "warm_median_ms": round(statistics.median(times[1:]), 2),
                "rss_after_each_call_mib": memory,
            }
        result = {"scope": "Local CPU-only synthetic OCR benchmark; no Render or real screenshot validation.", "platform": platform.platform(), "python": platform.python_version(), "engine_version": importlib.metadata.version("rapidocr-onnxruntime"), "onnxruntime_version": importlib.metadata.version("onnxruntime"), "threads": 2, "orientation_classification": False, "font": args.font, "initialization_ms": round(initialization_ms, 2), "sampled_peak_rss_mib": round(max(samples), 2), "sample_interval_ms": 5, "fixtures": report}
        (OUT / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps({key: value for key, value in result.items() if key != "fixtures"}, indent=2))
        for name, metrics in report.items():
            print(name, json.dumps({key: value for key, value in metrics.items() if key not in ("expected", "recognized")}))
    finally:
        stop.set()
        worker.join()


if __name__ == "__main__":
    main()
